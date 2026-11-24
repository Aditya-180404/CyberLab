"""
CyberLab Database Seeding Script
"""
import logging
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.models.site import Site
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.core.security import get_password_hash

logger = logging.getLogger("cyberlab.seed")


def seed_database(db: Session) -> None:
    """Populates baseline organization, site, and RBAC users if not already present."""
    # 1. Organization & Site
    org = db.query(Organization).first()
    if not org:
        logger.info("Seeding default CyberLab organization and site...")
        org = Organization(
            name="CyberLab Primary Research Lab",
            slug="primary-lab"
        )
        db.add(org)
        db.flush()

        site = Site(
            organization_id=org.id,
            name="HQ Sandbox Infrastructure Site",
            description="Default isolated network simulation and hypervisor cluster"
        )
        db.add(site)
        db.commit()

    # 2. Users
    user_count = db.query(User).count()
    if user_count == 0:
        logger.info("Seeding default RBAC accounts...")
        default_users = [
            {
                "username": "admin",
                "email": "admin@cyberlab.local",
                "password": "CyberLab@Admin2026!",
                "role": UserRole.SUPER_ADMIN,
            },
            {
                "username": "analyst",
                "email": "analyst@cyberlab.local",
                "password": "Analyst@CyberLab2026!",
                "role": UserRole.SOC_ANALYST,
            },
            {
                "username": "engineer",
                "email": "engineer@cyberlab.local",
                "password": "Engineer@CyberLab2026!",
                "role": UserRole.NETWORK_ENGINEER,
            },
            {
                "username": "auditor",
                "email": "auditor@cyberlab.local",
                "password": "Auditor@CyberLab2026!",
                "role": UserRole.AUDITOR,
            },
        ]

        for u in default_users:
            user = User(
                organization_id=org.id,
                username=u["username"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                is_active=True,
                is_verified=True
            )
            db.add(user)

        # Log system initialization in immutable audit table
        init_audit = AuditLog(
            username="system",
            action="SYSTEM_INITIALIZE",
            resource_type="system",
            resource_id="cyberlab-core",
            status="SUCCESS",
            ip_address="127.0.0.1",
            details="Database seeded with default organization, site, and baseline RBAC administrative accounts"
        )
        db.add(init_audit)
        db.commit()
        logger.info("Database seeding complete.")
