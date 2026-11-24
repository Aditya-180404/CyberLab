# CyberLab v1.0.0 — Production Deployment & Hardening Checklist

**Target**: Enterprise SOC & Laboratory Production Deployments  
**Auditor Roles**: DevSecOps Engineer, Systems Architect  

Before transitioning CyberLab v1.0.0 into a production environment, operations and security teams must complete the following mandatory hardening checklist.

---

## 1. Secrets & Cryptographic Configuration

- [ ] **Static Cryptographic Secret Key**:
  Generate and set a high-entropy 256-bit secret key in the production environment:
  ```bash
  export SECRET_KEY=$(openssl rand -hex 32)
  ```
  *Never allow the backend to fall back to volatile auto-generated keys in production.*
- [ ] **Rotate Default Seeded Administrative Credentials**:
  Immediately change passwords for `admin`, `analyst`, `engineer`, and `auditor` via `/api/v1/users` or database update.
- [ ] **Agent Enrollment Key**:
  Configure an agent registration pre-shared key (`AGENT_ENROLLMENT_KEY`) so that rogue agents cannot register without authorization.

---

## 2. Database & Persistence Layer

- [ ] **PostgreSQL 15+ Provisioning**:
  Transition from local SQLite to dedicated PostgreSQL with connection pooling and TLS enabled:
  ```env
  DATABASE_URL=postgresql://cyberlab_app:SecureDBPassword@10.0.1.50:5432/cyberlab_db?sslmode=require
  ```
- [ ] **Package Installation**:
  Ensure production runtime environment installs required database and graph packages:
  ```bash
  pip install psycopg2-binary>=2.9.9 networkx>=3.4.2 alembic>=1.13.0
  ```
- [ ] **Automated Backup Strategy**:
  Schedule daily compressed PostgreSQL database backups and WAL archiving.

---

## 3. Server Runtime & Process Hardening

- [ ] **Dedicated Non-Root Service Account**:
  Create an unprivileged system user for running the application:
  ```bash
  sudo useradd -r -s /bin/false -d /opt/cyberlab cyberlab
  ```
- [ ] **Production ASGI Execution**:
  Run Uvicorn without development reload flags and with worker scaling:
  ```bash
  uvicorn app.main:app \
      --host 127.0.0.1 \
      --port 8000 \
      --workers 4 \
      --proxy-headers \
      --forwarded-allow-ips="127.0.0.1" \
      --no-server-header
  ```
- [ ] **Environment Mode**:
  Set `ENVIRONMENT=production` in the environment to disable verbose internal error traces.

---

## 4. Reverse Proxy & Network Perimeter

- [ ] **Nginx Reverse Proxy & TLS 1.3 Termination**:
  Terminate HTTPS externally; never expose Uvicorn port 8000 to public or untrusted lab interfaces.
  ```nginx
  server {
      listen 443 ssl http2;
      server_name cyberlab.enterprise.internal;

      ssl_certificate /etc/ssl/certs/cyberlab.crt;
      ssl_certificate_key /etc/ssl/private/cyberlab.key;
      ssl_protocols TLSv1.2 TLSv1.3;

      # Rate Limiting Zone
      limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
      limit_req zone=api_limit burst=20 nodelay;

      location /api/ {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }

      location / {
          proxy_pass http://127.0.0.1:3000;
      }
  }
  ```
- [ ] **CORS Origins Hardening**:
  Restrict `CORS_ORIGINS` in `config.py` to the exact corporate or laboratory domain.

---

## 5. Security & Isolation Controls

- [ ] **Vulnerable VM Network Isolation**:
  Confirm in the Virtual Machines workspace that all vulnerable lab targets (Metasploitable, VulnHub) are bound to **Host-Only (`vmnet1`)** or simulated Linux bridges, and are **NOT in Bridged (`vmnet0`) mode**.
- [ ] **Endpoint Agent HTTPS Configuration**:
  Direct all distributed endpoint agents to the verified HTTPS domain (`--server https://cyberlab.enterprise.internal`).
- [ ] **Liveness & Health Monitoring**:
  Integrate `/api/v1/health` into external uptime and SOC monitoring probes.
