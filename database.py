
# Εισάγουμε τη βιβλιοθήκη για τη διαχείριση της SQLite.
import sqlite3
import os
# Βιβλιοθήκες για την αναζήτηση παρόμοιων λέξεων και τη διαχείριση τόνων.
import difflib
import unicodedata

# Ορίζουμε τον βασικό φάκελο του project.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Η βάση μπορεί να αλλάξει μέσω μεταβλητής περιβάλλοντος.
# Αν δοθεί σχετική διαδρομή, υπολογίζεται πάντα από τον φάκελο του project.
_database_setting = os.environ.get("DATABASE_NAME", "storepilot.db")
DATABASE_NAME = (
    _database_setting
    if os.path.isabs(_database_setting)
    else os.path.join(BASE_DIR, _database_setting)
)


def get_connection():
    """Δημιουργεί και επιστρέφει σύνδεση με τη βάση δεδομένων."""

    connection = sqlite3.connect(DATABASE_NAME)

    # Επιτρέπουμε την πρόσβαση στις στήλες με βάση το όνομά τους.
    connection.row_factory = sqlite3.Row

    return connection



def create_tables():
    """Δημιουργεί τους απαραίτητους πίνακες, αν δεν υπάρχουν ήδη."""

    connection = get_connection()

    # Δημιουργούμε τον πίνακα προϊόντων.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL
        )
    """)

    # Δημιουργούμε τον πίνακα κατηγοριών.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Ορίζουμε τις αρχικές κατηγορίες του StorePilot.
    default_categories = [
        "Περιφερειακά",
        "Υπολογιστές",
        "Οθόνες",
        "Αποθήκευση",
        "Καλώδια"
    ]

    # Προσθέτουμε κάθε κατηγορία μόνο αν δεν υπάρχει ήδη.
    for category in default_categories:
        connection.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (category,)
        )

    # Δημιουργούμε τον πίνακα ιστορικού κινήσεων αποθήκης.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            sku TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            note TEXT
        )
    """)

    # Αποθηκεύουμε όλες τις αλλαγές.
    connection.commit()

    # Κλείνουμε τη σύνδεση με τη βάση δεδομένων.
    connection.close()

# ==========================================
# ΙΣΤΟΡΙΚΟ ΚΙΝΗΣΕΩΝ ΑΠΟΘΗΚΗΣ
# ==========================================

def add_stock_movement(product_id, product_name, sku,
                       movement_type, quantity, note=None):
    """
    Καταγράφει μία κίνηση αποθέματος στο ιστορικό.
    """

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection = get_connection()

    # Αποθηκεύουμε τα στοιχεία της κίνησης.
    connection.execute("""
        INSERT INTO stock_movements (
            product_id,
            product_name,
            sku,
            movement_type,
            quantity,
            note
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        product_id,
        product_name,
        sku,
        movement_type,
        quantity,
        note
    ))

    # Αποθηκεύουμε την κίνηση.
    connection.commit()

    # Κλείνουμε τη σύνδεση.
    connection.close()

# Εμφανίζουμε όλες τις κινήσεις αποθήκης για έλεγχο.
def get_all_stock_movements():

    connection = get_connection()

    movements = connection.execute("""
        SELECT *
        FROM stock_movements
        ORDER BY id DESC
    """).fetchall()

    connection.close()

    return movements

# Προσθέτουμε μια νέα κατηγορία στη βάση δεδομένων.
def add_category(name):
    """Αποθηκεύει μια νέα κατηγορία."""
    connection = get_connection()

    connection.execute(
        "INSERT INTO categories (name) VALUES (?)",
        (name,)
    )

    connection.commit()
    connection.close()


# Διαβάζουμε όλες τις κατηγορίες από τη βάση δεδομένων.
def get_all_categories():
    """Επιστρέφει όλες τις κατηγορίες αλφαβητικά."""
    connection = get_connection()

    categories = connection.execute(
        "SELECT * FROM categories ORDER BY name ASC"
    ).fetchall()

    connection.close()
    return categories


# Προσθέτουμε ένα νέο προϊόν στη βάση δεδομένων.
def add_product(name, sku, price, quantity, category):
    """
    Αποθηκεύει ένα νέο προϊόν και καταγράφει
    την αρχική ποσότητά του στο ιστορικό αποθήκης.
    """

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection = get_connection()

    try:
        # Καταχωρίζουμε τα στοιχεία του νέου προϊόντος.
        cursor = connection.execute(
            """
            INSERT INTO products (name, sku, price, quantity, category)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, sku, price, quantity, category)
        )

        # Παίρνουμε το ID του προϊόντος που μόλις δημιουργήθηκε.
        product_id = cursor.lastrowid

        # Αν η αρχική ποσότητα είναι μεγαλύτερη από μηδέν,
        # καταγράφουμε την εισαγωγή στο ιστορικό.
        if quantity > 0:

            connection.execute(
                """
                INSERT INTO stock_movements (
                    product_id,
                    product_name,
                    sku,
                    movement_type,
                    quantity,
                    note
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    name,
                    sku,
                    "in",
                    quantity,
                    "Αρχικό απόθεμα νέου προϊόντος"
                )
            )

        # Αποθηκεύουμε μαζί το προϊόν και την κίνησή του.
        connection.commit()

    except Exception:
        # Αν παρουσιαστεί σφάλμα, ακυρώνουμε όλες τις αλλαγές.
        connection.rollback()
        raise

    finally:
        # Κλείνουμε τη σύνδεση με τη βάση δεδομένων.
        connection.close()


# Διαβάζουμε όλα τα προϊόντα από τη βάση δεδομένων.
def get_all_products():
    #Επιστρέφει όλα τα προϊόντα που έχουν αποθηκευτεί.

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection= get_connection()

# Εκτελούμε ερώτημα για να πάρουμε όλα τα προϊόντα.
    products = connection.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()
  
    # Κλείνουμε τη σύνδεση με τη βάση.
    connection.close()

    # Επιστρέφουμε τη λίστα των προϊόντων.
    return products


# Αναζητούμε ένα συγκεκριμένο προϊόν με βάση το ID του.
def get_product_by_id(product_id):
    """Επιστρέφει ένα προϊόν ή None αν δεν υπάρχει."""

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection = get_connection()

    # Αναζητούμε μόνο το προϊόν με το συγκεκριμένο ID.
    product = connection.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    # Κλείνουμε τη σύνδεση με τη βάση.
    connection.close()

    # Επιστρέφουμε το προϊόν που βρέθηκε.
    return product




# Ενημερώνουμε τα στοιχεία ενός υπάρχοντος προϊόντος.
def update_product(product_id, name, sku, price, quantity, category):
    """
    Ενημερώνει ένα προϊόν και καταγράφει τις αλλαγές
    στην ποσότητα του αποθέματος.
    """

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection = get_connection()

    try:
        # Βρίσκουμε τα τρέχοντα στοιχεία του προϊόντος.
        old_product = connection.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        # Ελέγχουμε αν υπάρχει το προϊόν.
        if old_product is None:
            return False

        # Παίρνουμε την προηγούμενη ποσότητα.
        old_quantity = old_product["quantity"]

        # Υπολογίζουμε τη διαφορά μεταξύ νέας και παλιάς ποσότητας.
        quantity_difference = quantity - old_quantity

        # Ενημερώνουμε τα στοιχεία του προϊόντος.
        connection.execute(
            """
            UPDATE products
            SET name = ?, sku = ?, price = ?, quantity = ?, category = ?
            WHERE id = ?
            """,
            (name, sku, price, quantity, category, product_id)
        )

        # Ελέγχουμε αν άλλαξε η ποσότητα.
        if quantity_difference != 0:

            # Αν η ποσότητα αυξήθηκε, έχουμε εισαγωγή αποθέματος.
            if quantity_difference > 0:
                movement_type = "in"
                movement_quantity = quantity_difference
                movement_note = "Αύξηση αποθέματος μέσω επεξεργασίας"

            # Αν η ποσότητα μειώθηκε, έχουμε εξαγωγή αποθέματος.
            else:
                movement_type = "out"
                movement_quantity = abs(quantity_difference)
                movement_note = "Μείωση αποθέματος μέσω επεξεργασίας"

            # Καταγράφουμε την κίνηση στο ιστορικό.
            connection.execute(
                """
                INSERT INTO stock_movements (
                    product_id,
                    product_name,
                    sku,
                    movement_type,
                    quantity,
                    note
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    name,
                    sku,
                    movement_type,
                    movement_quantity,
                    movement_note
                )
            )

        # Αποθηκεύουμε μαζί την ενημέρωση και την κίνηση.
        connection.commit()

        return True

    except Exception:
        # Αν παρουσιαστεί σφάλμα, ακυρώνουμε τις αλλαγές.
        connection.rollback()
        raise

    finally:
        # Κλείνουμε τη σύνδεση με τη βάση δεδομένων.
        connection.close()



# Διαγράφουμε ένα προϊόν από τη βάση δεδομένων.
def delete_product(product_id):
    """Διαγράφει το προϊόν που αντιστοιχεί στο συγκεκριμένο ID."""

    # Ανοίγουμε σύνδεση με τη βάση δεδομένων.
    connection = get_connection()

    # Διαγράφουμε μόνο το προϊόν με το συγκεκριμένο ID.
    connection.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    # Αποθηκεύουμε τη διαγραφή.
    connection.commit()

    # Κλείνουμε τη σύνδεση.
    connection.close()



# Εισάγουμε τη βιβλιοθήκη για να μπορούμε να αφαιρούμε τους τόνους.
import unicodedata


# Μετατρέπουμε το κείμενο σε μορφή κατάλληλη για αναζήτηση.
def normalize_search_text(text):
    """Αφαιρεί τους τόνους και μετατρέπει τα γράμματα σε πεζά."""
    text = str(text).casefold()
    text = unicodedata.normalize("NFD", text)

    return "".join(
        character
        for character in text
        if unicodedata.category(character) != "Mn"
    )



# Αναγνωρίζουμε εναλλακτικές ονομασίες για συνηθισμένα προϊόντα.
PRODUCT_SYNONYMS = {
    "ακουστικα": [
        "headphones",
        "headset",
        "ακουστικα κεφαλης",
        "earphones",
        "wireless headphones"
    ],
    "ποντικι": [
        "mouse",
        "ποντικι υπολογιστη",
        "computer mouse"
    ],
    "πληκτρολογιο": [
        "keyboard",
        "mechanical keyboard"
    ],
    "οθονη": [
        "monitor",
        "display",
        "screen",
        "οθονη υπολογιστη"
    ],
    "φορητος υπολογιστης": [
        "laptop",
        "notebook",
        "portable computer"
    ]
}

# ==========================================
# ΜΕΤΑΤΡΟΠΗ GREEKLISH ΣΕ ΕΛΛΗΝΙΚΑ
# ==========================================

def greeklish_to_greek(text):
    """Μετατρέπει συνηθισμένες γραφές Greeklish σε ελληνικούς χαρακτήρες."""

    text = text.lower()

    replacements = [
        ("th", "θ"),
        ("ch", "χ"),
        ("ps", "ψ"),
        ("ks", "ξ"),
        ("ou", "ου"),
        ("ai", "αι"),
        ("ei", "ι"),
        ("oi", "ι"),
        ("ui", "ι"),
        ("mp", "μπ"),
        ("nt", "ντ"),
        ("gk", "γκ"),
        ("gg", "γγ"),
        ("tz", "τζ"),
        ("ts", "τσ"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    translation = str.maketrans({
        "a": "α",
        "b": "β",
        "c": "κ",
        "d": "δ",
        "e": "ε",
        "f": "φ",
        "g": "γ",
        "h": "η",
        "i": "ι",
        "j": "τζ",
        "k": "κ",
        "l": "λ",
        "m": "μ",
        "n": "ν",
        "o": "ο",
        "p": "π",
        "q": "κ",
        "r": "ρ",
        "s": "σ",
        "t": "τ",
        "u": "υ",
        "v": "β",
        "w": "ω",
        "x": "χ",
        "y": "υ",
        "z": "ζ",
    })

    return text.translate(translation)

# ==========================================
# ΕΞΥΠΝΗ ΑΝΑΖΗΤΗΣΗ ΠΡΟΪΟΝΤΩΝ
# Ελληνικά, Αγγλικά, Greeklish και συνώνυμα
# ==========================================

def search_products(search_term):
    """Αναζητά προϊόντα με ελληνικά, αγγλικά, Greeklish και συνώνυμα."""

    connection = get_connection()

    products = connection.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    connection.close()

    normalized_term = normalize_search_text(search_term).strip()

    if not normalized_term:
        return products

    # Δημιουργούμε και ελληνική εκδοχή του όρου.
    greek_term = normalize_search_text(
        greeklish_to_greek(normalized_term)
    ).strip()

    # Όλοι οι πιθανοί όροι αναζήτησης.
    search_variants = {
        normalized_term,
        greek_term
    }

    # Ενεργοποίηση συνωνύμων ακόμη και με μερική λέξη.
    for synonym_key, synonyms in PRODUCT_SYNONYMS.items():

        normalized_key = normalize_search_text(synonym_key)

        normalized_synonyms = {
            normalize_search_text(synonym)
            for synonym in synonyms
        }

        synonym_group = {normalized_key} | normalized_synonyms

        if any(
            normalized_term in variant
            or variant in normalized_term
            or greek_term in variant
            or variant in greek_term
            for variant in synonym_group
            if len(variant) >= 2
        ):
            search_variants.update(synonym_group)

    matching_products = []

    for product in products:

        name = normalize_search_text(product["name"])
        sku = normalize_search_text(product["sku"])

        greek_name = normalize_search_text(
            greeklish_to_greek(name)
        )

        words = name.split()

        # Άμεση αντιστοίχιση σε όνομα, SKU ή Greeklish.
        if any(
            term in name
            or term in sku
            or term in greek_name
            for term in search_variants
            if len(term) >= 2
        ):
            matching_products.append(product)
            continue

        # Έλεγχος μικρών ορθογραφικών λαθών.
        found_match = False

        for term in search_variants:

            for search_word in term.split():

                if len(search_word) < 4:
                    continue

                close_words = difflib.get_close_matches(
                    search_word,
                    words,
                    n=1,
                    cutoff=0.82
                )

                if close_words:
                    found_match = True
                    break

            if found_match:
                break

        if found_match:
            matching_products.append(product)

        # ==========================================
    # ΤΑΞΙΝΟΜΗΣΗ ΜΕ ΒΑΣΗ ΤΗ ΣΧΕΤΙΚΟΤΗΤΑ
    # ==========================================

    def product_relevance(product):

        name = normalize_search_text(product["name"])
        sku = normalize_search_text(product["sku"])

        # 1. Ακριβής αντιστοίχιση ονόματος.
        if name in search_variants:
            return 0

        # 2. Το όνομα αρχίζει με τον όρο αναζήτησης.
        if any(name.startswith(term) for term in search_variants):
            return 1

        # 3. Ο όρος υπάρχει μέσα στο όνομα.
        if any(term in name for term in search_variants):
            return 2

        # 4. Αντιστοίχιση μέσω SKU.
        if any(term in sku for term in search_variants):
            return 3

        # 5. Συνώνυμα ή ορθογραφικές αντιστοιχίσεις.
        return 4

    # Τα πιο σχετικά προϊόντα εμφανίζονται πρώτα.
    matching_products.sort(key=product_relevance)

    return matching_products

# Επιστρέφουμε το πλήθος προϊόντων ανά κατηγορία.
def get_products_per_category():

    connection = get_connection()

    results = connection.execute("""
        SELECT
            c.name AS category,
            COUNT(p.id) AS total
        FROM categories c
        LEFT JOIN products p
            ON p.category = c.name
        GROUP BY c.name
        ORDER BY c.name ASC
    """).fetchall()

    connection.close()

    return results