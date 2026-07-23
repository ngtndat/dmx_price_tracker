import sqlite3
import os
from datetime import datetime
import pytz

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "price_tracker.db")
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def get_vn_now():
    return datetime.now(VN_TZ).isoformat()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT,
        picture TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Products Table (extended with is_active, last_checked_at, lowest_price, highest_price)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        platform TEXT NOT NULL,
        original_url TEXT NOT NULL,
        title TEXT NOT NULL,
        image_url TEXT,
        current_price INTEGER NOT NULL,
        lowest_price INTEGER,
        highest_price INTEGER,
        is_active INTEGER NOT NULL DEFAULT 1,
        last_checked_at TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # Migrate existing DB: add missing columns if not present
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(products)").fetchall()]
    for col, definition in [
        ("lowest_price", "INTEGER"),
        ("highest_price", "INTEGER"),
        ("is_active", "INTEGER NOT NULL DEFAULT 1"),
        ("last_checked_at", "TEXT"),
    ]:
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {definition}")

    # 3. Price History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        price INTEGER NOT NULL,
        recorded_at TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    );
    """)

    # 4. Affiliate Clicks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS affiliate_clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id TEXT,
        platform TEXT,
        clicked_at TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialized successfully.")

# --- User CRUD ---

def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(user_id, email, name, picture):
    conn = get_db_connection()
    created_at = get_vn_now()
    try:
        conn.execute(
            "INSERT INTO users (id, email, name, picture, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, name, picture, created_at)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.execute(
            "UPDATE users SET name = ?, picture = ? WHERE id = ?",
            (name, picture, user_id)
        )
        conn.commit()
    conn.close()
    return get_user(user_id)

# --- Product CRUD ---

def get_user_products(user_id):
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(p) for p in products]

def get_product(product_id):
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(product) if product else None

def get_all_active_products():
    """Used by scheduler to get all products currently being tracked."""
    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products WHERE is_active = 1"
    ).fetchall()
    conn.close()
    return [dict(p) for p in products]

def add_product(user_id, platform, original_url, title, image_url, current_price):
    conn = get_db_connection()
    created_at = get_vn_now()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO products 
           (user_id, platform, original_url, title, image_url, current_price, lowest_price, highest_price, is_active, last_checked_at, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
        (user_id, platform, original_url, title, image_url, current_price,
         current_price, current_price, created_at, created_at)
    )
    product_id = cursor.lastrowid

    # Add initial price to history
    cursor.execute(
        "INSERT INTO price_history (product_id, price, recorded_at) VALUES (?, ?, ?)",
        (product_id, current_price, created_at)
    )

    conn.commit()
    conn.close()
    return get_product(product_id)

def delete_product(product_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ? AND user_id = ?", (product_id, user_id))
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_deleted > 0

def mark_product_dead(product_id):
    """Mark a product as inactive when its link is dead (404, gone, etc)."""
    conn = get_db_connection()
    now = get_vn_now()
    conn.execute(
        "UPDATE products SET is_active = 0, last_checked_at = ? WHERE id = ?",
        (now, product_id)
    )
    conn.commit()
    conn.close()
    print(f"[DB] Product {product_id} marked as dead/inactive.")

def update_product_price(product_id, new_price):
    """Update the current price and maintain lowest/highest watermarks."""
    conn = get_db_connection()
    now = get_vn_now()
    cursor = conn.cursor()

    # Get existing watermarks
    product = cursor.execute("SELECT lowest_price, highest_price FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        low = product["lowest_price"] or new_price
        high = product["highest_price"] or new_price
        new_low = min(low, new_price)
        new_high = max(high, new_price)
    else:
        new_low = new_price
        new_high = new_price

    cursor.execute(
        """UPDATE products 
           SET current_price = ?, lowest_price = ?, highest_price = ?, last_checked_at = ?, is_active = 1
           WHERE id = ?""",
        (new_price, new_low, new_high, now, product_id)
    )
    cursor.execute(
        "INSERT INTO price_history (product_id, price, recorded_at) VALUES (?, ?, ?)",
        (product_id, new_price, now)
    )
    conn.commit()
    conn.close()

# --- Price History ---

def add_price_history(product_id, price):
    update_product_price(product_id, price)

def get_price_history(product_id):
    conn = get_db_connection()
    history = conn.execute(
        "SELECT * FROM price_history WHERE product_id = ? ORDER BY recorded_at ASC",
        (product_id,)
    ).fetchall()
    conn.close()
    return [dict(h) for h in history]

# --- Affiliate Click Logging ---

def log_affiliate_click(product_id, user_id, platform):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO affiliate_clicks (product_id, user_id, platform, clicked_at) VALUES (?, ?, ?, ?)",
        (product_id, user_id, platform, get_vn_now())
    )
    conn.commit()
    conn.close()

def get_affiliate_click_count():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM affiliate_clicks").fetchone()[0]
    conn.close()
    return count
