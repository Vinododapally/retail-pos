from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories import sales_repository


class SalesService:
    @staticmethod
    def create_sale(user, data, payment_method: str | None = None, register_session_id: int | None = None):
        if user["role"] != "admin" and data.discount > 0 and not user.get("permissions", {}).get("apply_discounts", False):
            raise HTTPException(status_code=403, detail="Your account doesn't have permission to apply discounts.")
        result = sales_repository.create_sale(
            user["tenant_id"],
            user["id"],
            [item.model_dump() for item in data.items],
            data.discount,
            payment_method or data.payment_method,
            datetime.now(timezone.utc).isoformat(),
            register_session_id,
        )
        if result.get("error") == "not_found":
            raise HTTPException(status_code=404, detail="A product in this sale could not be found.")
        if result.get("error") == "register":
            raise HTTPException(status_code=409, detail="Open your register before starting a sale.")
        if result.get("error") == "stock":
            raise HTTPException(
                status_code=409,
                detail=f"Not enough stock for {result['product']} ({result['available']} available).",
            )
        if result.get("error") == "discount":
            raise HTTPException(status_code=422, detail="Discount cannot exceed the subtotal.")
        return result

    @staticmethod
    def list_sales(user, limit: int):
        cashier_id = user["id"] if user["role"] != "admin" else None
        sales = sales_repository.list_sales(user["tenant_id"], limit, cashier_id)
        if user["role"] != "admin" and not user.get("permissions", {}).get("view_purchase_costs", False):
            for sale in sales:
                sale.pop("cost", None)
        return sales

    @staticmethod
    def get_sale(user, sale_id: int):
        cashier_id = user["id"] if user["role"] != "admin" else None
        sale = sales_repository.get_sale(user["tenant_id"], sale_id, cashier_id)
        if not sale:
            raise HTTPException(status_code=404, detail="Sale not found.")
        if user["role"] != "admin" and not user.get("permissions", {}).get("view_purchase_costs", False):
            for item in sale["items"]:
                item.pop("unit_cost", None)
        return sale

    @staticmethod
    def return_sale(user, sale_id: int, data):
        from datetime import datetime, timezone

        result = sales_repository.return_sale(
            user["tenant_id"], user["id"], sale_id,
            [item.model_dump() for item in data.items],
            datetime.now(timezone.utc).isoformat(),
        )
        errors = {
            "sale": (404, "Sale not found."),
            "line": (404, "A sale item could not be found."),
            "quantity": (409, f"Return quantity exceeds the quantity originally sold for {result.get('product')}."),
        }
        if result.get("error") in errors:
            status, detail = errors[result["error"]]
            raise HTTPException(status_code=status, detail=detail)
        return result
