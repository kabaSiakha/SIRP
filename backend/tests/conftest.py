"""
Configuration des tests pytest pour SIRP.
Fixtures partagées pour tous les tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base
from app.core.deps import get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentCategory


# Base de données en mémoire pour les tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de la dépendance get_db pour les tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Fixture pour la base de données de test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Fixture pour le client de test FastAPI"""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)

    with TestClient(app) as c:
        yield c

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db):
    """Fixture pour créer un utilisateur admin"""
    user = User(
        email="admin@test.com",
        username="admin",
        full_name="Admin Test",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def analyst_user(db):
    """Fixture pour créer un utilisateur analyst"""
    user = User(
        email="analyst@test.com",
        username="analyst",
        full_name="Analyst Test",
        hashed_password=get_password_hash("Analyst123!"),
        role=UserRole.ANALYST,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def reporter_user(db):
    """Fixture pour créer un utilisateur reporter"""
    user = User(
        email="reporter@test.com",
        username="reporter",
        full_name="Reporter Test",
        hashed_password=get_password_hash("Reporter123!"),
        role=UserRole.REPORTER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_incident(db, admin_user):
    """Fixture pour créer un incident de test"""
    incident = Incident(
        title="Test Incident",
        description="Description de l'incident de test",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        category=IncidentCategory.PHISHING,
        created_by=admin_user.id
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_auth_token(client, email: str, password: str) -> str:
    """Helper pour obtenir un token d'authentification"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    """Fixture pour obtenir un token admin"""
    return get_auth_token(client, "admin@test.com", "Admin123!")


@pytest.fixture
def analyst_token(client, analyst_user):
    """Fixture pour obtenir un token analyst"""
    return get_auth_token(client, "analyst@test.com", "Analyst123!")


@pytest.fixture
def reporter_token(client, reporter_user):
    """Fixture pour obtenir un token reporter"""
    return get_auth_token(client, "reporter@test.com", "Reporter123!")
