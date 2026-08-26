"""
Tests unitaires pour les incidents.
"""

import pytest
from fastapi import status


class TestCreateIncident:
    """Tests pour la création d'incidents"""

    def test_create_incident_success(self, client, admin_token):
        """Test création d'incident réussie"""
        response = client.post(
            "/api/v1/incidents/",
            json={
                "title": "Test Incident",
                "description": "Description de test pour l'incident",
                "severity": "high",
                "category": "phishing"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Incident"
        assert data["severity"] == "high"
        assert data["status"] == "open"

    def test_create_incident_unauthorized(self, client):
        """Test création sans authentification"""
        response = client.post(
            "/api/v1/incidents/",
            json={
                "title": "Test Incident",
                "description": "Description de test",
                "severity": "high",
                "category": "phishing"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_incident_invalid_severity(self, client, admin_token):
        """Test création avec sévérité invalide"""
        response = client.post(
            "/api/v1/incidents/",
            json={
                "title": "Test Incident",
                "description": "Description de test",
                "severity": "invalid",
                "category": "phishing"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListIncidents:
    """Tests pour la liste des incidents"""

    def test_list_incidents_admin(self, client, admin_token, sample_incident):
        """Test liste des incidents par admin"""
        response = client.get(
            "/api/v1/incidents/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_list_incidents_with_filter(self, client, admin_token, sample_incident):
        """Test liste avec filtre par sévérité"""
        response = client.get(
            "/api/v1/incidents/?severity=high",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for item in data["items"]:
            assert item["severity"] == "high"

    def test_list_incidents_reporter_sees_own(self, client, db, reporter_user, reporter_token, sample_incident):
        """Test que le reporter ne voit que ses propres incidents"""
        # Le reporter ne devrait pas voir l'incident créé par admin
        response = client.get(
            "/api/v1/incidents/",
            headers={"Authorization": f"Bearer {reporter_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0


class TestGetIncident:
    """Tests pour récupérer un incident"""

    def test_get_incident_success(self, client, admin_token, sample_incident):
        """Test récupération d'un incident"""
        response = client.get(
            f"/api/v1/incidents/{sample_incident.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_incident.id
        assert data["title"] == sample_incident.title

    def test_get_incident_not_found(self, client, admin_token):
        """Test récupération incident inexistant"""
        response = client.get(
            "/api/v1/incidents/9999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_incident_reporter_forbidden(self, client, reporter_token, sample_incident):
        """Test que le reporter ne peut pas voir les incidents des autres"""
        response = client.get(
            f"/api/v1/incidents/{sample_incident.id}",
            headers={"Authorization": f"Bearer {reporter_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateIncident:
    """Tests pour la mise à jour d'incidents"""

    def test_update_incident_success(self, client, admin_token, sample_incident):
        """Test mise à jour réussie"""
        response = client.put(
            f"/api/v1/incidents/{sample_incident.id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["title"] == "Updated Title"

    def test_update_incident_reporter_forbidden(self, client, reporter_token, sample_incident):
        """Test que le reporter ne peut pas modifier"""
        response = client.put(
            f"/api/v1/incidents/{sample_incident.id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {reporter_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteIncident:
    """Tests pour la suppression d'incidents"""

    def test_delete_incident_admin(self, client, admin_token, sample_incident):
        """Test suppression par admin"""
        response = client.delete(
            f"/api/v1/incidents/{sample_incident.id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_incident_analyst_forbidden(self, client, analyst_token, sample_incident):
        """Test que l'analyst ne peut pas supprimer"""
        response = client.delete(
            f"/api/v1/incidents/{sample_incident.id}",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestIncidentStats:
    """Tests pour les statistiques"""

    def test_get_stats_analyst(self, client, analyst_token, sample_incident):
        """Test récupération des stats par analyst"""
        response = client.get(
            "/api/v1/incidents/stats/summary",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total" in data
        assert "by_status" in data
        assert "by_severity" in data

    def test_get_stats_reporter_forbidden(self, client, reporter_token):
        """Test que le reporter ne peut pas voir les stats"""
        response = client.get(
            "/api/v1/incidents/stats/summary",
            headers={"Authorization": f"Bearer {reporter_token}"}
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
