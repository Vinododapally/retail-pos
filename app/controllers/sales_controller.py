from fastapi import APIRouter, Depends, Query

from app.middleware.auth_middleware import CurrentUser, require_admin_or_permission
from app.models.schemas import ReturnInput, SaleInput
from app.services.sales_service import SalesService

router = APIRouter()


@router.post("/sales")
def create_sale(data: SaleInput, user: CurrentUser):
    return SalesService.create_sale(user, data)


@router.get("/sales")
def list_sales(user: CurrentUser, limit: int = Query(default=100, ge=1, le=500)):
    return SalesService.list_sales(user, limit)


@router.get("/sales/{sale_id}")
def sale_detail(sale_id: int, user: CurrentUser):
    return SalesService.get_sale(user, sale_id)


@router.post("/sales/{sale_id}/returns")
def return_sale(sale_id: int, data: ReturnInput, user: dict = Depends(require_admin_or_permission("process_returns"))):
    return SalesService.return_sale(user, sale_id, data)
