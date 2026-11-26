"""
Authentication API Router
"""
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, RevokedToken
from app.models.audit import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest
from app.schemas.user import UserResponse
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.dependencies import get_current_user
from app.core.config import settings

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)
_failed_login_attempts: Dict[str, List[datetime]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> None:
    """Enforces sliding-window login rate limiting against failed credential stuffing."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=60)
    recent = [ts for ts in _failed_login_attempts[client_ip] if ts > cutoff]
    _failed_login_attempts[client_ip] = recent
    if len(recent) >= 15:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again in 60 seconds."
        )


@router.post("/auth/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials, generates JWT token, and records an audit log entry."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    user = db.query(User).filter(User.username == payload.username).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        _failed_login_attempts[client_ip].append(datetime.now(timezone.utc))
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


@router.post("/auth/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rotates the authenticated user's password."""
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="USER_PASSWORD_CHANGED",
        resource_type="auth",
        resource_id=current_user.id,
        status="SUCCESS",
        details="User rotated password",
    ))
    db.commit()
    return {"message": "Password updated successfully"}


@router.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revokes the current JWT token (via jti blacklist) and logs logout in the audit trail."""
    if credentials:
        try:
            claims = decode_access_token(credentials.credentials)
            jti = claims.get("jti")
            if jti and not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
                db.add(RevokedToken(jti=jti, username=current_user.username))
        except Exception:
            pass

    logout_log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="USER_LOGOUT",
        resource_type="auth",
        resource_id=current_user.id,
        status="SUCCESS",
        details="User logged out and token revoked"
    )
    db.add(logout_log)
    db.commit()
    return {"message": "Successfully logged out"}
