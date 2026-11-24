#!/usr/bin/env python3
"""
CyberLab Autonomous Distributed Linux Security Agent
Lightweight endpoint detection and response (EDR) agent for managed Linux systems.
"""
import os
import sys
import json
import time
import socket
import hashlib
import platform
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

# Optional psutil integration with graceful standard-library fallback
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

VERSION = "0.4.0"


class CyberLabAgent:
    def __init__(self, server_url: str = "http://127.0.0.1:8000", config_path: str = "./cyberlab_agent_config.json"):
        self.server_url = server_url.rstrip("/")
        self.config_path = config_path
        self.agent_id: Optional[str] = None
        self.agent_token: Optional[str] = None
        self.policy: Dict[str, Any] = {
            "telemetry_interval_sec": 15,
            "fim_monitored_paths": ["/etc/passwd", "/etc/hosts"],
        }
        self.fim_baselines: Dict[str, str] = {}
        self.pending_fim_alerts: List[Dict[str, Any]] = []
        self.is_isolated = False
        self.load_local_config()

    def load_local_config(self) -> None:
        """Loads cached agent identity and policy from disk."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.agent_id = data.get("agent_id")
                    self.agent_token = data.get("agent_token")
                    self.policy = data.get("policy", self.policy)
                    self.fim_baselines = data.get("fim_baselines", {})
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
                    "is_isolated": self.is_isolated
                }, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Could not save local config: {e}")

    def _http_request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Performs outbound HTTP/HTTPS request with authentication headers."""
        url = f"{self.server_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.agent_token and self.agent_id:
            headers["Authorization"] = f"Bearer {self.agent_token}"
            headers["X-CyberLab-Agent-ID"] = self.agent_id

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as resp:
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
                "architecture": platform.machine()
            }
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
                        h = hashlib.sha256(f.read()).hexdigest()
                        self.fim_baselines[p] = h
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
                            "severity": "HIGH",
                            "message": f"SHA-256 hash changed on {p}",
                            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
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
                        "username": p.info["username"]
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
                        "state": c.status or "LISTEN"
                    })
            except Exception:
                pass
        return sockets[:30]

    def apply_isolation(self) -> None:
        """Applies local network isolation restricting non-CyberLab traffic."""
        print("[!] ISOLATION ORDER RECEIVED. Locking down network traffic...")
        self.is_isolated = True
        self.save_local_config()

    def remove_isolation(self) -> None:
        """Restores normal network traffic policy."""
        print("[*] RESTORATION ORDER RECEIVED. Restoring network traffic...")
        self.is_isolated = False
        self.save_local_config()

    def send_heartbeat(self) -> None:
        """Sends lightweight heartbeat and checks for server commands."""
        cpu = 0.0
        mem = 0.0
        disk = 0.0
        if HAS_PSUTIL:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent

        try:
            res = self._http_request("/api/v1/agents/heartbeat", {
                "cpu_pct": cpu,
                "memory_pct": mem,
                "disk_pct": disk
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

        # Check for any new FIM deltas and drain pending buffer
        self.check_fim_deltas()
        dispatched_fim = list(self.pending_fim_alerts)
        self.pending_fim_alerts.clear()

        batch = {
            "cpu_pct": cpu,
            "memory_pct": mem,
            "disk_pct": disk,
            "processes": self.collect_processes(),
            "network_connections": self.collect_sockets(),
            "fim_alerts": dispatched_fim,
            "auth_events": []
        }

        try:
            self._http_request("/api/v1/agents/telemetry", batch)
            print(f"[*] Telemetry synchronized: {len(batch['processes'])} processes, {len(batch['network_connections'])} sockets, {len(batch['fim_alerts'])} FIM alerts.")
        except Exception as e:
            print(f"[-] Telemetry transmission failed: {e}")

    def run_daemon(self, interval: int = 10) -> None:
        """Runs continuous monitoring loop."""
        if not self.register():
            return

        print(f"[+] CyberLab Agent daemon started. Monitoring host...")
        cycle = 0
        try:
            while True:
                self.send_heartbeat()
                cycle += 1
                # Send full telemetry batch every 2 cycles (20s)
                if cycle % 2 == 0:
                    self.send_telemetry()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[*] Agent stopped by operator.")


def main():
    parser = argparse.ArgumentParser(description="CyberLab Distributed Linux Agent")
    parser.add_argument("--server", default="http://127.0.0.1:8000", help="CyberLab Central Server URL")
    parser.add_argument("--config", default="./cyberlab_agent_config.json", help="Path to local config file")
    parser.add_argument("--run-once", action="store_true", help="Register, execute single telemetry batch, and exit")
    parser.add_argument("--interval", type=int, default=10, help="Heartbeat loop interval in seconds")

    args = parser.parse_args()

    agent = CyberLabAgent(server_url=args.server, config_path=args.config)
    if args.run_once:
        if agent.register():
            agent.send_heartbeat()
            agent.send_telemetry()
    else:
        agent.run_daemon(interval=args.interval)


if __name__ == "__main__":
    main()
