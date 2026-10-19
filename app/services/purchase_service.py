import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories import purchase_repository


class PurchaseService:
    @staticmethod
    def _visible(user, record):
        if user["role"] == "admin" or user.get("permissions", {}).get("view_purchase_costs", False):
            return record
        hidden = {"outstanding", "invoice_count", "subtotal", "tax", "freight", "total", "paid_amount"}
        return {key: value for key, value in record.items() if key not in hidden}

    @staticmethod
    def list_suppliers(user):
        return [PurchaseService._visible(user, row) for row in purchase_repository.list_suppliers(user["tenant_id"])]

    @staticmethod
    def create_supplier(user, data):
        return purchase_repository.create_supplier(
            user["tenant_id"],
            {key: value.strip() for key, value in data.model_dump().items()},
            datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def list_purchases(user):
        return [PurchaseService._visible(user, row) for row in purchase_repository.list_purchases(user["tenant_id"])]

    @staticmethod
    def create_purchase(user, data):
        try:
            result = purchase_repository.create_purchase(
                user["tenant_id"], user["id"], data.model_dump(), datetime.now(timezone.utc).isoformat()
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="That invoice number is already recorded for this supplier.")
        error = result.get("error")
        if error == "supplier":
            raise HTTPException(status_code=404, detail="Supplier not found.")
        if error == "product":
            raise HTTPException(status_code=404, detail="A product in the invoice was not found.")
        if error == "payment":
            raise HTTPException(status_code=422, detail="Payment cannot exceed the invoice total.")
        if error == "duplicate":
            raise HTTPException(status_code=422, detail="Each product can appear only once on an invoice.")
        return PurchaseService._visible(user, result)
