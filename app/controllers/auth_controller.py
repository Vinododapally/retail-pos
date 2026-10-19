from fastapi import APIRouter, Header

from app.dbconfig.database import get_db
from app.models.schemas import LoginInput, PlatformLoginInput
from app.services.auth_service import AuthService
from app.utils.security import demo_mode_enabled

router = APIRouter()


@router.get("/config")
def auth_config():
    with get_db() as connection:
        available = connection.execute(
            "SELECT 1 FROM tenants WHERE is_demo = 1 AND status = 'active' LIMIT 1"
        ).fetchone()
    accounts = [
        {"label": "Shop admin", "email": "demo.admin@openkarts.in", "password": "DemoShop123!"},
        {"label": "Staff", "email": "demo.staff@openkarts.in", "password": "DemoStaff123!"},
    ] if available else []
    return {"demo_mode": demo_mode_enabled(), "demo_accounts": accounts}


@router.post("/register")
def register():
    return AuthService.register()


@router.post("/login")
def login(data: LoginInput):
    return AuthService.login(data)


@router.post("/platform/login")
def platform_login(data: PlatformLoginInput):
    return AuthService.platform_login(data)


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    user = AuthService.current_user(authorization)
    if user.get("platform_owner"):
        return user
    return AuthService.get_current_user(user)
