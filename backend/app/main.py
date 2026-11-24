"""
CyberLab Central Backend Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.database.seed import seed_database
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.api.v1 import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberlab.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema and baseline data during startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    
    # 1. Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized.")

    # 2. Seed initial organization, site, and RBAC users
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        logger.error(f"Error during database seed: {e}")
        db.rollback()
    finally:
        db.close()

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CyberLab Hybrid Cybersecurity Infrastructure, Network Simulation, Endpoint Security & SOC Platform API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware Pipeline
# 1. Custom Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request Logging & Metrics
app.add_middleware(LoggingMiddleware)

# 3. Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The submitted request failed schema validation.",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request."
        }
    )


# Root informational endpoint
@app.get("/", tags=["System"])
def root():
    return {
        "project": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }


# Mount API v1 Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
