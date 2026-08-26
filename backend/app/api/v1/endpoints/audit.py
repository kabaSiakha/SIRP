from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_analyst
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse, AuditLogListResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    incident_id: Optional[int] = Query(None, description="Filtrer par incident"),
    user_id: Optional[int] = Query(None, description="Filtrer par utilisateur"),
    action: Optional[str] = Query(None, description="Filtrer par action"),
    entity_type: Optional[str] = Query(None, description="Filtrer par type d'entité"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    page_size: int = Query(50, ge=1, le=100, description="Taille de page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Lister les logs d'audit avec filtres et pagination.

    Actions possibles:
    - create: Création d'un incident
    - update: Modification d'un incident
    - delete: Suppression d'un incident
    - prise_en_charge: Passage de OPEN à IN_PROGRESS
    - resolution: Passage de IN_PROGRESS à RESOLVED
    - remise_attente: Passage de IN_PROGRESS à OPEN
    - fermeture: Passage de RESOLVED à CLOSED
    - reouverture: Passage de RESOLVED/CLOSED à IN_PROGRESS
    - assign: Assignation d'un incident
    """
    query = db.query(AuditLog)

    if incident_id:
        query = query.filter(AuditLog.incident_id == incident_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()

    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/incident/{incident_id}", response_model=AuditLogListResponse)
def get_incident_history(
    incident_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Récupérer l'historique complet d'un incident"""
    query = db.query(AuditLog).filter(AuditLog.incident_id == incident_id)

    total = query.count()

    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/user/{user_id}", response_model=AuditLogListResponse)
def get_user_activity(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Récupérer toutes les actions d'un utilisateur"""
    query = db.query(AuditLog).filter(AuditLog.user_id == user_id)

    total = query.count()

    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return AuditLogListResponse(
        items=logs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats")
def get_audit_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Statistiques des actions d'audit"""
    total = db.query(AuditLog).count()

    # Compter par action
    by_action = {}
    actions = db.query(AuditLog.action).distinct().all()
    for (action,) in actions:
        count = db.query(AuditLog).filter(AuditLog.action == action).count()
        by_action[action] = count

    # Top 5 utilisateurs les plus actifs
    from sqlalchemy import func
    top_users = db.query(
        AuditLog.user_id,
        func.count(AuditLog.id).label("count")
    ).group_by(AuditLog.user_id).order_by(func.count(AuditLog.id).desc()).limit(5).all()

    return {
        "total_logs": total,
        "by_action": by_action,
        "top_users": [{"user_id": u, "actions_count": c} for u, c in top_users]
    }
