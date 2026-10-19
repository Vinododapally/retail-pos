import os
import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.utils.security import hash_password

ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "retail_pos.db"))


@contextmanager
def get_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 15000")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                business_type TEXT NOT NULL DEFAULT 'general',
                currency TEXT NOT NULL DEFAULT 'INR',
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'suspended')),
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'staff')),
                permissions TEXT NOT NULL DEFAULT '{}',
                is_demo INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(tenant_id, email)
            );
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name TEXT NOT NULL,
                brand TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL,
                sku TEXT NOT NULL,
                size TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT 'each',
                tax_rate REAL NOT NULL DEFAULT 0,
                expiry_date TEXT NOT NULL DEFAULT '',
                price REAL NOT NULL CHECK(price > 0),
                cost REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                reorder_level INTEGER NOT NULL DEFAULT 5,
                created_at TEXT NOT NULL,
                UNIQUE(tenant_id, sku)
            );
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                user_id INTEGER REFERENCES users(id),
                register_session_id INTEGER REFERENCES register_sessions(id),
                subtotal REAL NOT NULL,
                discount REAL NOT NULL,
                total REAL NOT NULL,
                payment_method TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales(id),
                product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                product_name TEXT NOT NULL,
                variant TEXT NOT NULL DEFAULT '',
                sku TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                tax_amount REAL NOT NULL DEFAULT 0,
                line_total REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                name TEXT NOT NULL,
                contact_name TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                address TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
                invoice_number TEXT NOT NULL,
                invoice_date TEXT NOT NULL,
                subtotal REAL NOT NULL,
                tax REAL NOT NULL,
                freight REAL NOT NULL,
                total REAL NOT NULL,
                paid_amount REAL NOT NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT NOT NULL,
                UNIQUE(tenant_id, supplier_id, invoice_number)
            );
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL REFERENCES purchases(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                tax_rate REAL NOT NULL,
                line_total REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                expense_date TEXT NOT NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
                user_id INTEGER REFERENCES users(id),
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                reference TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inventory_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                batch_number TEXT NOT NULL DEFAULT '',
                received_at TEXT NOT NULL,
                expiry_date TEXT NOT NULL DEFAULT '',
                quantity_received INTEGER NOT NULL,
                quantity_remaining INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                UNIQUE(tenant_id, product_id, batch_number, received_at)
            );
            CREATE TABLE IF NOT EXISTS sale_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                sale_id INTEGER NOT NULL REFERENCES sales(id),
                user_id INTEGER REFERENCES users(id),
                refund_total REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sale_return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL REFERENCES sale_returns(id),
                sale_item_id INTEGER NOT NULL REFERENCES sale_items(id),
                quantity INTEGER NOT NULL,
                refund_amount REAL NOT NULL,
                cost_reversed REAL NOT NULL DEFAULT 0,
                restocked INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS register_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                opened_at TEXT NOT NULL,
                closed_at TEXT NOT NULL DEFAULT '',
                opening_cash REAL NOT NULL,
                counted_cash REAL,
                expected_cash REAL,
                status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open', 'closed'))
            );
            CREATE TABLE IF NOT EXISTS payment_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                register_session_id INTEGER NOT NULL REFERENCES register_sessions(id),
                razorpay_order_id TEXT NOT NULL UNIQUE,
                razorpay_payment_id TEXT NOT NULL DEFAULT '',
                checkout_signature TEXT NOT NULL DEFAULT '',
                amount_minor INTEGER NOT NULL,
                currency TEXT NOT NULL,
                sale_payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created'
                    CHECK(status IN ('created', 'processing', 'paid', 'needs_refund')),
                sale_id INTEGER REFERENCES sales(id),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_sales_tenant_date ON sales(tenant_id, created_at);
            """
        )
        product_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(products)").fetchall()
        }
        if "size" not in product_columns:
            connection.execute("ALTER TABLE products ADD COLUMN size TEXT NOT NULL DEFAULT ''")
        if "brand" not in product_columns:
            connection.execute("ALTER TABLE products ADD COLUMN brand TEXT NOT NULL DEFAULT ''")
        if "color" not in product_columns:
            connection.execute("ALTER TABLE products ADD COLUMN color TEXT NOT NULL DEFAULT ''")
        for column, declaration in (
            ("unit", "TEXT NOT NULL DEFAULT 'each'"),
            ("tax_rate", "REAL NOT NULL DEFAULT 0"),
            ("expiry_date", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in product_columns:
                connection.execute(f"ALTER TABLE products ADD COLUMN {column} {declaration}")
        sale_columns = {row["name"] for row in connection.execute("PRAGMA table_info(sales)").fetchall()}
        if "tax" not in sale_columns:
            connection.execute("ALTER TABLE sales ADD COLUMN tax REAL NOT NULL DEFAULT 0")
        if "register_session_id" not in sale_columns:
            connection.execute("ALTER TABLE sales ADD COLUMN register_session_id INTEGER REFERENCES register_sessions(id)")
        sale_item_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(sale_items)").fetchall()
        }
        if "unit_cost" not in sale_item_columns:
            connection.execute("ALTER TABLE sale_items ADD COLUMN unit_cost REAL NOT NULL DEFAULT 0")
        if "tax_amount" not in sale_item_columns:
            connection.execute("ALTER TABLE sale_items ADD COLUMN tax_amount REAL NOT NULL DEFAULT 0")
        if "variant" not in sale_item_columns:
            connection.execute("ALTER TABLE sale_items ADD COLUMN variant TEXT NOT NULL DEFAULT ''")
        user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "permissions" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN permissions TEXT NOT NULL DEFAULT '{}'")
        return_columns = {row["name"] for row in connection.execute("PRAGMA table_info(sale_return_items)").fetchall()}
        if "cost_reversed" not in return_columns:
            connection.execute("ALTER TABLE sale_return_items ADD COLUMN cost_reversed REAL NOT NULL DEFAULT 0")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_global_email ON users(email COLLATE NOCASE)")
        tenant_columns = {row["name"] for row in connection.execute("PRAGMA table_info(tenants)").fetchall()}
        if "business_type" not in tenant_columns:
            connection.execute("ALTER TABLE tenants ADD COLUMN business_type TEXT NOT NULL DEFAULT 'general'")
        if "currency" not in tenant_columns:
            connection.execute("ALTER TABLE tenants ADD COLUMN currency TEXT NOT NULL DEFAULT 'INR'")
        if "status" not in tenant_columns:
            connection.execute("ALTER TABLE tenants ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
        if "is_demo" not in tenant_columns:
            connection.execute("ALTER TABLE tenants ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
        user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)").fetchall()}
        if "is_demo" not in user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN is_demo INTEGER NOT NULL DEFAULT 0")
        now = datetime.now(timezone.utc).isoformat()
        if not connection.execute("SELECT 1 FROM tenants LIMIT 1").fetchone() and os.getenv(
            "DEMO_MODE", "true"
        ).strip().lower() in {"1", "true", "yes"}:
            _seed_local_workspace(connection, now)
        _ensure_public_demo_workspace(connection, now)


def _sample_products():
    return [
        ("Organic whole milk", "Dairy", "8901030874561", 4.99, 2.50, 24, 8),
        ("Sourdough loaf", "Bakery", "8901030874562", 6.50, 3.00, 14, 5),
        ("Avocado — single", "Produce", "8901030874563", 2.25, 0.90, 32, 10),
        ("Cold brew coffee", "Drinks", "8901030874564", 5.75, 2.20, 18, 6),
        ("Sea salt crackers", "Pantry", "8901030874565", 3.49, 1.40, 7, 8),
        ("Oat milk", "Dairy", "8901030874566", 4.25, 1.90, 19, 6),
        ("Dark chocolate bar", "Snacks", "8901030874567", 3.25, 1.10, 41, 12),
        ("Fresh orange juice", "Drinks", "8901030874568", 7.99, 3.75, 11, 5),
    ]


def _seed_local_workspace(connection, now: str):
    tenant_id = connection.execute(
        "INSERT INTO tenants(name, created_at) VALUES (?, ?)", ("Acme Market", now)
    ).lastrowid
    connection.executemany(
        """INSERT INTO users(tenant_id, name, email, password_hash, role, permissions, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            (tenant_id, "Alex Morgan", "admin@demo.com", hash_password("admin123"), "admin", "{}", now),
            (tenant_id, "Sam Rivera", "staff@demo.com", hash_password("staff123"), "staff", "{}", now),
        ],
    )
    _insert_sample_products(connection, tenant_id, now)


def _ensure_public_demo_workspace(connection, now: str):
    if connection.execute("SELECT 1 FROM tenants WHERE is_demo = 1 LIMIT 1").fetchone():
        return
    tenant_id = connection.execute(
        """INSERT INTO tenants(name, business_type, currency, status, is_demo, created_at)
           VALUES (?, 'supermarket', 'INR', 'active', 1, ?)""",
        ("OpenKarts Demo Shop", now),
    ).lastrowid
    connection.executemany(
        """INSERT INTO users(tenant_id, name, email, password_hash, role, permissions, is_demo, created_at)
           VALUES (?, ?, ?, ?, ?, '{}', 1, ?)""",
        [
            (tenant_id, "Demo Shop Admin", "demo.admin@openkarts.in", hash_password("DemoShop123!"), "admin", now),
            (tenant_id, "Demo Cashier", "demo.staff@openkarts.in", hash_password("DemoStaff123!"), "staff", now),
        ],
    )
    _insert_sample_products(connection, tenant_id, now)


def _insert_sample_products(connection, tenant_id: int, now: str):
    connection.executemany(
        """INSERT INTO products(tenant_id, name, category, sku, price, cost, stock, reorder_level, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(tenant_id, *product, now) for product in _sample_products()],
    )
