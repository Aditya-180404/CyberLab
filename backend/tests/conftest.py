"""
Pytest Test Fixtures & In-Memory Database Configuration
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.session import Base, get_db
from app.database.seed import seed_database
from app.main import app

# Create in-memory SQLite database for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "CyberLab@Admin2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def analyst_token(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst", "password": "Analyst@CyberLab2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auditor_token(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "auditor", "password": "Auditor@CyberLab2026!"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
