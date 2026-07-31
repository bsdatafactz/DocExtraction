from fastapi import APIRouter

from app.api.v1 import auth, cost, dashboard, documents, projects, users

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(cost.router)
router.include_router(dashboard.router)
router.include_router(projects.router)
router.include_router(users.router)
router.include_router(documents.project_documents_router)
router.include_router(documents.router)
