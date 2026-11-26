#!/usr/bin/env bash
set -euo pipefail

# CyberLab Company Endpoint Agent Installer (systemd service)
# Usage: sudo ./install-agent.sh --server https://SOC_IP --enrollment-key KEY [--ca-cert /path/to/cyberlab.crt]

SERVER_URL=""
ENROLLMENT_KEY=""
CA_CERT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER_URL="$2"; shift 2 ;;
    --enrollment-key) ENROLLMENT_KEY="$2"; shift 2 ;;
    --ca-cert) CA_CERT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

if [[ -z "$SERVER_URL" ]]; then
  echo "Usage: sudo $0 --server https://SOC_SERVER_IP [--enrollment-key KEY] [--ca-cert /path/to/cert.crt]"
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "[!] Please run as root (sudo) to install systemd service."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
AGENT_SRC="${REPO_ROOT}/agent/cyberlab_agent.py"

if [[ ! -f "$AGENT_SRC" ]]; then
  echo "[!] Could not find cyberlab_agent.py at $AGENT_SRC"
  exit 1
fi

mkdir -p /opt/cyberlab-agent /etc/cyberlab-agent
cp "$AGENT_SRC" /opt/cyberlab-agent/cyberlab_agent.py
chmod 750 /opt/cyberlab-agent/cyberlab_agent.py

EXTRA_ARGS=""
if [[ -n "$ENROLLMENT_KEY" ]]; then
  EXTRA_ARGS="$EXTRA_ARGS --enrollment-key ${ENROLLMENT_KEY}"
fi
if [[ -n "$CA_CERT" && -f "$CA_CERT" ]]; then
  cp "$CA_CERT" /etc/cyberlab-agent/ca.crt
  chmod 644 /etc/cyberlab-agent/ca.crt
  EXTRA_ARGS="$EXTRA_ARGS --ca-cert /etc/cyberlab-agent/ca.crt"
fi

cat << EOF > /etc/systemd/system/cyberlab-agent.service
[Unit]
Description=CyberLab Autonomous Distributed EDR Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/etc/cyberlab-agent
ExecStart=/usr/bin/python3 /opt/cyberlab-agent/cyberlab_agent.py --server ${SERVER_URL} --config /etc/cyberlab-agent/config.json --interval 10 ${EXTRA_ARGS}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now cyberlab-agent.service

echo "[+] CyberLab Agent installed and running as systemd service!"
systemctl status cyberlab-agent.service --no-pager -n 5
