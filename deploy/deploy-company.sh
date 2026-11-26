#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=========================================="
echo " CyberLab Enterprise Stack Deployment"
echo "=========================================="

# 1. Generate .env with secure random secrets if missing
if [[ ! -f .env ]]; then
  SECRET_VAL=$(openssl rand -hex 32)
  DB_PASS=$(openssl rand -hex 16)
  ENROLL_KEY=$(openssl rand -hex 16)
  cat << EOF > .env
ENVIRONMENT=production
SECRET_KEY=${SECRET_VAL}
AGENT_ENROLLMENT_KEY=${ENROLL_KEY}
POSTGRES_USER=cyberlab
POSTGRES_PASSWORD=${DB_PASS}
POSTGRES_DB=cyberlab_db
SYSLOG_ENABLED=true
SYSLOG_PORT=5514
NETWORK_ENGINE_DRIVER=simulation
NEXT_PUBLIC_API_URL=/api/backend
EOF
  chmod 600 .env
  echo "[+] Generated production .env with random SECRET_KEY, DB password, and AGENT_ENROLLMENT_KEY."
else
  echo "[*] Using existing .env configuration."
fi

# 2. Generate internal TLS certs if missing
HOST_IP=$(hostname -I | awk '{print $1}')
HOST_IP="${HOST_IP:-127.0.0.1}"
bash ./deploy/generate-certs.sh "$HOST_IP"

# 3. Start full TLS stack (PostgreSQL + Backend + Frontend + Nginx HTTPS)
echo "[*] Building and starting CyberLab enterprise stack..."
docker compose --profile tls up -d --build

source .env
echo ""
echo "=========================================="
echo " CyberLab Deployment Complete"
echo "=========================================="
echo " Web SOC Console (HTTPS):  https://${HOST_IP}"
echo " Syslog/NDR Collector:     ${HOST_IP}:5514 (UDP/TCP)"
echo " Agent Enrollment Key:     ${AGENT_ENROLLMENT_KEY}"
echo ""
echo " Onboard any Linux laptop/server with:"
echo "   sudo ./deploy/install-agent.sh --server https://${HOST_IP} --enrollment-key ${AGENT_ENROLLMENT_KEY} --ca-cert ./deploy/nginx/certs/cyberlab.crt"
echo ""
echo " IMPORTANT: Log in as 'admin' (CyberLab@Admin2026!) and rotate default passwords immediately."
echo "=========================================="
