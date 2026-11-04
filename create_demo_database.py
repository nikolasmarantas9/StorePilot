
import sqlite3
from datetime import datetime, timedelta

# Δημιουργούμε ξεχωριστή βάση επίδειξης.
DEMO_DATABASE = "storepilot_demo.db"

# Οι κατηγορίες του StorePilot.
categories = [
    "Περιφερειακά",
    "Υπολογιστές",
    "Οθόνες",
    "Αποθήκευση",
    "Καλώδια"
]

# Ενδεικτικά προϊόντα για την επίδειξη.
products = [
    ("Logitech MX Master 3S", "PR001", 109.90, 12, "Περιφερειακά"),
    ("Mechanical Keyboard RGB", "PR002", 79.90, 4, "Περιφερειακά"),
    ("Wireless Headphones", "PR003", 59.90, 18, "Περιφερειακά"),
    ("Gaming Mouse", "PR004", 39.90, 3, "Περιφερειακά"),

    ("Lenovo ThinkPad E14", "PC001", 899.00, 7, "Υπολογιστές"),
    ("HP Pavilion 15", "PC002", 749.00, 2, "Υπολογιστές"),
    ("Dell OptiPlex Desktop", "PC003", 649.00, 9, "Υπολογιστές"),

    ("Samsung 27 Monitor", "MN001", 229.90, 11, "Οθόνες"),
    ("LG UltraWide 29", "MN002", 299.90, 5, "Οθόνες"),
    ("ASUS Gaming Monitor", "MN003", 349.90, 2, "Οθόνες"),

    ("Samsung SSD 1TB", "ST001", 89.90, 25, "Αποθήκευση"),
    ("Kingston USB 128GB", "ST002", 19.90, 30, "Αποθήκευση"),
    ("Seagate HDD 2TB", "ST003", 74.90, 6, "Αποθήκευση"),

    ("USB-C Cable 2m", "CB001", 9.90, 40, "Καλώδια"),
    ("HDMI Cable 4K", "CB002", 12.90, 22, "Καλώδια")
]

# Δημιουργούμε τη σύνδεση με τη νέα βάση.
connection = sqlite3.connect(DEMO_DATABASE)

try:
    cursor = connection.cursor()

    # Δημιουργούμε τους πίνακες.
    cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            sku TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT
                (datetime('now', 'localtime')),
            note TEXT
        )
    """)

    # Εισάγουμε τις κατηγορίες.
    cursor.executemany(
        "INSERT INTO categories (name) VALUES (?)",
        [(category,) for category in categories]
    )

    # Εισάγουμε τα προϊόντα.
    for name, sku, price, quantity, category in products:

        cursor.execute("""
            INSERT INTO products
            (name, sku, price, quantity, category)
            VALUES (?, ?, ?, ?, ?)
        """, (name, sku, price, quantity, category))

        product_id = cursor.lastrowid

        # Αρχικό απόθεμα.
        cursor.execute("""
            INSERT INTO stock_movements
            (product_id, product_name, sku,
             movement_type, quantity, created_at, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id,
            name,
            sku,
            "in",
            quantity,
            (datetime.now() - timedelta(days=20)).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "Demo initial stock"
        ))

        # Δημιουργούμε επιπλέον ενδεικτικές κινήσεις.
        if quantity >= 5:

            outgoing = 2

            cursor.execute("""
                INSERT INTO stock_movements
                (product_id, product_name, sku,
                 movement_type, quantity, created_at, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                name,
                sku,
                "out",
                outgoing,
                (datetime.now() - timedelta(days=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Demo stock movement"
            ))

            cursor.execute("""
                INSERT INTO stock_movements
                (product_id, product_name, sku,
                 movement_type, quantity, created_at, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                name,
                sku,
                "in",
                outgoing,
                (datetime.now() - timedelta(days=2)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "Demo stock replenishment"
            ))

    # Αποθηκεύουμε τα δεδομένα.
    connection.commit()

    print("Η demo βάση δημιουργήθηκε επιτυχώς!")
    print("Προϊόντα:", len(products))
    print("Κατηγορίες:", len(categories))

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
