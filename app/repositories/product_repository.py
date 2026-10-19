from app.dbconfig.database import get_db


def _consume_batches(connection, tenant_id: int, product_id: int, quantity: float):
    batches = connection.execute(
        """SELECT id, quantity_remaining FROM inventory_batches WHERE tenant_id = ?
           AND product_id = ? AND quantity_remaining > 0
           ORDER BY CASE WHEN expiry_date = '' THEN 1 ELSE 0 END, expiry_date, id""",
        (tenant_id, product_id),
    ).fetchall()
    remaining = quantity
    for batch in batches:
        used = min(remaining, batch["quantity_remaining"])
        connection.execute(
            "UPDATE inventory_batches SET quantity_remaining = quantity_remaining - ? WHERE id = ?",
            (used, batch["id"]),
        )
        remaining -= used
        if not remaining:
            break


def _add_batch(connection, tenant_id: int, product_id: int, batch_number: str, created_at: str,
               expiry_date: str, quantity: float, unit_cost: float):
    connection.execute(
        """INSERT INTO inventory_batches(tenant_id, product_id, batch_number, received_at,
           expiry_date, quantity_received, quantity_remaining, unit_cost)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (tenant_id, product_id, batch_number, created_at, expiry_date, quantity, quantity, unit_cost),
    )


def list_products(tenant_id: int, search: str, category: str, low_stock: bool):
    conditions = ["tenant_id = ?"]
    values: list = [tenant_id]
    if search.strip():
        needle = f"%{search.strip()}%"
        conditions.append("(name LIKE ? OR brand LIKE ? OR sku LIKE ? OR category LIKE ?)")
        values.extend((needle, needle, needle, needle))
    if category and category != "All":
        conditions.append("category = ?")
        values.append(category)
    if low_stock:
        conditions.append("stock <= reorder_level")
    with get_db() as connection:
        rows = connection.execute(
            f"SELECT * FROM products WHERE {' AND '.join(conditions)} ORDER BY name COLLATE NOCASE",
            values,
        ).fetchall()
    return [dict(row) for row in rows]


def list_categories(tenant_id: int):
    with get_db() as connection:
        rows = connection.execute(
            "SELECT DISTINCT category FROM products WHERE tenant_id = ? ORDER BY category",
            (tenant_id,),
        ).fetchall()
    return [row["category"] for row in rows]


def get_product(tenant_id: int, product_id: int):
    with get_db() as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE tenant_id = ? AND id = ?", (tenant_id, product_id)
        ).fetchone()
    return dict(row) if row else None


def create_product(tenant_id: int, data: dict, created_at: str):
    with get_db() as connection:
        product_id = connection.execute(
            """INSERT INTO products(tenant_id, name, brand, category, sku, size, color, unit, tax_rate,
               expiry_date, price, cost, stock, reorder_level, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (tenant_id, data["name"], data["brand"], data["category"], data["sku"], data["size"], data["color"],
             data["unit"], data["tax_rate"], data["expiry_date"], data["price"], data["cost"],
             data["stock"], data["reorder_level"], created_at),
        ).lastrowid
        if data["stock"]:
            _add_batch(connection, tenant_id, product_id, "OPENING", created_at,
                       data["expiry_date"], data["stock"], data["cost"])
            connection.execute(
                """INSERT INTO stock_movements(tenant_id, product_id, movement_type, quantity,
                   unit_cost, reference, created_at) VALUES (?, ?, 'opening', ?, ?, 'Opening stock', ?)""",
                (tenant_id, product_id, data["stock"], data["cost"], created_at),
            )
        return dict(connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone())


def import_products(tenant_id: int, products: list[dict], created_at: str):
    with get_db() as connection:
        for item in products:
            product_id = connection.execute(
                """INSERT INTO products(tenant_id, name, brand, category, sku, size, color, unit, tax_rate,
                   expiry_date, price, cost, stock, reorder_level, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tenant_id, item["name"], item["brand"], item["category"], item["sku"], item["size"],
                 item["color"], item["unit"], item["tax_rate"], item["expiry_date"], item["price"],
                 item["cost"], item["stock"], item["reorder_level"], created_at),
            ).lastrowid
            if item["stock"]:
                _add_batch(connection, tenant_id, product_id, "IMPORT", created_at,
                           item["expiry_date"], item["stock"], item["cost"])
                connection.execute(
                    """INSERT INTO stock_movements(tenant_id, product_id, movement_type, quantity,
                       unit_cost, reference, created_at) VALUES (?, ?, 'opening', ?, ?, 'Bulk import', ?)""",
                    (tenant_id, product_id, item["stock"], item["cost"], created_at),
                )
    return len(products)


def update_product(tenant_id: int, product_id: int, data: dict, user_id: int, created_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        current = connection.execute(
            "SELECT stock, cost FROM products WHERE id = ? AND tenant_id = ?",
            (product_id, tenant_id),
        ).fetchone()
        if not current:
            return None
        stock_delta = data["stock"] - current["stock"]
        cursor = connection.execute(
            """UPDATE products SET name = ?, brand = ?, category = ?, sku = ?, size = ?, color = ?, unit = ?,
               tax_rate = ?, expiry_date = ?, price = ?, cost = ?, stock = ?, reorder_level = ?
               WHERE id = ? AND tenant_id = ?""",
            (data["name"], data["brand"], data["category"], data["sku"], data["size"], data["color"], data["unit"],
             data["tax_rate"], data["expiry_date"], data["price"], data["cost"], data["stock"],
             data["reorder_level"], product_id, tenant_id),
        )
        if stock_delta > 0:
            _add_batch(connection, tenant_id, product_id, f"EDIT-{created_at}", created_at,
                       data["expiry_date"], stock_delta, data["cost"])
        elif stock_delta < 0:
            _consume_batches(connection, tenant_id, product_id, -stock_delta)
        if stock_delta:
            connection.execute(
                """INSERT INTO stock_movements(tenant_id, product_id, user_id, movement_type,
                   quantity, unit_cost, reference, reason, created_at)
                   VALUES (?, ?, ?, 'adjustment', ?, ?, 'Product edit', 'Inventory edit', ?)""",
                (tenant_id, product_id, user_id, stock_delta, data["cost"], created_at),
            )
        return dict(connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone())


def delete_product(tenant_id: int, product_id: int):
    with get_db() as connection:
        cursor = connection.execute(
            "DELETE FROM products WHERE id = ? AND tenant_id = ?", (product_id, tenant_id)
        )
    return cursor.rowcount > 0


def adjust_stock(tenant_id: int, user_id: int, product_id: int, quantity: int, reason: str, created_at: str):
    with get_db() as connection:
        connection.execute("BEGIN IMMEDIATE")
        product = connection.execute(
            "SELECT stock, cost FROM products WHERE tenant_id = ? AND id = ?",
            (tenant_id, product_id),
        ).fetchone()
        if not product:
            return False
        new_stock = product["stock"] + quantity
        if new_stock < 0:
            return None
        connection.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
        if quantity > 0:
            _add_batch(connection, tenant_id, product_id, f"ADJUST-{created_at}", created_at,
                       "", quantity, product["cost"])
        elif quantity < 0:
            _consume_batches(connection, tenant_id, product_id, -quantity)
        connection.execute(
            """INSERT INTO stock_movements(tenant_id, product_id, user_id, movement_type,
               quantity, unit_cost, reason, created_at) VALUES (?, ?, ?, 'adjustment', ?, ?, ?, ?)""",
            (tenant_id, product_id, user_id, quantity, product["cost"], reason, created_at),
        )
    return True
