"""
Tests unitaires pour le workflow des incidents.
"""

import pytest
from fastapi import status

from app.models.incident import IncidentStatus
from app.models.user import UserRole
from app.core.workflow import validate_transition, get_allowed_transitions


class TestWorkflowValidation:
    """Tests pour la validation des transitions"""

    def test_valid_transition_open_to_in_progress(self):
        """Test transition valide: OPEN -> IN_PROGRESS"""
        config = validate_transition(
            IncidentStatus.OPEN,
            IncidentStatus.IN_PROGRESS,
            UserRole.ANALYST
        )
        assert config["action"] == "prise_en_charge"

    def test_valid_transition_in_progress_to_resolved(self):
        """Test transition valide: IN_PROGRESS -> RESOLVED"""
        config = validate_transition(
            IncidentStatus.IN_PROGRESS,
            IncidentStatus.RESOLVED,
            UserRole.ANALYST
        )
        assert config["action"] == "resolution"

    def test_valid_transition_resolved_to_closed(self):
        """Test transition valide: RESOLVED -> CLOSED"""
        config = validate_transition(
            IncidentStatus.RESOLVED,
            IncidentStatus.CLOSED,
            UserRole.ANALYST
        )
        assert config["action"] == "fermeture"

    def test_invalid_transition_open_to_closed(self):
        """Test transition invalide: OPEN -> CLOSED"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(
                IncidentStatus.OPEN,
                IncidentStatus.CLOSED,
                UserRole.ADMIN
            )
        assert exc_info.value.status_code == 400
        assert "Transition invalide" in exc_info.value.detail

    def test_invalid_transition_open_to_resolved(self):
        """Test transition invalide: OPEN -> RESOLVED"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(
                IncidentStatus.OPEN,
                IncidentStatus.RESOLVED,
                UserRole.ADMIN
            )
        assert exc_info.value.status_code == 400

    def test_same_status_transition(self):
        """Test transition vers le même statut"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(
                IncidentStatus.OPEN,
                IncidentStatus.OPEN,
                UserRole.ADMIN
            )
        assert exc_info.value.status_code == 400
        assert "déjà en statut" in exc_info.value.detail

    def test_reopen_closed_admin_only(self):
        """Test réouverture d'incident fermé - admin uniquement"""
        # Admin peut réouvrir
        config = validate_transition(
            IncidentStatus.CLOSED,
            IncidentStatus.IN_PROGRESS,
            UserRole.ADMIN
        )
        assert config["action"] == "reouverture_exceptionnelle"

        # Analyst ne peut pas
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_transition(
                IncidentStatus.CLOSED,
                IncidentStatus.IN_PROGRESS,
                UserRole.ANALYST
            )
        assert exc_info.value.status_code == 403


class TestAllowedTransitions:
    """Tests pour récupérer les transitions possibles"""

    def test_transitions_from_open(self):
        """Test transitions depuis OPEN"""
        transitions = get_allowed_transitions(IncidentStatus.OPEN, UserRole.ANALYST)
        assert len(transitions) == 1
        assert transitions[0]["to_status"] == "in_progress"

    def test_transitions_from_in_progress(self):
        """Test transitions depuis IN_PROGRESS"""
        transitions = get_allowed_transitions(IncidentStatus.IN_PROGRESS, UserRole.ANALYST)
        assert len(transitions) == 2
        statuses = [t["to_status"] for t in transitions]
        assert "resolved" in statuses
        assert "open" in statuses

    def test_transitions_from_resolved(self):
        """Test transitions depuis RESOLVED"""
        transitions = get_allowed_transitions(IncidentStatus.RESOLVED, UserRole.ANALYST)
        assert len(transitions) == 2
        statuses = [t["to_status"] for t in transitions]
        assert "closed" in statuses
        assert "in_progress" in statuses

    def test_transitions_from_closed_admin(self):
        """Test transitions depuis CLOSED pour admin"""
        transitions = get_allowed_transitions(IncidentStatus.CLOSED, UserRole.ADMIN)
        assert len(transitions) == 1
        assert transitions[0]["to_status"] == "in_progress"

    def test_transitions_from_closed_analyst(self):
        """Test transitions depuis CLOSED pour analyst (aucune)"""
        transitions = get_allowed_transitions(IncidentStatus.CLOSED, UserRole.ANALYST)
        assert len(transitions) == 0


class TestWorkflowAPI:
    """Tests pour les endpoints du workflow"""

    def test_change_status_open_to_in_progress(self, client, admin_token, sample_incident):
        """Test changement de statut via API"""
        response = client.patch(
            f"/api/v1/incidents/{sample_incident.id}/status?new_status=in_progress",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "in_progress"

    def test_change_status_invalid_transition(self, client, admin_token, sample_incident):
        """Test transition invalide via API"""
        response = client.patch(
            f"/api/v1/incidents/{sample_incident.id}/status?new_status=closed",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Transition invalide" in response.json()["detail"]

    def test_get_transitions_endpoint(self, client, admin_token, sample_incident):
        """Test endpoint des transitions possibles"""
        response = client.get(
            f"/api/v1/incidents/{sample_incident.id}/transitions",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["current_status"] == "open"
        assert len(data["allowed_transitions"]) == 1

    def test_workflow_diagram_endpoint(self, client, admin_token):
        """Test endpoint du diagramme workflow"""
        response = client.get(
            "/api/v1/incidents/workflow/diagram",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "open" in data
        assert "in_progress" in data
        assert "resolved" in data
        assert "closed" in data

    def test_full_workflow_cycle(self, client, admin_token, sample_incident):
        """Test cycle complet du workflow"""
        incident_id = sample_incident.id
        headers = {"Authorization": f"Bearer {admin_token}"}

        # OPEN -> IN_PROGRESS
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status?new_status=in_progress",
            headers=headers
        )
        assert response.json()["status"] == "in_progress"

        # IN_PROGRESS -> RESOLVED
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status?new_status=resolved",
            headers=headers
        )
        assert response.json()["status"] == "resolved"
        assert response.json()["resolved_at"] is not None

        # RESOLVED -> CLOSED
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status?new_status=closed",
            headers=headers
        )
        assert response.json()["status"] == "closed"
        assert response.json()["closed_at"] is not None

        # CLOSED -> IN_PROGRESS (réouverture exceptionnelle)
        response = client.patch(
            f"/api/v1/incidents/{incident_id}/status?new_status=in_progress",
            headers=headers
        )
        assert response.json()["status"] == "in_progress"
