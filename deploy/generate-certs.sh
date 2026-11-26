#!/usr/bin/env bash
set -euo pipefail

CERT_DIR="$(cd "$(dirname "$0")" && pwd)/nginx/certs"
mkdir -p "$CERT_DIR"

HOST_IP="${1:-127.0.0.1}"

if [[ -f "$CERT_DIR/cyberlab.crt" && -f "$CERT_DIR/cyberlab.key" ]]; then
  echo "[*] TLS certificates already exist in $CERT_DIR"
  exit 0
fi

echo "[*] Generating self-signed TLS certificate for $HOST_IP..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/cyberlab.key" \
  -out "$CERT_DIR/cyberlab.crt" \
  -subj "/C=US/ST=SOC/L=Enterprise/O=CyberLab/CN=${HOST_IP}" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:${HOST_IP}"

chmod 600 "$CERT_DIR/cyberlab.key"
echo "[+] TLS certificates generated in $CERT_DIR"
