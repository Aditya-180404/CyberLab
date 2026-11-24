# CyberLab PostgreSQL Migration Path & Production Hardening Guide

**Platform Version**: v1.0 Production Release  
**Target Environments**: Enterprise Self-Hosted, Cloud VPC (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL), High-Availability On-Premises Clusters.

---

## 1. Dual-Database Architecture Overview

CyberLab is engineered with a **dual-database abstraction layer** in `backend/app/database/session.py`. It provides seamless portability between lightweight single-node development (SQLite WAL) and horizontally scalable enterprise production (PostgreSQL 15+).

```
                      ┌──────────────────────────────────────┐
                      │    FastAPI Backend / SQLAlchemy 2    │
                      └──────────────────┬───────────────────┘
                                         │
                    DATABASE_URL environment variable check
                                         │
               ┌─────────────────────────┴─────────────────────────┐
               ▼                                                   ▼
     "sqlite://..." (Dev/Lab)                            "postgresql://..." (Production)
┌─────────────────────────────────┐                 ┌─────────────────────────────────┐
│ • SQLite with WAL journal mode  │                 │ • Connection Pooling (QueuePool)│
│ • Foreign key pragma enabled    │                 │ • Multi-worker concurrency      │
│ • Zero zero-conf local file     │                 │ • Full ACID / Row-level locking │
│ • Synchronous NORMAL for speed  │                 │ • Multi-site enterprise scaling │
└─────────────────────────────────┘                 └─────────────────────────────────┘
```

---

## 2. PostgreSQL Prerequisites

Ensure your PostgreSQL cluster meets the following baseline requirements:
- **Engine Version**: PostgreSQL 15.x or 16.x
- **Extensions Required**: `uuid-ossp` or `pgcrypto` (optional, as CyberLab generates canonical UUID4s in application code), `pg_trgm` (for fast log searching).
- **Recommended Hardware**:
  - Minimum: 2 vCPUs, 4 GB RAM, SSD storage.
  - Production Enterprise Fleet (50+ agents, high-frequency SIEM ingestion): 4+ vCPUs, 16 GB RAM, NVMe storage.

### Dedicated Database & User Provisioning

Execute the following in `psql` as a superuser:

```sql
-- Create CyberLab database user
CREATE USER cyberlab_app WITH PASSWORD 'ChangeMeSecurePassword_2026!';

-- Create CyberLab production database
CREATE DATABASE cyberlab_db WITH OWNER cyberlab_app ENCODING 'UTF8';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE cyberlab_db TO cyberlab_app;

-- Connect to cyberlab_db and grant schema usage
\c cyberlab_db
GRANT ALL ON SCHEMA public TO cyberlab_app;
```

---

## 3. Configuration & Environment Variables

To switch the CyberLab backend to PostgreSQL, configure the `DATABASE_URL` environment variable in `backend/.env` or in your systemd / container environment:

```env
# -------------------------------------------------------------
# CyberLab Production Database Configuration (PostgreSQL 15+)
# -------------------------------------------------------------
DATABASE_URL=postgresql://cyberlab_app:ChangeMeSecurePassword_2026!@127.0.0.1:5432/cyberlab_db

# Connection Pool Tuning (Optional, defaults configured in session.py)
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Environment Mode
ENVIRONMENT=production
DEBUG=false
```

When `DATABASE_URL` begins with `postgresql://` or `postgres://`, `backend/app/database/session.py` automatically:
1. Omits SQLite-specific `connect_args={"check_same_thread": False}`.
2. Bypasses SQLite PRAGMA execution listeners.
3. Leverages SQLAlchemy's enterprise `QueuePool` with automatic recycling and pre-ping connection liveness verification.

---

## 4. Database Schema Migration via Alembic

CyberLab includes a complete Alembic migration workflow to manage schema evolution.

### Step 1: Initialize Alembic (if configuring from scratch)

```bash
cd /home/ghost/Desktop/CyberLab/backend
alembic init alembic
```

### Step 2: Configure `alembic/env.py`

Ensure `alembic/env.py` imports CyberLab's SQLAlchemy `Base`:

```python
from app.database.session import Base
from app.models import *  # Ingests all models (Asset, Agent, Incident, Site, Vulnerability, etc.)

target_metadata = Base.metadata
```

### Step 3: Generate and Apply Migration Revision

```bash
# Generate the initial schema migration script
alembic revision --autogenerate -m "CyberLab v1.0 Production Schema"

# Execute migration against PostgreSQL
alembic upgrade head
```

Alternatively, running the application bootstrap (`python -m app.main`) will automatically invoke `Base.metadata.create_all(bind=engine)`, creating all 18 tables and relationships safely.

---

## 5. Data Migration from SQLite WAL to PostgreSQL

If you have existing assets, agents, network topologies, and audit logs in `cyberlab.db` and wish to migrate them to PostgreSQL without data loss, use `pgloader`.

### Installing `pgloader` (Debian/Ubuntu/Kali)

```bash
sudo apt-get update && sudo apt-get install -y pgloader
```

### Migration Command

Create a migration descriptor `migrate.load`:

```lisp
LOAD DATABASE
     FROM sqlite:///home/ghost/Desktop/CyberLab/backend/cyberlab.db
     INTO postgresql://cyberlab_app:ChangeMeSecurePassword_2026!@127.0.0.1:5432/cyberlab_db

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '64MB', maintenance_work_mem to '256MB';
```

Execute the migration:

```bash
pgloader migrate.load
```

---

## 6. Production Security & Hardening Checklist

| Domain | Control | Recommendation |
|---|---|---|
| **Network Security** | PostgreSQL Binding | Listen exclusively on `127.0.0.1` or internal VPC subnet. Never expose port 5432 to public interfaces. |
| **Transport Encryption** | SSL / TLS | Enforce `sslmode=require` or `sslmode=verify-full` in `DATABASE_URL`. |
| **Authentication** | Password Security | Use `scram-sha-256` password hashing in `pg_hba.conf`. |
| **Backup Automation** | Disaster Recovery | Schedule daily physical `pg_dump` snapshots and WAL archiving with retention policies. |
| **Connection Pooling** | Concurrency | For large fleets (>100 active EDR agents), deploy `PgBouncer` in transaction pooling mode. |
| **Host System** | Principle of Least Privilege | Run FastAPI and PostgreSQL under dedicated non-root service accounts (`cyberlab`, `postgres`). |
