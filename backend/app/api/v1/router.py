from fastapi import APIRouter

from app.api.v1.endpoints import auth, incidents, audit

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(incidents.router)
api_router.include_router(audit.router)
