from fastapi import APIRouter, Depends

from app.middleware.auth_middleware import require_admin_or_permission
from app.models.schemas import PurchaseInput, SupplierInput
from app.services.purchase_service import PurchaseService

router = APIRouter()


@router.get("/suppliers")
def list_suppliers(user: dict = Depends(require_admin_or_permission("receive_stock"))):
    return PurchaseService.list_suppliers(user)


@router.post("/suppliers")
def create_supplier(data: SupplierInput, user: dict = Depends(require_admin_or_permission("receive_stock"))):
    return PurchaseService.create_supplier(user, data)


@router.get("/purchases")
def list_purchases(user: dict = Depends(require_admin_or_permission("receive_stock"))):
    return PurchaseService.list_purchases(user)


@router.post("/purchases")
def create_purchase(data: PurchaseInput, user: dict = Depends(require_admin_or_permission("receive_stock"))):
    return PurchaseService.create_purchase(user, data)
