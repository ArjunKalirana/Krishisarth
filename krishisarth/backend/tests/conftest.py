import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock

from app.main import app
from app.db.postgres import get_db, Base
from app.db.redis import get_redis
from app.services import auth_service
from app.models import Farmer
from app.core.config import settings

# Dedicated Test Database URL (Match your local Postgres setup)
# Ensure 'krishisarth_test' database exists before running integration tests
TEST_DB_URL = "postgresql://postgres:postgres@localhost:5432/krishisarth_test"

engine = create_engine(TEST_DB_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in the test database once per session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db() -> Generator:
    """Provides a transactional database session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_redis():
    """Returns a MagicMock for Redis operations."""
    return MagicMock()

@pytest.fixture
def client(db: Session, mock_redis) -> Generator:
    """
    FastAPI TestClient with database and redis dependency overrides.
    """
    def override_get_db():
        yield db
        
    def override_get_redis():
        yield mock_redis
        
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

@pytest.fixture
def test_farmer(db: Session) -> Farmer:
    """Seeds a single farmer for authenticated testing."""
    farmer = Farmer(
        email="test_auth@krishisarth.test",
        name="Test Auth User",
        password_hash=auth_service.hash_password("testpassword123")
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer

@pytest.fixture
def auth_headers(test_farmer: Farmer) -> dict:
    """Returns Bearer token headers for the test farmer."""
    access_token = auth_service.create_access_token(test_farmer.id)
    return {"Authorization": f"Bearer {access_token}"}
