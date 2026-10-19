from fastapi import APIRouter, Depends

from app.middleware.auth_middleware import CurrentUser, require_admin
from app.models.schemas import StaffInput, StaffPermissionsInput
from app.services.staff_service import StaffService

router = APIRouter()


@router.get("/staff")
def list_staff(user: dict = Depends(require_admin)):
    return StaffService.list_staff(user)


@router.post("/staff")
def create_staff(data: StaffInput, user: dict = Depends(require_admin)):
    return StaffService.create_staff(user, data)


@router.put("/staff/{staff_id}/permissions")
def update_permissions(staff_id: int, data: StaffPermissionsInput, user: dict = Depends(require_admin)):
    return StaffService.update_permissions(user, staff_id, data)
