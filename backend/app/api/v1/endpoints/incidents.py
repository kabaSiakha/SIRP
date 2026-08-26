from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.deps import get_db, get_current_user, require_analyst, require_admin
from app.core.workflow import validate_transition, get_allowed_transitions, get_workflow_diagram
from app.models.user import User, UserRole
from app.models.incident import Incident, IncidentStatus, IncidentSeverity, IncidentCategory
from app.models.audit_log import AuditLog
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentListResponse,
)
from app.services.notification import NotificationService

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    incident_id: int,
    details: str = None,
    ip_address: str = None
):
    """Crée une entrée dans le journal d'audit"""
    audit = AuditLog(
        action=action,
        entity_type="incident",
        entity_id=incident_id,
        details=details,
        user_id=user_id,
        incident_id=incident_id,
        ip_address=ip_address,
    )
    db.add(audit)


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouvel incident"""
    incident = Incident(
        title=incident_data.title,
        description=incident_data.description,
        severity=incident_data.severity,
        category=incident_data.category,
        created_by=current_user.id,
        assigned_to=incident_data.assigned_to,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="create",
        incident_id=incident.id,
        details=f"Incident créé: {incident.title}"
    )
    db.commit()

    return incident


@router.get("/", response_model=IncidentListResponse)
def list_incidents(
    status: Optional[IncidentStatus] = Query(None, description="Filtrer par statut"),
    severity: Optional[IncidentSeverity] = Query(None, description="Filtrer par sévérité"),
    category: Optional[IncidentCategory] = Query(None, description="Filtrer par catégorie"),
    assigned_to_me: bool = Query(False, description="Mes incidents assignés uniquement"),
    created_by_me: bool = Query(False, description="Mes incidents créés uniquement"),
    search: Optional[str] = Query(None, description="Recherche dans titre/description"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(20, ge=1, le=100, description="Taille de page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lister les incidents avec filtres et pagination"""
    query = db.query(Incident)

    # Les reporters ne voient que leurs propres incidents
    if current_user.role == UserRole.REPORTER:
        query = query.filter(
            or_(
                Incident.created_by == current_user.id,
                Incident.assigned_to == current_user.id
            )
        )

    # Filtres
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if category:
        query = query.filter(Incident.category == category)
    if assigned_to_me:
        query = query.filter(Incident.assigned_to == current_user.id)
    if created_by_me:
        query = query.filter(Incident.created_by == current_user.id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Incident.title.ilike(search_filter),
                Incident.description.ilike(search_filter)
            )
        )

    # Comptage total
    total = query.count()

    # Pagination
    offset = (page - 1) * page_size
    incidents = query.order_by(Incident.created_at.desc()).offset(offset).limit(page_size).all()

    return IncidentListResponse(
        items=incidents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer un incident par son ID"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    # Les reporters ne peuvent voir que leurs propres incidents
    if current_user.role == UserRole.REPORTER:
        if incident.created_by != current_user.id and incident.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à cet incident"
            )

    return incident


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Mettre à jour un incident (Admin/Analyst uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    update_data = incident_data.model_dump(exclude_unset=True)
    changes = []

    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(incident, field)
            if old_value != value:
                changes.append(f"{field}: {old_value} → {value}")
                setattr(incident, field, value)

    # Gestion des timestamps de statut
    if incident_data.status:
        if incident_data.status == IncidentStatus.RESOLVED and not incident.resolved_at:
            incident.resolved_at = datetime.utcnow()
        elif incident_data.status == IncidentStatus.CLOSED and not incident.closed_at:
            incident.closed_at = datetime.utcnow()

    incident.updated_at = datetime.utcnow()

    if changes:
        create_audit_log(
            db=db,
            user_id=current_user.id,
            action="update",
            incident_id=incident.id,
            details="; ".join(changes)
        )

    db.commit()
    db.refresh(incident)

    return incident


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Supprimer un incident (Admin uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="delete",
        incident_id=incident.id,
        details=f"Incident supprimé: {incident.title}"
    )

    db.delete(incident)
    db.commit()

    return None


@router.patch("/{incident_id}/status", response_model=IncidentResponse)
def update_incident_status(
    incident_id: int,
    new_status: IncidentStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Changer le statut d'un incident selon le workflow.

    Transitions valides:
    - OPEN → IN_PROGRESS (Prise en charge)
    - IN_PROGRESS → RESOLVED (Résolution)
    - IN_PROGRESS → OPEN (Remise en attente)
    - RESOLVED → CLOSED (Fermeture)
    - RESOLVED → IN_PROGRESS (Réouverture)
    - CLOSED → IN_PROGRESS (Réouverture exceptionnelle - admin only)
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    old_status = incident.status

    # Valider la transition selon le workflow
    transition_config = validate_transition(old_status, new_status, current_user.role)

    incident.status = new_status
    incident.updated_at = datetime.utcnow()

    if new_status == IncidentStatus.RESOLVED:
        incident.resolved_at = datetime.utcnow()
    elif new_status == IncidentStatus.CLOSED:
        incident.closed_at = datetime.utcnow()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action=transition_config["action"],
        incident_id=incident.id,
        details=f"{transition_config['label']}: {old_status.value} → {new_status.value}"
    )

    db.commit()
    db.refresh(incident)

    # Notification email au créateur et à l'assigné
    creator = db.query(User).filter(User.id == incident.created_by).first()
    if creator and creator.id != current_user.id:
        NotificationService.notify_status_change(
            incident_id=incident.id,
            incident_title=incident.title,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=current_user.full_name,
            recipient_email=creator.email,
            recipient_name=creator.full_name
        )

    if incident.assigned_to and incident.assigned_to != current_user.id:
        assignee = db.query(User).filter(User.id == incident.assigned_to).first()
        if assignee:
            NotificationService.notify_status_change(
                incident_id=incident.id,
                incident_title=incident.title,
                old_status=old_status.value,
                new_status=new_status.value,
                changed_by=current_user.full_name,
                recipient_email=assignee.email,
                recipient_name=assignee.full_name
            )

    return incident


@router.get("/{incident_id}/transitions")
def get_incident_transitions(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les transitions possibles pour un incident"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    transitions = get_allowed_transitions(incident.status, current_user.role)

    return {
        "incident_id": incident.id,
        "current_status": incident.status.value,
        "allowed_transitions": transitions
    }


@router.get("/workflow/diagram")
def get_workflow():
    """Récupérer le diagramme du workflow des incidents"""
    return get_workflow_diagram()


@router.patch("/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident(
    incident_id: int,
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Assigner un incident à un utilisateur (Admin/Analyst uniquement)"""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()

    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident non trouvé"
        )

    assignee = None
    if assignee_id:
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur assigné non trouvé"
            )

    old_assignee = incident.assigned_to
    incident.assigned_to = assignee_id
    incident.updated_at = datetime.utcnow()

    create_audit_log(
        db=db,
        user_id=current_user.id,
        action="assign",
        incident_id=incident.id,
        details=f"Assignation: {old_assignee} → {assignee_id}"
    )

    db.commit()
    db.refresh(incident)

    # Notification email à l'utilisateur assigné
    if assignee and assignee.id != current_user.id:
        NotificationService.notify_incident_assigned(
            incident_id=incident.id,
            incident_title=incident.title,
            assigned_by=current_user.full_name,
            recipient_email=assignee.email,
            recipient_name=assignee.full_name
        )

    return incident


@router.get("/stats/summary")
def get_incidents_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Statistiques des incidents (Admin/Analyst uniquement)"""
    total = db.query(Incident).count()

    by_status = {}
    for s in IncidentStatus:
        count = db.query(Incident).filter(Incident.status == s).count()
        by_status[s.value] = count

    by_severity = {}
    for sev in IncidentSeverity:
        count = db.query(Incident).filter(Incident.severity == sev).count()
        by_severity[sev.value] = count

    by_category = {}
    for cat in IncidentCategory:
        count = db.query(Incident).filter(Incident.category == cat).count()
        by_category[cat.value] = count

    return {
        "total": total,
        "by_status": by_status,
        "by_severity": by_severity,
        "by_category": by_category
    }
