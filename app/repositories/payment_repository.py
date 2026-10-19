import json

from app.dbconfig.database import get_db


def save_order(tenant_id: int, user_id: int, session_id: int, order_id: str,
               amount_minor: int, currency: str, payload: dict, created_at: str):
    with get_db() as connection:
        connection.execute(
            """INSERT INTO payment_orders(tenant_id, user_id, register_session_id, razorpay_order_id,
               amount_minor, currency, sale_payload, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, user_id, session_id, order_id, amount_minor, currency,
             json.dumps(payload, separators=(",", ":")), created_at, created_at),
        )


def get_order(tenant_id: int, order_id: str):
    with get_db() as connection:
        row = connection.execute(
            "SELECT * FROM payment_orders WHERE tenant_id = ? AND razorpay_order_id = ?",
            (tenant_id, order_id),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["sale_payload"] = json.loads(result["sale_payload"])
    return result


def get_order_by_id(order_id: str):
    with get_db() as connection:
        row = connection.execute(
            """SELECT po.*, u.role, u.permissions FROM payment_orders po
               JOIN users u ON u.id = po.user_id WHERE po.razorpay_order_id = ?""",
            (order_id,),
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["sale_payload"] = json.loads(result["sale_payload"])
    result["permissions"] = json.loads(result["permissions"] or "{}")
    return result


def claim_order(tenant_id: int, order_id: str, payment_id: str, signature: str, updated_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM payment_orders WHERE tenant_id = ? AND razorpay_order_id = ?",
            (tenant_id, order_id),
        ).fetchone()
        if not row:
            return {"state": "not_found"}
        if row["status"] == "paid":
            return {"state": "paid", "sale_id": row["sale_id"]}
        if row["status"] == "needs_refund":
            return {"state": "needs_refund", "sale_id": row["sale_id"]}
        if row["status"] == "processing":
            return {"state": "processing"}
        connection.execute(
            """UPDATE payment_orders SET status = 'processing', razorpay_payment_id = ?,
               checkout_signature = ?, updated_at = ? WHERE id = ?""",
            (payment_id, signature, updated_at, row["id"]),
        )
        result = dict(row)
        result["sale_payload"] = json.loads(result["sale_payload"])
        return {"state": "claimed", "order": result}


def finish_order(tenant_id: int, order_id: str, status: str, sale_id: int | None, updated_at: str):
    with get_db() as connection:
        connection.execute(
            """UPDATE payment_orders SET status = ?, sale_id = ?, updated_at = ?
               WHERE tenant_id = ? AND razorpay_order_id = ? AND status = 'processing'""",
            (status, sale_id, updated_at, tenant_id, order_id),
        )
