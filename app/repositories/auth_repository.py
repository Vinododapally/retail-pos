from app.dbconfig.database import get_db


def find_by_email(email: str):
    with get_db() as connection:
        return connection.execute(
            """SELECT u.*, t.name AS store_name, t.business_type, t.currency, t.is_demo AS tenant_is_demo
               FROM users u
               JOIN tenants t ON t.id = u.tenant_id WHERE u.email = ? AND t.status = 'active'""",
            (email,),
        ).fetchone()


def find_user(user_id: int, tenant_id: int):
    with get_db() as connection:
        return connection.execute(
            """SELECT u.id, u.tenant_id, u.name, u.email, u.role, u.permissions, u.is_demo,
               t.is_demo AS tenant_is_demo FROM users u
               JOIN tenants t ON t.id = u.tenant_id
               WHERE u.id = ? AND u.tenant_id = ? AND t.status = 'active'""",
            (user_id, tenant_id),
        ).fetchone()


def find_store_name(tenant_id: int):
    with get_db() as connection:
        row = connection.execute("SELECT name, business_type, currency FROM tenants WHERE id = ?", (tenant_id,)).fetchone()
    return dict(row) if row else None
