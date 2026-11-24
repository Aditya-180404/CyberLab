"""
CyberLab Configuration Management
"""
import os
import secrets
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberLab"
    TAGLINE: str = "Hybrid Cybersecurity Infrastructure & SOC Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Cryptographic secret for signing tokens
    # Generates a secure random 32-byte secret if not provided in env
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database Configuration (SQLite default with WAL mode for Phase 1)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cyberlab.db")

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Host Protection: Interfaces strictly excluded from mutation
    PROTECTED_INTERFACES: List[str] = [
        "lo",
        "wlan0",
        "eth0",
        "wlp",
        "enp",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
