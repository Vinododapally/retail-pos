from app.dbconfig.database import get_db


def create_expense(tenant_id: int, user_id: int, data: dict, created_at: str):
    with get_db() as connection:
        expense_id = connection.execute(
            """INSERT INTO expenses(tenant_id, category, description, amount, expense_date, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, data["category"], data["description"], data["amount"],
             data["expense_date"], user_id, created_at),
        ).lastrowid
        return dict(connection.execute(
            "SELECT * FROM expenses WHERE id = ?", (expense_id,)
        ).fetchone())


def list_expenses(tenant_id: int):
    with get_db() as connection:
        rows = connection.execute(
            "SELECT * FROM expenses WHERE tenant_id = ? ORDER BY expense_date DESC, id DESC LIMIT 500",
            (tenant_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_financial_report(tenant_id: int, start_date: str | None = None, end_date: str | None = None):
    def date_range(column: str):
        clauses = []
        values = []
        if start_date:
            clauses.append(f"date({column}, 'localtime') >= date(?)")
            values.append(start_date)
        if end_date:
            clauses.append(f"date({column}, 'localtime') <= date(?)")
            values.append(end_date)
        return (" AND " + " AND ".join(clauses) if clauses else ""), values

    sales_range, sales_dates = date_range("s.created_at")
    returns_range, returns_dates = date_range("sr.created_at")
    expense_range, expense_dates = date_range("expense_date")
    purchase_range, purchase_dates = date_range("invoice_date")
    with get_db() as connection:
        sales = connection.execute(
            """SELECT strftime('%Y-%m', s.created_at) AS month, SUM(s.subtotal) AS gross_sales,
               SUM(s.discount) AS discounts, SUM(s.tax) AS tax_collected,
               SUM(s.subtotal - s.discount) AS net_sales, SUM(s.total) AS receipts
               FROM sales s WHERE s.tenant_id = ?""" + sales_range + " GROUP BY month ORDER BY month DESC",
            (tenant_id, *sales_dates),
        ).fetchall()
        cogs = connection.execute(
            """SELECT strftime('%Y-%m', s.created_at) AS month,
               SUM(si.quantity * si.unit_cost) AS cost_of_goods
               FROM sales s JOIN sale_items si ON si.sale_id = s.id
               WHERE s.tenant_id = ?""" + sales_range + " GROUP BY month ORDER BY month DESC",
            (tenant_id, *sales_dates),
        ).fetchall()
        returns = connection.execute(
            """SELECT strftime('%Y-%m', sr.created_at) AS month, SUM(sr.refund_total) AS refunds,
               SUM(sri.cost_reversed) AS cost_reversed
               FROM sale_returns sr JOIN sale_return_items sri ON sri.return_id = sr.id
               WHERE sr.tenant_id = ?""" + returns_range + " GROUP BY month ORDER BY month DESC",
            (tenant_id, *returns_dates),
        ).fetchall()
        expenses = connection.execute(
            """SELECT strftime('%Y-%m', expense_date) AS month, SUM(amount) AS total
               FROM expenses WHERE tenant_id = ?""" + expense_range + " GROUP BY month ORDER BY month DESC",
            (tenant_id, *expense_dates),
        ).fetchall()
        purchases = connection.execute(
            """SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total) AS total
               FROM purchases WHERE tenant_id = ?""" + purchase_range + " GROUP BY month ORDER BY month DESC",
            (tenant_id, *purchase_dates),
        ).fetchall()
        yearly = connection.execute(
            """SELECT strftime('%Y', created_at) AS year, SUM(subtotal - discount) AS net_sales,
               SUM(tax) AS tax_collected, SUM(total) AS receipts
               FROM sales s WHERE tenant_id = ?""" + sales_range + " GROUP BY year ORDER BY year DESC",
            (tenant_id, *sales_dates),
        ).fetchall()
        daily = connection.execute(
            """SELECT date(created_at, 'localtime') AS day, SUM(subtotal - discount) AS net_sales,
               SUM(total) AS receipts, COUNT(*) AS orders
               FROM sales s WHERE tenant_id = ?""" + sales_range + " GROUP BY day ORDER BY day DESC",
            (tenant_id, *sales_dates),
        ).fetchall()
        payments = connection.execute(
            """SELECT payment_method, COUNT(*) AS orders, SUM(total) AS total
               FROM sales s WHERE tenant_id = ?""" + sales_range + " GROUP BY payment_method ORDER BY total DESC",
            (tenant_id, *sales_dates),
        ).fetchall()
        best_sellers = connection.execute(
            """SELECT si.product_name, si.sku, SUM(si.quantity) AS units_sold,
               SUM(si.line_total) AS revenue
               FROM sales s JOIN sale_items si ON si.sale_id = s.id
               WHERE s.tenant_id = ?""" + sales_range + """
               GROUP BY si.product_id, si.product_name, si.sku
               ORDER BY units_sold DESC LIMIT 100""",
            (tenant_id, *sales_dates),
        ).fetchall()
        slow_movers = connection.execute(
            """SELECT p.name, p.sku, p.stock, p.unit,
               COALESCE(SUM(CASE WHEN s.created_at >= datetime('now', '-90 days')
                                 THEN si.quantity ELSE 0 END), 0) AS units_sold_90d
               FROM products p LEFT JOIN sale_items si ON si.product_id = p.id
               LEFT JOIN sales s ON s.id = si.sale_id AND s.tenant_id = p.tenant_id
               WHERE p.tenant_id = ? AND p.stock > 0
               GROUP BY p.id ORDER BY units_sold_90d ASC, p.stock DESC LIMIT 10""",
            (tenant_id,),
        ).fetchall()
        inventory_health = connection.execute(
            """SELECT p.id, p.name, p.sku, p.stock, p.unit, p.cost, p.expiry_date,
               p.reorder_level, COALESCE((SELECT MIN(sm.created_at) FROM stock_movements sm
                 WHERE sm.tenant_id = p.tenant_id AND sm.product_id = p.id
                 AND sm.movement_type IN ('purchase', 'adjustment')), p.created_at) AS oldest_stock_at
               FROM products p WHERE p.tenant_id = ? ORDER BY p.stock <= p.reorder_level DESC,
               oldest_stock_at ASC LIMIT 100""",
            (tenant_id,),
        ).fetchall()
        expiring_batches = connection.execute(
            """SELECT b.product_id, p.name, p.sku, b.batch_number, b.expiry_date,
               b.quantity_remaining, b.unit_cost FROM inventory_batches b
               JOIN products p ON p.id = b.product_id WHERE b.tenant_id = ?
               AND b.quantity_remaining > 0 AND b.expiry_date != ''
               AND b.expiry_date <= date('now', '+90 days')
               ORDER BY b.expiry_date LIMIT 100""",
            (tenant_id,),
        ).fetchall()
        inventory = connection.execute(
            "SELECT COALESCE(SUM(stock * cost), 0) FROM products WHERE tenant_id = ?",
            (tenant_id,),
        ).fetchone()[0]
        movement_history = connection.execute(
            """SELECT sm.*, p.name AS product_name, u.name AS staff_name FROM stock_movements sm
               LEFT JOIN products p ON p.id = sm.product_id LEFT JOIN users u ON u.id = sm.user_id
               WHERE sm.tenant_id = ? ORDER BY sm.id DESC LIMIT 100""",
            (tenant_id,),
        ).fetchall()
    return {
        "sales": [dict(row) for row in sales],
        "cost_of_goods": [dict(row) for row in cogs],
        "returns": [dict(row) for row in returns],
        "expenses": [dict(row) for row in expenses],
        "purchases": [dict(row) for row in purchases],
        "yearly": [dict(row) for row in yearly],
        "daily": [dict(row) for row in daily],
        "payments": [dict(row) for row in payments],
        "best_sellers": [dict(row) for row in best_sellers],
        "slow_movers": [dict(row) for row in slow_movers],
        "inventory_health": [dict(row) for row in inventory_health],
        "expiring_batches": [dict(row) for row in expiring_batches],
        "inventory_value": round(inventory, 2),
        "stock_movements": [dict(row) for row in movement_history],
    }
