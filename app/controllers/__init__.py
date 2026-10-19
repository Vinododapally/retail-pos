from fastapi import APIRouter

from app.controllers.auth_controller import router as auth_router
from app.controllers.dashboard_controller import router as dashboard_router
from app.controllers.product_controller import router as product_router
from app.controllers.purchase_controller import router as purchase_router
from app.controllers.finance_controller import router as finance_router
from app.controllers.sales_controller import router as sales_router
from app.controllers.register_controller import router as register_router
from app.controllers.payment_controller import router as payment_router
from app.controllers.staff_controller import router as staff_router
from app.controllers.platform_controller import router as platform_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard_router, tags=["Dashboard"])
api_router.include_router(product_router, tags=["Inventory"])
api_router.include_router(sales_router, tags=["Sales"])
api_router.include_router(staff_router, tags=["Team"])
api_router.include_router(purchase_router, tags=["Purchases"])
api_router.include_router(finance_router, tags=["Finance"])
api_router.include_router(register_router, tags=["Cash register"])
api_router.include_router(payment_router, tags=["Payments"])
api_router.include_router(platform_router, tags=["Platform management"])
