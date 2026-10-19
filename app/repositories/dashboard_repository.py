from app.dbconfig.database import get_db


def get_dashboard_data(tenant_id: int):
    with get_db() as connection:
        today = connection.execute(
            """SELECT COALESCE(SUM(total), 0) AS revenue, COUNT(*) AS orders FROM sales
               WHERE tenant_id = ? AND date(created_at) = date('now', 'localtime')""",
            (tenant_id,),
        ).fetchone()
        week_revenue = connection.execute(
            """SELECT COALESCE(SUM(total), 0) FROM sales
               WHERE tenant_id = ? AND created_at >= datetime('now', '-7 days')""",
            (tenant_id,),
        ).fetchone()[0]
        low_stock = connection.execute(
            "SELECT COUNT(*) FROM products WHERE tenant_id = ? AND stock <= reorder_level",
            (tenant_id,),
        ).fetchone()[0]
        product_count = connection.execute(
            "SELECT COUNT(*) FROM products WHERE tenant_id = ?", (tenant_id,)
        ).fetchone()[0]
        chart_rows = connection.execute(
            """SELECT date(created_at, 'localtime') AS day, COALESCE(SUM(total), 0) AS revenue
               FROM sales WHERE tenant_id = ? AND created_at >= datetime('now', '-6 days')
               GROUP BY date(created_at, 'localtime') ORDER BY day""",
            (tenant_id,),
        ).fetchall()
        recent_sales = connection.execute(
            """SELECT s.id, s.total, s.discount, s.created_at, s.payment_method, u.name AS cashier,
                      COUNT(si.id) AS item_count
               FROM sales s LEFT JOIN users u ON u.id = s.user_id
               LEFT JOIN sale_items si ON si.sale_id = s.id
               WHERE s.tenant_id = ? GROUP BY s.id ORDER BY s.id DESC LIMIT 5""",
            (tenant_id,),
        ).fetchall()
    return {
        "today": dict(today),
        "week_revenue": week_revenue,
        "low_stock": low_stock,
        "product_count": product_count,
        "chart_rows": [dict(row) for row in chart_rows],
        "recent_sales": [dict(row) for row in recent_sales],
    }
