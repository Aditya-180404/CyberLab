"""
User Administration API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.user import UserResponse, UserCreate
from app.core.security import get_password_hash
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER])),
    db: Session = Depends(get_db)
):
    """Lists system users with pagination. Requires administrative or SOC Manager role."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])),
    db: Session = Depends(get_db)
):
    """Creates a new user. Enforces uniqueness and logs to audit trail."""
    # Check if username or email already exists
    existing = db.query(User).filter(
        (User.username == payload.username) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username or email already exists"
        )

    if payload.role not in UserRole.ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles: {', '.join(UserRole.ALL_ROLES)}"
        )

    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
        organization_id=payload.organization_id or current_user.organization_id
    )
    db.add(new_user)
    db.flush()

    # Record in audit trail
    audit_entry = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="USER_CREATED",
        resource_type="user",
        resource_id=new_user.id,
        status="SUCCESS",
        details=f"Created user {new_user.username} with role {new_user.role}"
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Gets details of a specific user. Users may view themselves, admins may view any."""
    if current_user.id != user_id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this user profile"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
