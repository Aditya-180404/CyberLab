"""
Authentication API Router
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.core.config import settings

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials, generates JWT token, and records an audit log entry."""
    client_ip = request.client.host if request.client else "unknown"

    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        # Audit failure attempt
        failure_log = AuditLog(
            username=payload.username,
            action="USER_LOGIN_FAILED",
            resource_type="auth",
            resource_id=user.id if user else None,
            status="FAILURE",
            ip_address=client_ip,
            details=f"Failed login attempt for username: {payload.username}"
        )
        db.add(failure_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact system administrator."
        )

    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    
    # Audit successful login
    success_log = AuditLog(
        user_id=user.id,
        username=user.username,
        action="USER_LOGIN_SUCCESS",
        resource_type="auth",
        resource_id=user.id,
        status="SUCCESS",
        ip_address=client_ip,
        details="User authenticated successfully"
    )
    db.add(success_log)
    db.commit()

    token_data = {
        "sub": user.id,
        "username": user.username,
        "role": user.role
    }
    access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user={
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id
        }
    )


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Returns profile information for the authenticated user."""
    return current_user


@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logs the user logout event in the audit trail."""
    logout_log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="USER_LOGOUT",
        resource_type="auth",
        resource_id=current_user.id,
        status="SUCCESS",
        details="User logged out"
    )
    db.add(logout_log)
    db.commit()
    return {"message": "Successfully logged out"}
