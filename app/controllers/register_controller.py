from fastapi import APIRouter

from app.middleware.auth_middleware import CurrentUser
from app.models.schemas import RegisterCloseInput, RegisterOpenInput
from app.services.register_service import RegisterService

router = APIRouter()


@router.get("/register/current")
def current_register(user: CurrentUser):
    return RegisterService.current(user)


@router.post("/register/open")
def open_register(data: RegisterOpenInput, user: CurrentUser):
    return RegisterService.open(user, data)


@router.post("/register/close")
def close_register(data: RegisterCloseInput, user: CurrentUser):
    return RegisterService.close(user, data)
