from app.dbconfig.database import get_db


def create_sale(
    tenant_id: int,
    user_id: int,
    item_data: list[dict],
    discount: float,
    payment_method: str,
    created_at: str,
    register_session_id: int | None = None,
):
    quantities: dict[int, float] = {}
    for item in item_data:
        quantities[item["product_id"]] = quantities.get(item["product_id"], 0) + item["quantity"]

    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if register_session_id is not None:
            session = connection.execute(
                """SELECT id FROM register_sessions WHERE tenant_id = ? AND user_id = ?
                   AND id = ? AND status = 'open'""",
                (tenant_id, user_id, register_session_id),
            ).fetchone()
        else:
            session = connection.execute(
                """SELECT id FROM register_sessions WHERE tenant_id = ? AND user_id = ?
                   AND status = 'open' ORDER BY id DESC LIMIT 1""",
                (tenant_id, user_id),
            ).fetchone()
        if not session:
            return {"error": "register"}
        products = {}
        for product_id, quantity in quantities.items():
            product = connection.execute(
                "SELECT * FROM products WHERE id = ? AND tenant_id = ?", (product_id, tenant_id)
            ).fetchone()
            if not product:
                return {"error": "not_found"}
            if product["stock"] < quantity:
                return {"error": "stock", "product": product["name"], "available": product["stock"]}
            products[product_id] = product

        subtotal = round(sum(products[item["product_id"]]["price"] * item["quantity"] for item in item_data), 2)
        if discount > subtotal:
            return {"error": "discount"}
        tax = round(sum(
            products[item["product_id"]]["price"] * item["quantity"]
            * products[item["product_id"]]["tax_rate"] / 100
            for item in item_data
        ) * (subtotal - discount) / subtotal, 2) if subtotal else 0
        total = round(subtotal - discount + tax, 2)
        sale_id = connection.execute(
            """INSERT INTO sales(tenant_id, user_id, register_session_id, subtotal, discount, tax,
               total, payment_method, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, user_id, session["id"], subtotal, discount, tax, total, payment_method, created_at),
        ).lastrowid
        for product_id, quantity in quantities.items():
            connection.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
            remaining_to_sell = quantity
            batches = connection.execute(
                """SELECT id, quantity_remaining FROM inventory_batches WHERE tenant_id = ?
                   AND product_id = ? AND quantity_remaining > 0
                   ORDER BY CASE WHEN expiry_date = '' THEN 1 ELSE 0 END, expiry_date, id""",
                (tenant_id, product_id),
            ).fetchall()
            for batch in batches:
                used = min(remaining_to_sell, batch["quantity_remaining"])
                connection.execute(
                    "UPDATE inventory_batches SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
                    (used, batch["id"]),
                )
                remaining_to_sell -= used
                if not remaining_to_sell:
                    break
        for item in item_data:
            product = products[item["product_id"]]
            line_total = round(product["price"] * item["quantity"], 2)
            line_tax = round(
                line_total * product["tax_rate"] / 100 * (subtotal - discount) / subtotal, 2
            ) if subtotal else 0
            connection.execute(
                """INSERT INTO sale_items(sale_id, product_id, product_name, variant, sku, quantity,
                   unit_price, unit_cost, tax_amount, line_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, item["product_id"], product["name"],
                 "/".join(value for value in (product["size"], product["color"]) if value),
                 product["sku"], item["quantity"],
                 product["price"], product["cost"], line_tax, line_total),
            )
            connection.execute(
                """INSERT INTO stock_movements(tenant_id, product_id, user_id, movement_type, quantity,
                   unit_cost, reference, created_at) VALUES (?, ?, ?, 'sale', ?, ?, ?, ?)""",
                (tenant_id, item["product_id"], user_id, -item["quantity"], product["cost"],
                 f"Sale #{sale_id}", created_at),
            )
        lines = connection.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
    return {
        "id": sale_id, "subtotal": subtotal, "discount": discount, "tax": tax, "total": total,
        "payment_method": payment_method, "created_at": created_at,
        "items": [dict(row) for row in lines],
    }


def list_sales(tenant_id: int, limit: int, user_id: int | None = None):
    user_filter = " AND s.user_id = ?" if user_id is not None else ""
    params = (tenant_id, user_id, limit) if user_id is not None else (tenant_id, limit)
    with get_db() as connection:
        rows = connection.execute(
            f"""SELECT s.*, u.name AS cashier, COUNT(si.id) AS item_count
               FROM sales s LEFT JOIN users u ON u.id = s.user_id
               LEFT JOIN sale_items si ON si.sale_id = s.id
               WHERE s.tenant_id = ?{user_filter} GROUP BY s.id ORDER BY s.id DESC LIMIT ?""",
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def get_sale(tenant_id: int, sale_id: int, user_id: int | None = None):
    user_filter = " AND s.user_id = ?" if user_id is not None else ""
    with get_db() as connection:
        params = (sale_id, tenant_id, user_id) if user_id is not None else (sale_id, tenant_id)
        sale = connection.execute(
            f"""SELECT s.*, u.name AS cashier FROM sales s LEFT JOIN users u ON u.id = s.user_id
               WHERE s.id = ? AND s.tenant_id = ?{user_filter}""",
            params,
        ).fetchone()
        if not sale:
            return None
        items = connection.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
    return {**dict(sale), "items": [dict(row) for row in items]}


def return_sale(tenant_id: int, user_id: int, sale_id: int, items: list[dict], created_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        sale = connection.execute(
            "SELECT * FROM sales WHERE id = ? AND tenant_id = ?", (sale_id, tenant_id)
        ).fetchone()
        if not sale:
            return {"error": "sale"}
        return_lines = []
        refund_total = 0.0
        for item in items:
            line = connection.execute(
                """SELECT si.*, s.subtotal, s.discount FROM sale_items si
                   JOIN sales s ON s.id = si.sale_id WHERE si.id = ? AND si.sale_id = ?""",
                (item["sale_item_id"], sale_id),
            ).fetchone()
            if not line:
                return {"error": "line"}
            returned = connection.execute(
                """SELECT COALESCE(SUM(sri.quantity), 0) FROM sale_return_items sri
                   JOIN sale_returns sr ON sr.id = sri.return_id WHERE sri.sale_item_id = ?""",
                (item["sale_item_id"],),
            ).fetchone()[0]
            if returned + item["quantity"] > line["quantity"]:
                return {"error": "quantity", "product": line["product_name"]}
            unit_refund = (line["unit_price"] * (1 - line["discount"] / line["subtotal"])) if line["subtotal"] else 0
            unit_refund += line["tax_amount"] / line["quantity"]
            refund = round(unit_refund * item["quantity"], 2)
            refund_total += refund
            return_lines.append((line, item, refund))
        refund_total = round(refund_total, 2)
        return_id = connection.execute(
            """INSERT INTO sale_returns(tenant_id, sale_id, user_id, refund_total, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (tenant_id, sale_id, user_id, refund_total, created_at),
        ).lastrowid
        for line, item, refund in return_lines:
            connection.execute(
                """INSERT INTO sale_return_items(return_id, sale_item_id, quantity, refund_amount,
                   cost_reversed, restocked) VALUES (?, ?, ?, ?, ?, ?)""",
                (return_id, line["id"], item["quantity"], refund,
                 round(line["unit_cost"] * item["quantity"], 2) if item["restock"] else 0,
                 int(item["restock"])),
            )
            if item["restock"] and line["product_id"]:
                connection.execute(
                    "UPDATE products SET stock = stock + ? WHERE id = ?",
                    (item["quantity"], line["product_id"]),
                )
                connection.execute(
                    """INSERT INTO stock_movements(tenant_id, product_id, user_id, movement_type,
                       quantity, unit_cost, reference, created_at)
                       VALUES (?, ?, ?, 'return', ?, ?, ?, ?)""",
                    (tenant_id, line["product_id"], user_id, item["quantity"], line["unit_cost"],
                     f"Return #{return_id}", created_at),
                )
                connection.execute(
                    """INSERT INTO inventory_batches(tenant_id, product_id, batch_number, received_at,
                       expiry_date, quantity_received, quantity_remaining, unit_cost)
                       VALUES (?, ?, ?, ?, '', ?, ?, ?)""",
                    (tenant_id, line["product_id"], f"RETURN-{return_id}", created_at,
                     item["quantity"], item["quantity"], line["unit_cost"]),
                )
    return {"id": return_id, "sale_id": sale_id, "refund_total": refund_total}
