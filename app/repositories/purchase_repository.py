from app.dbconfig.database import get_db


def list_suppliers(tenant_id: int):
    with get_db() as connection:
        rows = connection.execute(
            """SELECT s.*, COUNT(p.id) AS invoice_count,
                      COALESCE(SUM(p.total - p.paid_amount), 0) AS outstanding
               FROM suppliers s LEFT JOIN purchases p ON p.supplier_id = s.id
               WHERE s.tenant_id = ? GROUP BY s.id ORDER BY s.name COLLATE NOCASE""",
            (tenant_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_supplier(tenant_id: int, data: dict, created_at: str):
    with get_db() as connection:
        supplier_id = connection.execute(
            """INSERT INTO suppliers(tenant_id, name, contact_name, email, phone, address, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, data["name"], data["contact_name"], data["email"], data["phone"],
             data["address"], created_at),
        ).lastrowid
        return dict(connection.execute(
            "SELECT * FROM suppliers WHERE id = ?", (supplier_id,)
        ).fetchone())


def list_purchases(tenant_id: int):
    with get_db() as connection:
        rows = connection.execute(
            """SELECT p.*, s.name AS supplier_name FROM purchases p
               JOIN suppliers s ON s.id = p.supplier_id
               WHERE p.tenant_id = ? ORDER BY p.id DESC LIMIT 250""",
            (tenant_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_purchase(tenant_id: int, user_id: int, data: dict, created_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if len({item["product_id"] for item in data["items"]}) != len(data["items"]):
            return {"error": "duplicate"}
        supplier = connection.execute(
            "SELECT id FROM suppliers WHERE id = ? AND tenant_id = ?",
            (data["supplier_id"], tenant_id),
        ).fetchone()
        if not supplier:
            return {"error": "supplier"}
        products = {}
        for item in data["items"]:
            product = connection.execute(
                "SELECT * FROM products WHERE id = ? AND tenant_id = ?",
                (item["product_id"], tenant_id),
            ).fetchone()
            if not product:
                return {"error": "product"}
            products[item["product_id"]] = product
        subtotal = round(sum(item["quantity"] * item["unit_cost"] for item in data["items"]), 2)
        tax = round(sum(
            item["quantity"] * item["unit_cost"] * item["tax_rate"] / 100 for item in data["items"]
        ), 2)
        total = round(subtotal + tax + data["freight"], 2)
        if data["paid_amount"] > total:
            return {"error": "payment"}
        purchase_id = connection.execute(
            """INSERT INTO purchases(tenant_id, supplier_id, invoice_number, invoice_date, subtotal,
               tax, freight, total, paid_amount, created_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, data["supplier_id"], data["invoice_number"], data["invoice_date"],
             subtotal, tax, data["freight"], total, data["paid_amount"], user_id, created_at),
        ).lastrowid
        total_units = sum(item["quantity"] for item in data["items"])
        freight_per_unit = data["freight"] / total_units if total_units else 0
        for item in data["items"]:
            product = products[item["product_id"]]
            old_stock = product["stock"]
            new_stock = old_stock + item["quantity"]
            landed_unit_cost = item["unit_cost"] + freight_per_unit
            average_cost = round(
                ((old_stock * product["cost"]) + (item["quantity"] * landed_unit_cost)) / new_stock, 4
            ) if new_stock else landed_unit_cost
            line_tax = round(item["quantity"] * item["unit_cost"] * item["tax_rate"] / 100, 2)
            line_total = round(item["quantity"] * item["unit_cost"] + line_tax, 2)
            connection.execute(
                "UPDATE products SET stock = ?, cost = ? WHERE id = ?",
                (new_stock, average_cost, item["product_id"]),
            )
            connection.execute(
                """INSERT INTO purchase_items(purchase_id, product_id, quantity, unit_cost, tax_rate, line_total)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (purchase_id, item["product_id"], item["quantity"], item["unit_cost"], item["tax_rate"], line_total),
            )
            batch_number = item.get("batch_number", "").strip() or data["invoice_number"]
            expiry_date = item.get("expiry_date", "").strip()
            connection.execute(
                """INSERT INTO inventory_batches(tenant_id, product_id, batch_number, received_at,
                   expiry_date, quantity_received, quantity_remaining, unit_cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_id, item["product_id"], batch_number, created_at, expiry_date,
                 item["quantity"], item["quantity"], landed_unit_cost),
            )
            connection.execute(
                """INSERT INTO stock_movements(tenant_id, product_id, user_id, movement_type,
                   quantity, unit_cost, reference, created_at) VALUES (?, ?, ?, 'purchase', ?, ?, ?, ?)""",
                (tenant_id, item["product_id"], user_id, item["quantity"], average_cost,
                 f"Invoice {data['invoice_number']}", created_at),
            )
    return {
        "id": purchase_id, "supplier_id": data["supplier_id"], "invoice_number": data["invoice_number"],
        "invoice_date": data["invoice_date"], "subtotal": subtotal, "tax": tax,
        "freight": data["freight"], "total": total, "paid_amount": data["paid_amount"],
        "outstanding": round(total - data["paid_amount"], 2),
    }
