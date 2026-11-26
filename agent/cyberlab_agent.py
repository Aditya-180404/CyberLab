#!/usr/bin/env python3
"""
CyberLab Autonomous Distributed Linux Security Agent
Lightweight endpoint detection and response (EDR) agent for managed Linux systems.
Supports:
- Enrollment key authentication & custom TLS CA verification
- Process, network socket, and installed package inventory (dpkg/rpm)
- SHA-256 File Integrity Monitoring (FIM) with offline delta buffering
- Auth log tailing (/var/log/auth.log, /var/log/secure)
- Real nftables endpoint isolation (when running with CAP_NET_ADMIN / root)
"""
import os
import re
import ssl
import sys
import json
import time
import socket
import hashlib
import platform
import argparse
import subprocess
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

VERSION = "1.0.0"

_AUTH_FAIL_RE = re.compile(r"(?:Failed password|Invalid user|authentication failure).*?from\s+((?:\d{1,3}\.){3}\d{1,3})", re.IGNORECASE)
_SUDO_RE = re.compile(r"sudo:.*?(?:NOT in sudoers|authentication failure|COMMAND=.*)", re.IGNORECASE)


class CyberLabAgent:
    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8000",
        config_path: str = "./cyberlab_agent_config.json",
        enrollment_key: Optional[str] = None,
        ca_cert: Optional[str] = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.config_path = config_path
        self.enrollment_key = enrollment_key or os.getenv("CYBERLAB_ENROLLMENT_KEY")
        self.ca_cert = ca_cert or os.getenv("CYBERLAB_CA_CERT")
        self.ssl_context = ssl.create_default_context(cafile=self.ca_cert) if self.ca_cert else None

        self.agent_id: Optional[str] = None
        self.agent_token: Optional[str] = None
        self.policy: Dict[str, Any] = {
            "telemetry_interval_sec": 15,
            "fim_monitored_paths": ["/etc/passwd", "/etc/hosts", "/etc/cyberlab_canary.key"],
        }
        self.fim_baselines: Dict[str, str] = {}
        self.pending_fim_alerts: List[Dict[str, Any]] = []
        self.auth_log_offsets: Dict[str, int] = {}
        self.is_isolated = False
        self._cached_packages: List[Dict[str, str]] = []
        self._last_pkg_scan: float = 0.0
        self.load_local_config()

    def load_local_config(self) -> None:
        """Loads cached agent identity, policy, and offsets from disk."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.agent_id = data.get("agent_id")
                    self.agent_token = data.get("agent_token")
                    self.policy = data.get("policy", self.policy)
                    self.fim_baselines = data.get("fim_baselines", {})
                    self.auth_log_offsets = data.get("auth_log_offsets", {})
                    self.is_isolated = data.get("is_isolated", False)
            except Exception as e:
                print(f"[!] Warning: Could not read local config: {e}")

    def save_local_config(self) -> None:
        """Persists agent identity and FIM baselines for offline survivability."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "agent_id": self.agent_id,
                    "agent_token": self.agent_token,
                    "policy": self.policy,
                    "fim_baselines": self.fim_baselines,
                    "auth_log_offsets": self.auth_log_offsets,
                    "is_isolated": self.is_isolated,
                }, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Could not save local config: {e}")

    def _http_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Performs outbound HTTP/HTTPS request with authentication and optional enrollment headers."""
        url = f"{self.server_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.agent_token and self.agent_id:
            headers["Authorization"] = f"Bearer {self.agent_token}"
            headers["X-CyberLab-Agent-ID"] = self.agent_id
        if self.enrollment_key and endpoint == "/api/v1/agents/register":
            headers["X-CyberLab-Enrollment-Key"] = self.enrollment_key

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers)

        with urllib.request.urlopen(req, timeout=10, context=self.ssl_context) as resp:
            return json.loads(resp.read().decode())

    def register(self) -> bool:
        """Onboards the agent with the central CyberLab server."""
        if self.agent_id and self.agent_token:
            return True

        print(f"[*] Registering new agent with {self.server_url}...")
        hostname = socket.gethostname()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_addr = s.getsockname()[0]
            s.close()
        except Exception:
            ip_addr = "127.0.0.1"

        payload = {
            "hostname": hostname,
            "ip_address": ip_addr,
            "os_type": platform.system(),
            "os_release": platform.platform(),
            "kernel_version": platform.release(),
            "agent_version": VERSION,
            "hardware_specs": {
                "cpu_cores": os.cpu_count() or 1,
                "architecture": platform.machine(),
            },
        }

        try:
            res = self._http_request("/api/v1/agents/register", payload)
            self.agent_id = res["agent_id"]
            self.agent_token = res["agent_token"]
            self.policy = res.get("policy", self.policy)
            self.save_local_config()
            print(f"[+] Successfully registered! Agent ID: {self.agent_id}")
            self.compute_fim_baselines()
            return True
        except Exception as e:
            print(f"[-] Registration failed: {e}")
            return False

    def compute_fim_baselines(self) -> None:
        """Generates initial SHA-256 baseline hashes for monitored system files."""
        paths = self.policy.get("fim_monitored_paths", ["/etc/passwd", "/etc/hosts"])
        for p in paths:
            if os.path.isfile(p):
                try:
                    with open(p, "rb") as f:
                        self.fim_baselines[p] = hashlib.sha256(f.read()).hexdigest()
                except Exception as e:
                    print(f"[!] FIM access error on {p}: {e}")
        self.save_local_config()

    def check_fim_deltas(self) -> List[Dict[str, Any]]:
        """Compares current file hashes against stored cryptographic baselines."""
        alerts = []
        paths = self.policy.get("fim_monitored_paths", ["/etc/passwd", "/etc/hosts"])
        for p in paths:
            if os.path.isfile(p):
                try:
                    with open(p, "rb") as f:
                        current_hash = hashlib.sha256(f.read()).hexdigest()
                    old_hash = self.fim_baselines.get(p)
                    if old_hash and current_hash != old_hash:
                        alerts.append({
                            "event_type": "FIM_MODIFIED",
                            "action": "MODIFIED",
                            "path": p,
                            "file_path": p,
                            "old_hash": old_hash,
                            "new_hash": current_hash,
                            "severity": "CRITICAL" if "canary" in p or p in ("/etc/shadow", "/etc/sudoers") else "HIGH",
                            "message": f"SHA-256 hash changed on {p}",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        })
                        self.fim_baselines[p] = current_hash
                    elif not old_hash:
                        self.fim_baselines[p] = current_hash
                except Exception:
                    pass
        if alerts:
            self.pending_fim_alerts.extend(alerts)
            self.save_local_config()
        return alerts

    def collect_auth_events(self) -> List[Dict[str, Any]]:
        """Tails readable Linux auth logs for SSH failures and sudo/privilege events."""
        events: List[Dict[str, Any]] = []
        for log_path in ("/var/log/auth.log", "/var/log/secure"):
            if not os.path.isfile(log_path):
                continue
            try:
                file_size = os.path.getsize(log_path)
                offset = self.auth_log_offsets.get(log_path)
                if offset is None or offset > file_size:
                    # Start tailing from current EOF on first run or log rotation
                    self.auth_log_offsets[log_path] = file_size
                    continue
                if offset == file_size:
                    continue

                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(offset)
                    new_lines = f.readlines()[-100:]
                    self.auth_log_offsets[log_path] = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    m_ssh = _AUTH_FAIL_RE.search(line)
                    if m_ssh:
                        events.append({
                            "category": "AUTHENTICATION",
                            "action": "FAILURE",
                            "severity": "MEDIUM",
                            "source_ip": m_ssh.group(1),
                            "message": line,
                            "mitre_tactic": "Credential Access",
                            "mitre_technique_id": "T1110",
                        })
                    elif _SUDO_RE.search(line):
                        is_fail = "not in sudoers" in line.lower() or "failure" in line.lower()
                        events.append({
                            "category": "AUTHENTICATION",
                            "action": "FAILURE" if is_fail else "EXECUTED",
                            "severity": "HIGH" if is_fail else "LOW",
                            "message": line,
                            "mitre_tactic": "Privilege Escalation",
                            "mitre_technique_id": "T1548.003",
                        })
            except PermissionError:
                pass
            except Exception:
                pass
        if events:
            self.save_local_config()
        return events[:50]

    def collect_packages(self) -> List[Dict[str, str]]:
        """Collects installed software package names and versions for CVE matching (cached 5m)."""
        now = time.time()
        if self._cached_packages and (now - self._last_pkg_scan) < 300:
            return self._cached_packages

        pkgs: List[Dict[str, str]] = []
        try:
            res = subprocess.run(
                ["dpkg-query", "-W", "-f=${Package}\t${Version}\n"],
                capture_output=True, text=True, timeout=5
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    if "\t" in line:
                        name, ver = line.split("\t", 1)
                        pkgs.append({"package": name.strip(), "version": ver.strip()})
        except Exception:
            try:
                res = subprocess.run(
                    ["rpm", "-qa", "--qf", "%{NAME}\t%{VERSION}-%{RELEASE}\n"],
                    capture_output=True, text=True, timeout=5
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if "\t" in line:
                            name, ver = line.split("\t", 1)
                            pkgs.append({"package": name.strip(), "version": ver.strip()})
            except Exception:
                pass

        # Prioritize security/network services if large package set
        priority = ("openssl", "openssh", "apache2", "nginx", "vsftpd", "samba", "sudo", "bash", "curl", "python3", "postgresql")
        prioritized = [p for p in pkgs if any(k in p["package"].lower() for k in priority)]
        others = [p for p in pkgs if p not in prioritized]
        self._cached_packages = (prioritized + others)[:120]
        self._last_pkg_scan = now
        return self._cached_packages

    def collect_processes(self) -> List[Dict[str, Any]]:
        """Collects process snapshot."""
        procs = []
        if HAS_PSUTIL:
            for p in psutil.process_iter(["pid", "ppid", "name", "username"]):
                try:
                    procs.append({
                        "pid": p.info["pid"],
                        "ppid": p.info["ppid"],
                        "name": p.info["name"],
                        "username": p.info["username"],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            procs.append({"pid": os.getpid(), "ppid": os.getppid(), "name": "cyberlab-agent", "username": "current"})
        return procs[:50]

    def collect_sockets(self) -> List[Dict[str, Any]]:
        """Collects listening and active network sockets."""
        sockets = []
        if HAS_PSUTIL:
            try:
                for c in psutil.net_connections(kind="inet"):
                    laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else ""
                    raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else ""
                    sockets.append({
                        "protocol": "TCP" if c.type == socket.SOCK_STREAM else "UDP",
                        "local_port": c.laddr.port if c.laddr else 0,
                        "local": laddr,
                        "remote": raddr,
                        "state": c.status or "LISTEN",
                    })
            except Exception:
                pass
        return sockets[:30]

    def apply_isolation(self) -> None:
        """Applies local nftables isolation restricting non-CyberLab traffic when privileged."""
        print("[!] ISOLATION ORDER RECEIVED. Applying host containment policy...")
        try:
            from urllib.parse import urlparse
            host = urlparse(self.server_url).hostname or "127.0.0.1"
            subprocess.run(["nft", "add", "table", "inet", "cyberlab_isolation"], check=True, capture_output=True)
            subprocess.run([
                "nft", "add", "chain", "inet", "cyberlab_isolation", "output",
                "{ type filter hook output priority 0; policy drop; }"
            ], check=True, capture_output=True)
            subprocess.run(["nft", "add", "rule", "inet", "cyberlab_isolation", "output", "oif", "lo", "accept"], check=True, capture_output=True)
            subprocess.run(["nft", "add", "rule", "inet", "cyberlab_isolation", "output", "ip", "daddr", host, "accept"], check=True, capture_output=True)
            print("[+] Kernel nftables isolation chain active (server management link preserved).")
        except Exception as e:
            print(f"[!] Logical isolation state set (kernel nftables requires root/CAP_NET_ADMIN: {e})")
        self.is_isolated = True
        self.save_local_config()

    def remove_isolation(self) -> None:
        """Removes nftables isolation table and restores normal network traffic."""
        print("[*] RESTORATION ORDER RECEIVED. Restoring network traffic...")
        try:
            subprocess.run(["nft", "delete", "table", "inet", "cyberlab_isolation"], check=True, capture_output=True)
            print("[+] Kernel nftables isolation table removed.")
        except Exception:
            pass
        self.is_isolated = False
        self.save_local_config()

    def send_heartbeat(self) -> None:
        """Sends lightweight heartbeat and checks for server commands."""
        cpu = psutil.cpu_percent() if HAS_PSUTIL else 0.0
        mem = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
        disk = psutil.disk_usage("/").percent if HAS_PSUTIL else 0.0

        try:
            res = self._http_request("/api/v1/agents/heartbeat", {
                "cpu_pct": cpu,
                "memory_pct": mem,
                "disk_pct": disk,
            })

            commands = res.get("pending_commands", [])
            for cmd in commands:
                if cmd == "ISOLATE":
                    self.apply_isolation()
                elif cmd == "RESTORE":
                    self.remove_isolation()
        except urllib.error.HTTPError as e:
            if e.code == 403:
                print("[-] Agent credentials revoked by administrator. Stopping agent.")
                sys.exit(1)
        except Exception as e:
            print(f"[!] Heartbeat error: {e}")

    def send_telemetry(self) -> None:
        """Collects and batches security telemetry to server."""
        cpu = psutil.cpu_percent() if HAS_PSUTIL else 0.0
        mem = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
        disk = psutil.disk_usage("/").percent if HAS_PSUTIL else 0.0

        self.check_fim_deltas()
        dispatched_fim = list(self.pending_fim_alerts)
        self.pending_fim_alerts.clear()

        auth_evts = self.collect_auth_events() if self.policy.get("monitor_auth_logs", True) else []
        pkgs = self.collect_packages()

        batch = {
            "cpu_pct": cpu,
            "memory_pct": mem,
            "disk_pct": disk,
            "processes": self.collect_processes(),
            "network_connections": self.collect_sockets(),
            "fim_alerts": dispatched_fim,
            "auth_events": auth_evts,
            "installed_packages": pkgs,
        }

        try:
            self._http_request("/api/v1/agents/telemetry", batch)
            print(
                f"[*] Telemetry synced: {len(batch['processes'])} procs, "
                f"{len(batch['network_connections'])} sockets, "
                f"{len(auth_evts)} auth, {len(pkgs)} pkgs, {len(dispatched_fim)} FIM alerts."
            )
        except Exception as e:
            # Re-queue FIM alerts for offline survivability
            if dispatched_fim:
                self.pending_fim_alerts.extend(dispatched_fim)
                self.save_local_config()
            print(f"[-] Telemetry transmission failed: {e}")

    def run_daemon(self, interval: int = 10) -> None:
        """Runs continuous monitoring loop."""
        if not self.register():
            return

        print("[+] CyberLab Agent daemon started. Monitoring host...")
        cycle = 0
        try:
            while True:
                self.send_heartbeat()
                cycle += 1
                if cycle % 2 == 0:
                    self.send_telemetry()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[*] Agent stopped by operator.")


def main():
    parser = argparse.ArgumentParser(description="CyberLab Distributed Linux Agent")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="CyberLab Central Server URL")
    parser.add_argument("--config", default="./cyberlab_agent_config.json", help="Path to local config file")
    parser.add_argument("--enrollment-key", default=None, help="Pre-shared agent enrollment key")
    parser.add_argument("--ca-cert", default=None, help="Path to TLS CA certificate bundle")
    parser.add_argument("--run-once", action="store_true", help="Register, execute single telemetry batch, and exit")
    parser.add_argument("--interval", type=int, default=10, help="Heartbeat loop interval in seconds")

    args = parser.parse_args()

    agent = CyberLabAgent(
        server_url=args.server,
        config_path=args.config,
        enrollment_key=args.enrollment_key,
        ca_cert=args.ca_cert,
    )
    if args.run_once:
        if agent.register():
            agent.send_heartbeat()
            agent.send_telemetry()
    else:
        agent.run_daemon(interval=args.interval)


if __name__ == "__main__":
    main()
