from fastapi import APIRouter, Depends, File, UploadFile

from app.middleware.auth_middleware import CurrentUser, require_admin_or_permission
from app.models.schemas import ProductInput, StockAdjustmentInput
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/products")
def list_products(
    user: CurrentUser,
    search: str = "",
    category: str = "",
    low_stock: bool = False,
):
    return ProductService.list_products(user, search, category, low_stock)


@router.get("/categories")
def categories(user: CurrentUser):
    return ProductService.list_categories(user)


@router.post("/products")
def create_product(data: ProductInput, user: dict = Depends(require_admin_or_permission("manage_inventory"))):
    return ProductService.create_product(user, data)


@router.post("/products/import")
async def import_products(file: UploadFile = File(...), user: dict = Depends(require_admin_or_permission("manage_inventory"))):
    contents = await file.read()
    return ProductService.import_products(user, file.filename or "", contents)


@router.post("/inventory/adjustments")
def adjust_stock(data: StockAdjustmentInput, user: dict = Depends(require_admin_or_permission("manage_inventory"))):
    return ProductService.adjust_stock(user, data)


@router.put("/products/{product_id}")
def update_product(product_id: int, data: ProductInput, user: dict = Depends(require_admin_or_permission("manage_inventory"))):
    return ProductService.update_product(user, product_id, data)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, user: dict = Depends(require_admin_or_permission("manage_inventory"))):
    return ProductService.delete_product(user, product_id)
