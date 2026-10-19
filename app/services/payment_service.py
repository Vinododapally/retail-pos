import logging
import os
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException

from app.dbconfig.database import get_db
from app.repositories import payment_repository, sales_repository
from app.services.sales_service import SalesService
from app.utils.razorpay import PaymentGatewayError

logger = logging.getLogger("counterpoint.payments")
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5173").rstrip("/")


class PaymentService:
    @staticmethod
    def config(user, gateway):
        with get_db() as connection:
            tenant = connection.execute("SELECT currency FROM tenants WHERE id = ?", (user["tenant_id"],)).fetchone()
            store = connection.execute("SELECT name FROM tenants WHERE id = ?", (user["tenant_id"],)).fetchone()
        return {
            "configured": gateway.configured,
            "key_id": gateway.key_id if gateway.configured else "",
            "currency": tenant["currency"] if tenant else "INR",
            "store_name": store["name"] if store else "",
            "callback_url": PUBLIC_URL,
        }

    @staticmethod
    def create_order(user, data, gateway):
        if user["role"] != "admin" and data.discount > 0 and not user.get("permissions", {}).get("apply_discounts", False):
            raise HTTPException(status_code=403, detail="Your account doesn't have permission to apply discounts.")
        quantities = {}
        for item in data.items:
            quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
        with get_db() as connection:
            session = connection.execute(
                """SELECT id FROM register_sessions WHERE tenant_id = ? AND user_id = ?
                   AND status = 'open' ORDER BY id DESC LIMIT 1""",
                (user["tenant_id"], user["id"]),
            ).fetchone()
            tenant = connection.execute("SELECT currency FROM tenants WHERE id = ?", (user["tenant_id"],)).fetchone()
            if not session:
                raise HTTPException(status_code=409, detail="Open your register before starting a sale.")
            products = {}
            for product_id, quantity in quantities.items():
                product = connection.execute(
                    "SELECT * FROM products WHERE id = ? AND tenant_id = ?",
                    (product_id, user["tenant_id"]),
                ).fetchone()
                if not product:
                    raise HTTPException(status_code=404, detail="A product in this sale could not be found.")
                if product["stock"] < quantity:
                    raise HTTPException(status_code=409, detail=f"Not enough stock for {product['name']} ({product['stock']} available).")
                products[product_id] = product
        subtotal = round(sum(products[line.product_id]["price"] * line.quantity for line in data.items), 2)
        if data.discount > subtotal:
            raise HTTPException(status_code=422, detail="Discount cannot exceed the subtotal.")
        tax = round(sum(
            products[line.product_id]["price"] * line.quantity * products[line.product_id]["tax_rate"] / 100
            for line in data.items
        ) * ((subtotal - data.discount) / subtotal), 2) if subtotal else 0
        total = round(subtotal - data.discount + tax, 2)
        currency = tenant["currency"].upper()
        if currency not in {"INR", "USD", "EUR", "GBP", "AUD", "CAD"}:
            raise HTTPException(status_code=422, detail="This store's currency is not supported for Razorpay checkout.")
        amount_minor = round(total * 100)
        if amount_minor < 100:
            raise HTTPException(status_code=422, detail="Razorpay requires a minimum payment of 1.00 in the store currency.")
        sale_payload = {
            "items": [line.model_dump() for line in data.items],
            "discount": data.discount,
            "payment_method": "razorpay",
        }
        receipt = f"cp_{user['tenant_id']}_{secrets.token_hex(8)}"
        try:
            razorpay_order = gateway.create_order(amount_minor, currency, receipt)
        except PaymentGatewayError as exc:
            logger.warning("Razorpay order creation rejected for tenant %s: %s", user["tenant_id"], exc)
            raise HTTPException(status_code=502, detail=str(exc))
        order_id = razorpay_order.get("id")
        if not order_id or razorpay_order.get("amount") != amount_minor or razorpay_order.get("currency") != currency:
            logger.error("Razorpay returned an inconsistent order response for tenant %s", user["tenant_id"])
            raise HTTPException(status_code=502, detail="Razorpay returned an invalid order. No payment was started.")
        now = datetime.now(timezone.utc).isoformat()
        payment_repository.save_order(
            user["tenant_id"], user["id"], session["id"], order_id, amount_minor,
            currency, sale_payload, now,
        )
        return {
            "order_id": order_id,
            "amount": amount_minor,
            "currency": currency,
            "key_id": gateway.key_id,
            "name": user.get("store_name", ""),
            "description": f"POS checkout · {receipt}",
            "callback_url": PUBLIC_URL,
            "subtotal": subtotal,
            "discount": data.discount,
            "tax": tax,
            "total": total,
        }

    @staticmethod
    def verify_checkout(user, data, gateway):
        try:
            valid_signature = gateway.verify_checkout_signature(
                data.razorpay_order_id, data.razorpay_payment_id, data.razorpay_signature
            )
        except PaymentGatewayError as exc:
            raise HTTPException(status_code=503, detail=str(exc))
        if not valid_signature:
            raise HTTPException(status_code=400, detail="Razorpay payment signature is invalid.")
        order = payment_repository.get_order(user["tenant_id"], data.razorpay_order_id)
        if not order or order["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="This payment order does not belong to your account.")
        try:
            payment = gateway.fetch_payment(data.razorpay_payment_id)
        except PaymentGatewayError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        if (payment.get("order_id") != order["razorpay_order_id"]
                or payment.get("amount") != order["amount_minor"]
                or payment.get("currency") != order["currency"]
                or payment.get("status") != "captured"):
            raise HTTPException(status_code=409, detail="Razorpay has not confirmed this payment as captured.")
        return PaymentService._record_captured(user, order, data.razorpay_payment_id, data.razorpay_signature)

    @staticmethod
    def process_webhook(event: dict, gateway):
        payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment_entity.get("order_id")
        payment_id = payment_entity.get("id")
        if event.get("event") != "payment.captured" or not order_id or not payment_id:
            return {"received": True, "processed": False}
        order = payment_repository.get_order_by_id(order_id)
        if not order:
            logger.warning("Captured Razorpay webhook references unknown order %s", order_id)
            return {"received": True, "processed": False}
        if payment_entity.get("amount") != order["amount_minor"] or payment_entity.get("currency") != order["currency"]:
            raise HTTPException(status_code=400, detail="Webhook payment amount does not match the order.")
        user = {
            "id": order["user_id"],
            "tenant_id": order["tenant_id"],
            "role": order["role"],
            "permissions": order["permissions"],
        }
        result = PaymentService._record_captured(user, order, payment_id, "")
        return {"received": True, "processed": True, "sale_id": result["sale"]["id"]}

    @staticmethod
    def _record_captured(user, order, payment_id, signature):
        now = datetime.now(timezone.utc).isoformat()
        claim = payment_repository.claim_order(
            user["tenant_id"], order["razorpay_order_id"], payment_id, signature, now
        )
        if claim["state"] == "paid":
            sale = sales_repository.get_sale(user["tenant_id"], claim["sale_id"])
            return {"sale": sale, "already_processed": True}
        if claim["state"] == "processing":
            raise HTTPException(status_code=409, detail="This payment is already being finalized.")
        if claim["state"] == "needs_refund":
            raise HTTPException(status_code=409, detail="Payment was captured but needs a manual refund. Contact the store administrator.")
        if claim["state"] == "not_found":
            raise HTTPException(status_code=404, detail="Payment order not found.")
        try:
            payload = claim["order"]["sale_payload"]
            payload["payment_method"] = "razorpay"
            sale = SalesService.create_sale(
                user,
                _payload_model(payload),
                payment_method="razorpay",
                register_session_id=claim["order"]["register_session_id"],
            )
        except HTTPException as exc:
            payment_repository.finish_order(
                user["tenant_id"], order["razorpay_order_id"], "needs_refund", None,
                datetime.now(timezone.utc).isoformat(),
            )
            logger.error(
                "Captured Razorpay payment %s could not become a sale; order %s requires refund: %s",
                payment_id, order["razorpay_order_id"], exc.detail,
            )
            raise HTTPException(
                status_code=409,
                detail="Payment was captured but inventory could not be committed. The order is flagged for refund; contact the store administrator.",
            )
        payment_repository.finish_order(
            user["tenant_id"], order["razorpay_order_id"], "paid", sale["id"],
            datetime.now(timezone.utc).isoformat(),
        )
        return {"sale": sale, "already_processed": False}


def _payload_model(payload: dict):
    from app.models.schemas import SaleInput

    payload["payment_method"] = "card"
    return SaleInput.model_validate(payload)
