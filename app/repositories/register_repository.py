from app.dbconfig.database import get_db


def current_session(tenant_id: int, user_id: int):
    with get_db() as connection:
        row = connection.execute(
            """SELECT * FROM register_sessions WHERE tenant_id = ? AND user_id = ?
               AND status = 'open' ORDER BY id DESC LIMIT 1""",
            (tenant_id, user_id),
        ).fetchone()
        if not row:
            return None
        totals = connection.execute(
            """SELECT s.payment_method, COALESCE(SUM(s.total), 0) AS total
               FROM sales s WHERE s.register_session_id = ? GROUP BY s.payment_method""",
            (row["id"],),
        ).fetchall()
        refunds = connection.execute(
            """SELECT s.payment_method, COALESCE(SUM(sr.refund_total), 0) AS total
               FROM sale_returns sr JOIN sales s ON s.id = sr.sale_id
               WHERE s.register_session_id = ? GROUP BY s.payment_method""",
            (row["id"],),
        ).fetchall()
    totals_by_method = {item["payment_method"]: item["total"] for item in totals}
    refunds_by_method = {item["payment_method"]: item["total"] for item in refunds}
    cash_sales = totals_by_method.get("cash", 0)
    cash_refunds = refunds_by_method.get("cash", 0)
    return {
        **dict(row),
        "cash_sales": round(cash_sales, 2),
        "card_sales": round(totals_by_method.get("card", 0), 2),
        "upi_sales": round(totals_by_method.get("upi", 0), 2),
        "other_sales": round(totals_by_method.get("other", 0), 2),
        "cash_refunds": round(cash_refunds, 2),
        "expected_cash": round(row["opening_cash"] + cash_sales - cash_refunds, 2),
    }


def open_session(tenant_id: int, user_id: int, opening_cash: float, opened_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            """SELECT id FROM register_sessions WHERE tenant_id = ? AND user_id = ?
               AND status = 'open' LIMIT 1""",
            (tenant_id, user_id),
        ).fetchone()
        if existing:
            return None
        session_id = connection.execute(
            """INSERT INTO register_sessions(tenant_id, user_id, opened_at, opening_cash)
               VALUES (?, ?, ?, ?)""",
            (tenant_id, user_id, opened_at, opening_cash),
        ).lastrowid
        return session_id


def close_session(tenant_id: int, user_id: int, counted_cash: float, closed_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """SELECT * FROM register_sessions WHERE tenant_id = ? AND user_id = ?
               AND status = 'open' ORDER BY id DESC LIMIT 1""",
            (tenant_id, user_id),
        ).fetchone()
        if not row:
            return None
        totals = connection.execute(
            """SELECT s.payment_method, COALESCE(SUM(s.total), 0) AS total
               FROM sales s WHERE s.register_session_id = ? GROUP BY s.payment_method""",
            (row["id"],),
        ).fetchall()
        refunds = connection.execute(
            """SELECT s.payment_method, COALESCE(SUM(sr.refund_total), 0) AS total
               FROM sale_returns sr JOIN sales s ON s.id = sr.sale_id
               WHERE s.register_session_id = ? GROUP BY s.payment_method""",
            (row["id"],),
        ).fetchall()
        sales = {item["payment_method"]: item["total"] for item in totals}
        refunded = {item["payment_method"]: item["total"] for item in refunds}
        expected = round(row["opening_cash"] + sales.get("cash", 0) - refunded.get("cash", 0), 2)
        connection.execute(
            """UPDATE register_sessions SET status = 'closed', closed_at = ?,
               counted_cash = ?, expected_cash = ? WHERE id = ?""",
            (closed_at, counted_cash, expected, row["id"]),
        )
    return {
        "id": row["id"], "status": "closed", "opening_cash": row["opening_cash"],
        "cash_sales": round(sales.get("cash", 0), 2),
        "card_sales": round(sales.get("card", 0), 2),
        "upi_sales": round(sales.get("upi", 0), 2),
        "cash_refunds": round(refunded.get("cash", 0), 2),
        "expected_cash": expected, "counted_cash": round(counted_cash, 2),
        "difference": round(counted_cash - expected, 2),
    }
