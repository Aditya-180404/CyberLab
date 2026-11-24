# CyberLab Database Design

## 1. Overview

CyberLab uses **SQLAlchemy 2.0** ORM.
- **Initial Engine**: SQLite with Write-Ahead Logging (`journal_mode=WAL`) and foreign keys enforced (`PRAGMA foreign_keys=ON`).
- **Target Engine**: PostgreSQL (fully supported via standard SQLAlchemy dialect abstractions without schema redesign).

---

## 2. Entity-Relationship Overview (Phase 1 Baseline & Incremental Entities)

```
       +-------------------+
       |   Organization    |
       +---------+---------+
                 | 1:N
       +---------v---------+
       |       Site        |
       +---------+---------+
                 | 1:N
       +---------+-------------------+
       |                             |
+------v------+               +------v------+
|    User     |               |    Agent    | (Phase 4)
+------+------+               +------+------+
       | 1:N                         | 1:N
+------v------+               +------v------+
|  AuditLog   |               | SecurityEvent | (Phase 6)
+-------------+               +------+------+
                                     | 1:N
                              +------v------+
                              |  Incident   | (Phase 6/7)
                              +-------------+
```

---

## 3. Phase 1 Database Tables

### 3.1 `organizations`
Represents customer/institution tenant boundaries.
- `id`: String (UUIDv4), Primary Key
- `name`: String(100), Unique, Not Null
- `slug`: String(100), Unique, Not Null
- `created_at`: DateTime(timezone=True)
- `updated_at`: DateTime(timezone=True)

### 3.2 `sites`
Represents physical or logical network locations.
- `id`: String (UUIDv4), Primary Key
- `organization_id`: String (UUIDv4), Foreign Key -> `organizations.id`
- `name`: String(100), Not Null
- `description`: Text, Nullable
- `created_at`: DateTime(timezone=True)

### 3.3 `users`
System accounts with strict role-based access control.
- `id`: String (UUIDv4), Primary Key
- `organization_id`: String (UUIDv4), Foreign Key -> `organizations.id`, Nullable
- `username`: String(50), Unique, Indexed, Not Null
- `email`: String(255), Unique, Indexed, Not Null
- `hashed_password`: String(255), Not Null
- `role`: String(50), Default 'soc_analyst', Not Null (`super_admin`, `org_admin`, `soc_manager`, `soc_analyst`, `network_engineer`, `auditor`)
- `is_active`: Boolean, Default True, Not Null
- `is_verified`: Boolean, Default True, Not Null
- `created_at`: DateTime(timezone=True)
- `last_login`: DateTime(timezone=True), Nullable

### 3.4 `audit_logs`
Immutable record of all security-sensitive actions and operations.
- `id`: String (UUIDv4), Primary Key
- `user_id`: String (UUIDv4), Foreign Key -> `users.id`, Nullable
- `username`: String(50), Not Null
- `action`: String(100), Not Null
- `resource_type`: String(100), Not Null
- `resource_id`: String(100), Nullable
- `status`: String(20), Not Null (`SUCCESS`, `FAILURE`, `DENIED`)
- `ip_address`: String(45), Nullable
- `details`: JSON / Text, Nullable
- `created_at`: DateTime(timezone=True), Indexed

---

## 4. Migration Strategy
Phase 1 uses automatic table creation via SQLAlchemy metadata during local initialization, supplemented with Alembic migration scaffolding ready for schema evolution across Phase 2 through Phase 12.
