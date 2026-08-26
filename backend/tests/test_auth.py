"""
Tests unitaires pour l'authentification.
"""

import pytest
from fastapi import status


class TestRegister:
    """Tests pour l'inscription"""

    def test_register_success(self, client):
        """Test inscription réussie"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "username": "newuser",
                "full_name": "New User",
                "password": "Password123!",
                "role": "reporter"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["username"] == "newuser"
        assert data["role"] == "reporter"
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, admin_user):
        """Test inscription avec email existant"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@test.com",
                "username": "newadmin",
                "full_name": "New Admin",
                "password": "Password123!",
                "role": "admin"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, admin_user):
        """Test inscription avec username existant"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@test.com",
                "username": "admin",
                "full_name": "New Admin",
                "password": "Password123!",
                "role": "admin"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "utilisateur" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test inscription avec email invalide"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "full_name": "Test User",
                "password": "Password123!",
                "role": "reporter"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """Test inscription avec mot de passe trop court"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                "username": "testuser",
                "full_name": "Test User",
                "password": "short",
                "role": "reporter"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestLogin:
    """Tests pour la connexion"""

    def test_login_success(self, client, admin_user):
        """Test connexion réussie"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "Admin123!"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, admin_user):
        """Test connexion avec mauvais mot de passe"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """Test connexion avec utilisateur inexistant"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@test.com", "password": "Password123!"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestMe:
    """Tests pour l'endpoint /me"""

    def test_get_current_user(self, client, admin_token):
        """Test récupération du profil utilisateur"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["role"] == "admin"

    def test_get_current_user_no_token(self, client):
        """Test accès sans token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """Test accès avec token invalide"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshToken:
    """Tests pour le rafraîchissement de token"""

    def test_refresh_token_success(self, client, admin_user):
        """Test rafraîchissement de token réussi"""
        # D'abord se connecter
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "Admin123!"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Puis rafraîchir
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        """Test rafraîchissement avec token invalide"""
        response = client.post(
            "/api/v1/auth/refresh",
            params={"refresh_token": "invalid_token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
