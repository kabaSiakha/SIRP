"""
Machine à états pour les incidents SIRP

Transitions valides:
    OPEN → IN_PROGRESS      (Prise en charge)
    IN_PROGRESS → RESOLVED  (Résolution)
    IN_PROGRESS → OPEN      (Remise en attente)
    RESOLVED → CLOSED       (Fermeture définitive)
    RESOLVED → IN_PROGRESS  (Réouverture)
    CLOSED → IN_PROGRESS    (Réouverture exceptionnelle - admin only)

Diagramme:
    ┌──────────┐
    │   OPEN   │
    └────┬─────┘
         │ prise en charge
         ▼
    ┌──────────────┐
    │ IN_PROGRESS  │◄─────────────┐
    └────┬─────────┘              │
         │ résolution        réouverture
         ▼                        │
    ┌──────────┐                  │
    │ RESOLVED ├──────────────────┘
    └────┬─────┘
         │ fermeture
         ▼
    ┌──────────┐
    │  CLOSED  │
    └──────────┘
"""

from fastapi import HTTPException, status
from app.models.incident import IncidentStatus
from app.models.user import UserRole


TRANSITIONS = {
    IncidentStatus.OPEN: {
        IncidentStatus.IN_PROGRESS: {
            "action": "prise_en_charge",
            "label": "Prise en charge",
            "roles": [UserRole.ADMIN, UserRole.ANALYST],
        },
    },
    IncidentStatus.IN_PROGRESS: {
        IncidentStatus.RESOLVED: {
            "action": "resolution",
            "label": "Marquer comme résolu",
            "roles": [UserRole.ADMIN, UserRole.ANALYST],
        },
        IncidentStatus.OPEN: {
            "action": "remise_attente",
            "label": "Remettre en attente",
            "roles": [UserRole.ADMIN, UserRole.ANALYST],
        },
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.CLOSED: {
            "action": "fermeture",
            "label": "Fermer définitivement",
            "roles": [UserRole.ADMIN, UserRole.ANALYST],
        },
        IncidentStatus.IN_PROGRESS: {
            "action": "reouverture",
            "label": "Réouvrir l'incident",
            "roles": [UserRole.ADMIN, UserRole.ANALYST],
        },
    },
    IncidentStatus.CLOSED: {
        IncidentStatus.IN_PROGRESS: {
            "action": "reouverture_exceptionnelle",
            "label": "Réouverture exceptionnelle",
            "roles": [UserRole.ADMIN],  # Admin uniquement
        },
    },
}


def get_allowed_transitions(current_status: IncidentStatus, user_role: UserRole) -> list[dict]:
    """Retourne les transitions possibles pour un statut et un rôle donnés"""
    transitions = TRANSITIONS.get(current_status, {})
    allowed = []

    for next_status, config in transitions.items():
        if user_role in config["roles"]:
            allowed.append({
                "to_status": next_status.value,
                "action": config["action"],
                "label": config["label"],
            })

    return allowed


def validate_transition(
    current_status: IncidentStatus,
    new_status: IncidentStatus,
    user_role: UserRole
) -> dict:
    """
    Valide une transition d'état.
    Retourne les infos de transition si valide, sinon lève une exception.
    """
    if current_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"L'incident est déjà en statut '{current_status.value}'"
        )

    transitions = TRANSITIONS.get(current_status, {})

    if new_status not in transitions:
        allowed = [s.value for s in transitions.keys()]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition invalide: {current_status.value} → {new_status.value}. "
                   f"Transitions possibles depuis '{current_status.value}': {allowed}"
        )

    config = transitions[new_status]

    if user_role not in config["roles"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Vous n'avez pas les droits pour effectuer cette transition "
                   f"({config['label']}). Rôles autorisés: {[r.value for r in config['roles']]}"
        )

    return config


def get_workflow_diagram() -> dict:
    """Retourne le diagramme du workflow sous forme de dictionnaire"""
    diagram = {}

    for from_status, transitions in TRANSITIONS.items():
        diagram[from_status.value] = {
            "transitions": [
                {
                    "to": to_status.value,
                    "action": config["action"],
                    "label": config["label"],
                    "roles": [r.value for r in config["roles"]],
                }
                for to_status, config in transitions.items()
            ]
        }

    return diagram
