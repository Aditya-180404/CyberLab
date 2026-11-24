# CyberLab v1.0.0 — PostgreSQL Production Readiness & Migration Audit

**Component Audited**: `backend/app/database/` (`session.py`, `seed.py`), `backend/requirements.txt`  
**Target Architecture**: PostgreSQL 15+ Enterprise Deployment  
**Auditor Roles**: Senior Backend Engineer, Database Administrator, DevSecOps Engineer  

---

## 1. Dual-Database Engine Architecture

CyberLab provides an abstraction layer in `backend/app/database/session.py` designed to run against both SQLite WAL and PostgreSQL 15+:

```python
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
```

---

## 2. Readiness Evaluation & Deficits

### Deficit 1: Missing Database Drivers in Packaging (`requirements.txt`)
- **Status**: **BLOCKER FOR FRESH DEPLOYMENTS**
- **Evidence**:
  ```
  fastapi>=0.115.0
  uvicorn[standard]>=0.32.0
  pydantic>=2.9.0
  pydantic-settings>=2.5.0
  sqlalchemy>=2.0.35
  pyjwt>=2.9.0
  bcrypt>=4.2.0
  httpx>=0.27.2
  pytest>=8.3.3
  pytest-asyncio>=0.24.0
  psutil>=6.1.0
  ```
- **Auditor Assessment**: Neither `psycopg2-binary` nor `asyncpg` is specified in `requirements.txt`. While Kali Linux happened to have system-wide `python3-psycopg2` installed, deploying in Docker, Kubernetes, Alpine, or a clean Ubuntu/Debian server from `requirements.txt` will immediately fail with:
  ```
  ModuleNotFoundError: No module named 'psycopg2'
  ```
- **Correction**: Add `psycopg2-binary>=2.9.9` and `alembic>=1.13.0` to `requirements.txt`.

### Deficit 2: Lack of Production Connection Pool Tuning
- In `backend/app/database/session.py`, `create_engine` does not explicitly set enterprise connection pool parameters:
  - `pool_size` (defaults to 5)
  - `max_overflow` (defaults to 10)
  - `pool_timeout` (defaults to 30)
  - `pool_recycle` (recommend 1800s to avoid stale firewall drops)
  - `pool_pre_ping=True` (essential to prevent broken pipe disconnects after idle periods)
- **Recommendation**: Pass pool configuration parameters when `DATABASE_URL` starts with `postgresql://`.

### Deficit 3: DDL Evolution via `create_all` rather than Versioned Migrations
- Currently, `main.py` invokes `Base.metadata.create_all(bind=engine)` during startup.
- `create_all` only creates tables if they do not exist; **it cannot alter existing columns, add constraints, or modify column types**.
- In production, schema changes must be applied via managed migrations using Alembic.

---

## 3. SQLite to PostgreSQL Data Migration Procedure

To migrate existing lab assets, topologies, and historical telemetry without data loss:

1. **Provision Target PostgreSQL Instance**:
   ```sql
   CREATE DATABASE cyberlab_db WITH OWNER cyberlab_app ENCODING 'UTF8';
   ```
2. **Export or Direct Transfer via `pgloader`**:
   ```lisp
   LOAD DATABASE
        FROM sqlite:///home/ghost/Desktop/CyberLab/backend/cyberlab.db
        INTO postgresql://cyberlab_app:SecurePassword@127.0.0.1:5432/cyberlab_db
   WITH include drop, create tables, create indexes, reset sequences;
   ```
3. **Configure Environment Variable**:
   ```env
   DATABASE_URL=postgresql://cyberlab_app:SecurePassword@127.0.0.1:5432/cyberlab_db?sslmode=require
   ```
4. **Liveness & Concurrency Verification**:
   Execute backend test suite pointing to disposable PostgreSQL container to verify transaction isolation, foreign-key cascade integrity, and concurrency.
