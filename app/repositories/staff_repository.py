import json

from app.dbconfig.database import get_db


def list_staff(tenant_id: int):
    with get_db() as connection:
        rows = connection.execute(
            """SELECT id, name, email, role, permissions, created_at FROM users
               WHERE tenant_id = ? ORDER BY role, name""",
            (tenant_id,),
        ).fetchall()
    result = [dict(row) for row in rows]
    for staff in result:
        staff["permissions"] = json.loads(staff["permissions"] or "{}")
    return result


def create_staff(tenant_id: int, name: str, email: str, password_hash: str, permissions: dict, created_at: str):
    with get_db() as connection:
        user_id = connection.execute(
            """INSERT INTO users(tenant_id, name, email, password_hash, role, permissions, created_at)
               VALUES (?, ?, ?, ?, 'staff', ?, ?)""",
            (tenant_id, name, email, password_hash, json.dumps(permissions), created_at),
        ).lastrowid
        return dict(connection.execute(
            "SELECT id, name, email, role, permissions, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()) | {"permissions": permissions}


def update_permissions(tenant_id: int, user_id: int, permissions: dict):
    with get_db() as connection:
        cursor = connection.execute(
            """UPDATE users SET permissions = ? WHERE id = ? AND tenant_id = ? AND role = 'staff'""",
            (json.dumps(permissions), user_id, tenant_id),
        )
        if not cursor.rowcount:
            return None
        return dict(connection.execute(
            "SELECT id, name, email, role, permissions, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()) | {"permissions": permissions}
