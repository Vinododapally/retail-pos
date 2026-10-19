from app.dbconfig.database import get_db


def list_stores():
    with get_db() as connection:
        rows = connection.execute(
            """SELECT t.id, t.name, t.business_type, t.currency, t.status, t.created_at,
               u.name AS owner_name, u.email AS owner_email,
               (SELECT COUNT(*) FROM users staff WHERE staff.tenant_id = t.id) AS user_count,
               (SELECT COUNT(*) FROM products p WHERE p.tenant_id = t.id) AS product_count
               FROM tenants t LEFT JOIN users u ON u.tenant_id = t.id AND u.role = 'admin'
               WHERE t.is_demo = 0
               ORDER BY t.id DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def create_store(data: dict, password_hash: str, created_at: str):
    with get_db() as connection:
        tenant_id = connection.execute(
            """INSERT INTO tenants(name, business_type, currency, status, created_at)
               VALUES (?, ?, ?, 'active', ?)""",
            (data["store_name"], data["business_type"], data["currency"], created_at),
        ).lastrowid
        connection.execute(
            """INSERT INTO users(tenant_id, name, email, password_hash, role, permissions, created_at)
               VALUES (?, ?, ?, ?, 'admin', '{}', ?)""",
            (tenant_id, data["owner_name"], data["owner_email"], password_hash, created_at),
        )
        store = connection.execute(
            """SELECT t.id, t.name, t.business_type, t.currency, t.status, t.created_at,
               u.name AS owner_name, u.email AS owner_email, 1 AS user_count, 0 AS product_count
               FROM tenants t JOIN users u ON u.tenant_id = t.id AND u.role = 'admin'
               WHERE t.id = ?""",
            (tenant_id,),
        ).fetchone()
    return dict(store)


def set_store_status(store_id: int, status: str):
    with get_db() as connection:
        cursor = connection.execute(
            "UPDATE tenants SET status = ? WHERE id = ?",
            (status, store_id),
        )
        if cursor.rowcount == 0:
            return None
        return dict(connection.execute(
            "SELECT id, name, status FROM tenants WHERE id = ?", (store_id,)
        ).fetchone())
