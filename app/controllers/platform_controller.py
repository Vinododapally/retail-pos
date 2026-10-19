from fastapi import APIRouter, HTTPException

from app.middleware.auth_middleware import PlatformOwner
from app.models.schemas import PlatformStoreInput
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/platform")


@router.get("/stores")
def list_stores(_: PlatformOwner):
    return PlatformService.list_stores()


@router.post("/stores", status_code=201)
def create_store(data: PlatformStoreInput, _: PlatformOwner):
    return PlatformService.create_store(data)


@router.patch("/stores/{store_id}/status")
def update_store_status(store_id: int, status: str, _: PlatformOwner):
    if status not in {"active", "suspended"}:
        raise HTTPException(status_code=422, detail="Status must be active or suspended.")
    return PlatformService.set_store_status(store_id, status)
