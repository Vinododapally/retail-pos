from fastapi import APIRouter, Depends

from app.middleware.auth_middleware import require_admin
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard(user: dict = Depends(require_admin)):
    return DashboardService.get_dashboard(user)
