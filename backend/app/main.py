from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.api.v1.router import api_router

DESCRIPTION = """
## SIRP - Secure Incident Reporting Platform

Plateforme DevSecOps de gestion et suivi des incidents de cybersécurité.

### Fonctionnalités

* **Authentification** - JWT avec access/refresh tokens, RBAC (3 rôles)
* **Gestion des incidents** - CRUD complet avec filtres et pagination
* **Workflow** - Machine à états (Open → In Progress → Resolved → Closed)
* **Audit Trail** - Traçabilité complète des actions
* **Notifications** - Emails automatiques sur changement de statut

### Rôles utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Admin** | Accès total, suppression, réouverture exceptionnelle |
| **Analyst** | Gestion des incidents, changement de statut |
| **Reporter** | Création d'incidents, vue limitée |

### Authentification

Utilisez l'endpoint `/api/v1/auth/login` pour obtenir un token JWT.
Incluez le token dans le header `Authorization: Bearer <token>`.
"""

TAGS_METADATA = [
    {
        "name": "Authentification",
        "description": "Inscription, connexion, gestion des tokens JWT.",
    },
    {
        "name": "Incidents",
        "description": "Gestion des incidents de sécurité (CRUD, filtres, workflow).",
    },
    {
        "name": "Audit Trail",
        "description": "Journal d'audit et traçabilité des actions.",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=DESCRIPTION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "SIRP Support",
        "email": "support@sirp.com",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get(f"{settings.API_V1_PREFIX}/")
def root():
    return {
        "message": "Bienvenue sur SIRP API",
        "docs": "/docs",
    }
