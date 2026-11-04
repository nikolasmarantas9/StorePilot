# Βοηθητικές λειτουργίες για την αναγνώριση παρόμοιων λέξεων.
import difflib
import unicodedata  
import os
# Εισάγουμε το Flask για να δημιουργήσουμε την εφαρμογή μας.
from flask import Flask, render_template, request, redirect, url_for,  flash
# Εισάγουμε την προστασία CSRF για τις φόρμες.
from flask_wtf.csrf import CSRFProtect
from io import BytesIO
from openpyxl import Workbook
from flask import send_file 

# Εισάγουμε τη λειτουργία δημιουργίας του πίνακα προϊόντων.
from database import( 
    create_tables ,
    add_product ,
    get_all_products,  
    get_product_by_id,
    update_product,
    delete_product,
    search_products,
    get_all_categories,
    get_all_stock_movements,
    get_products_per_category
    
    )

# Δημιουργούμε την εφαρμογή Flask.
app = Flask(__name__)

# Φορτώνουμε το Secret Key.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)

# Ενεργοποιούμε την προστασία CSRF.
csrf = CSRFProtect(app)

# Οι μοναδικές κατηγορίες που επιτρέπονται στο StorePilot.
ALLOWED_CATEGORIES = (
    "Αποθήκευση",
    "Καλώδια",
    "Οθόνες",
    "Περιφερειακά",
    "Υπολογιστές"
)

# Ορίζουμε τι θα εμφανίζεται στην αρχική σελίδα.

# Αυτόματες προτάσεις αναζήτησης προϊόντων.
@app.route("/api/search-suggestions")
def search_suggestions():

    # Διαβάζουμε αυτό που πληκτρολογεί ο χρήστης.
    search_term = request.args.get("q", "").strip()

    # Δεν εμφανίζουμε προτάσεις για αναζητήσεις κάτω από 2 χαρακτήρες.
    if len(search_term) < 2:
        return {"suggestions": []}

    # Αναζητούμε προϊόντα στη βάση δεδομένων.
    products = search_products(search_term)

    # Δημιουργούμε προτάσεις από πραγματικά προϊόντα.
    suggestions = []

    for product in products[:7]:
        suggestions.append({
            "name": product["name"],
            "sku": product["sku"]
        })

    return {"suggestions": suggestions}

@app.route("/")
def home():
    # Παίρνουμε τους όρους από τη διεύθυνση της σελίδας.
    search_term = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "").strip()

    # Φορτώνουμε όλα τα προϊόντα για τον υπολογισμό στατιστικών.
    all_products = get_all_products()

    # Υπολογισμός συνολικών στατιστικών αποθήκης.
    total_products = len(all_products)


    # Υπολογισμός συνολικών τεμαχίων αποθήκης.
    total_stock = sum(
        product["quantity"]
        for product in all_products
    )

    # Υπολογισμός συνολικής χρηματικής αξίας αποθέματος.
    total_inventory_value = sum(
        product["price"] * product["quantity"]
        for product in all_products
    )

    # Υπολογισμός προϊόντων με χαμηλό απόθεμα.
    low_stock_count = sum(
        1
        for product in all_products
        if product["quantity"] <= 5
        
    )
        # Συγκεντρώνουμε τα προϊόντα που χρειάζονται αναπλήρωση.
    low_stock_products = [
        product
        for product in all_products
        if product["quantity"] <= 5
    ]

    # Ταξινομούμε τα προϊόντα από το μικρότερο απόθεμα.
    low_stock_products.sort(
        key=lambda product: product["quantity"]
    )
           # Πρώτα εκτελούμε την υπάρχουσα αναζήτηση.
    if search_term:
        products = search_products(search_term)
    else:
        products = all_products
    # Έπειτα φιλτράρουμε τα αποτελέσματα ανά κατηγορία.
    if selected_category:
        products = [
            product
            for product in products
            if product["category"] == selected_category
        ]

    # Φορτώνουμε τις διαθέσιμες κατηγορίες.
    categories = get_all_categories()

    # Υπολογίζουμε πόσα προϊόντα υπάρχουν σε κάθε κατηγορία.
    products_per_category = get_products_per_category()

    # Συγκεντρώνουμε το πραγματικό απόθεμα ανά κατηγορία.
    stock_by_category = {}

    for product in all_products:
        category_name = product["category"]
        stock_by_category[category_name] = (
            stock_by_category.get(category_name, 0)
            + product["quantity"]
        )

    # Ταξινομούμε τις κατηγορίες από το μεγαλύτερο απόθεμα.
    stock_per_category = [
        {"category": category, "quantity": quantity}
        for category, quantity in stock_by_category.items()
    ]
   # Ταξινομούμε τις κατηγορίες από το μεγαλύτερο απόθεμα.
    stock_per_category.sort(
        key=lambda item: item["quantity"],
        reverse=True
    )

    # Εμφανίζουμε τα δεδομένα στο Terminal για έλεγχο.
    print("STOCK PER CATEGORY:", stock_per_category)

    # Βρίσκουμε τη μεγαλύτερη ποσότητα για τις μπάρες του γραφήματος.
    max_category_stock = max(
        (item["quantity"] for item in stock_per_category),
        default=1
    ) or 1

    # Φορτώνουμε τις πέντε πιο πρόσφατες κινήσεις αποθήκης.
    recent_stock_movements = get_all_stock_movements()[:5]

    # Βρίσκουμε τη μεγαλύτερη κατηγορία για τον υπολογισμό των μπαρών.
    max_category_count = max(
        (item["total"] for item in products_per_category),
        default=1
    )
    # Επιθυμητό απόθεμα για κάθε προϊόν.
    
    target_stock = 20

    # Στέλνουμε όλα τα δεδομένα στη σελίδα.
    return render_template(
        "index.html",
        products=products,
        search_term=search_term,
        categories=categories,
        selected_category=selected_category,
        total_products=total_products,
        total_stock=total_stock,
        low_stock_count=low_stock_count,
        low_stock_products=low_stock_products,
        total_inventory_value=total_inventory_value,
        products_per_category=products_per_category,
        stock_per_category=stock_per_category,
        max_category_stock=max_category_stock,
        recent_stock_movements=recent_stock_movements,
        target_stock=target_stock,
        max_category_count=max_category_count
    )

# Ορίζουμε τη διαδρομή για την προσθήκη νέου προϊόντος.
@app.route("/products/add", methods=["GET", "POST"])
def add_product_page():

    # Αν ο χρήστης υποβάλει τη φόρμα, διαβάζουμε τα στοιχεία της.
    if request.method == "POST":

        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        price_text = request.form.get("price", "").strip()
        quantity_text = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()

        # Ελέγχουμε ότι συμπληρώθηκαν όλα τα πεδία.
        if not all([name, sku, price_text, quantity_text, category]):
            flash("Συμπλήρωσε όλα τα πεδία.", "error")
            return redirect(url_for("add_product_page"))
       
        # Ελέγχουμε αν η κατηγορία ανήκει στις επιτρεπόμενες.
          
        if category not in ALLOWED_CATEGORIES:
           flash("Επίλεξε μία από τις διαθέσιμες κατηγορίες.", "error")
           return redirect(url_for("add_product_page"))
        

        # Ελέγχουμε ότι η τιμή και η ποσότητα είναι έγκυρες.
        try:
            price = float(price_text.replace(",", "."))
            quantity = int(quantity_text)

            if price < 0 or quantity < 0:
                raise ValueError

        except ValueError:
            flash("Η τιμή και η ποσότητα πρέπει να είναι έγκυροι μη αρνητικοί αριθμοί.", "error")
            return redirect(url_for("add_product_page"))

        # Αποθηκεύουμε το προϊόν στη βάση δεδομένων.
        try:
            add_product(name, sku, price, quantity, category)
        except Exception:
            app.logger.exception("Αποτυχία καταχώρισης προϊόντος.")
            flash("Δεν ήταν δυνατή η καταχώριση. Έλεγξε αν ο κωδικός SKU υπάρχει ήδη.", "error")
            return redirect(url_for("add_product_page"))

        # Ενημερώνουμε τον χρήστη ότι η καταχώριση ολοκληρώθηκε.
        flash("Το προϊόν προστέθηκε επιτυχώς!", "success")
        return redirect(url_for("add_product_page"))

    # Αν ο χρήστης ανοίξει τη διαδρομή, εμφανίζουμε τη φόρμα.
    return render_template("add_product.html")


# Επεξεργασία υπάρχοντος προϊόντος.
@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product_page(product_id):

    # Αναζητούμε το προϊόν στη βάση με βάση το ID.
    product = get_product_by_id(product_id)

    # Αν δεν υπάρχει, επιστρέφουμε στην αρχική σελίδα.
    if product is None:
        flash("Το προϊόν δεν βρέθηκε.", "error")
        return redirect(url_for("home"))

    # Αν υποβληθεί η φόρμα, διαβάζουμε τα νέα στοιχεία.
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip()
        price_text = request.form.get("price", "").strip()
        quantity_text = request.form.get("quantity", "").strip()
        category = request.form.get("category", "").strip()

       
        # Ελέγχουμε αν συμπληρώθηκαν όλα τα πεδία.
        if not all([name, sku, price_text, quantity_text, category]):
            flash("Συμπλήρωσε όλα τα πεδία.", "error")
            return redirect(
                url_for("edit_product_page", product_id=product_id)
            )
           
        # Ελέγχουμε αν η νέα κατηγορία είναι επιτρεπόμενη.
        if category not in ALLOWED_CATEGORIES:
            flash("Επίλεξε μία από τις διαθέσιμες κατηγορίες.", "error")
            return redirect(
                url_for("edit_product_page", product_id=product_id)
            )


        # Ελέγχουμε την τιμή και την ποσότητα.
        try:
            price = float(price_text.replace(",", "."))
            quantity = int(quantity_text)

            if price < 0 or quantity < 0:
                raise ValueError

        except ValueError:
            flash(
                "Η τιμή και η ποσότητα πρέπει να είναι έγκυροι "
                "μη αρνητικοί αριθμοί.",
                "error"
            )
            return redirect(
                url_for("edit_product_page", product_id=product_id)
            )

        # Αποθηκεύουμε τις αλλαγές στη βάση δεδομένων.
        try:
            update_product(
                product_id,
                name,
                sku,
                price,
                quantity,
                category
            )
        except Exception:
            app.logger.exception("Αποτυχία ενημέρωσης προϊόντος.")
            flash(
                "Δεν ήταν δυνατή η ενημέρωση. "
                "Έλεγξε αν ο κωδικός SKU χρησιμοποιείται ήδη.",
                "error"
            )
            return redirect(
                url_for("edit_product_page", product_id=product_id)
            )

        flash("Το προϊόν ενημερώθηκε επιτυχώς!", "success")
        return redirect(url_for("home"))

    # Εμφανίζουμε τη φόρμα με τα υπάρχοντα στοιχεία.
    return render_template("edit_product.html", product=product)


# Διαγραφή προϊόντος.
@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product_page(product_id):

    # Ελέγχουμε αν υπάρχει το προϊόν πριν από τη διαγραφή.
    product = get_product_by_id(product_id)

    if product is None:
        flash("Το προϊόν δεν βρέθηκε.", "error")
        return redirect(url_for("home"))

    # Διαγράφουμε το συγκεκριμένο προϊόν.
    try:
        delete_product(product_id)
    except Exception:
        app.logger.exception("Αποτυχία διαγραφής προϊόντος.")
        flash("Δεν ήταν δυνατή η διαγραφή του προϊόντος.", "error")
        return redirect(url_for("home"))

    flash("Το προϊόν διαγράφηκε επιτυχώς.", "success")
    return redirect(url_for("home"))


# Δημιουργούμε τον πίνακα προϊόντων αν δεν υπάρχει ήδη.
create_tables()



# ==========================================
# ΕΞΑΓΩΓΗ ΙΣΤΟΡΙΚΟΥ ΚΙΝΗΣΕΩΝ ΣΕ EXCEL
# ==========================================

@app.route("/stock-history/export")
def export_stock_history():
    """Εξάγει τις φιλτραρισμένες κινήσεις σε επαγγελματικό Excel."""

    # Διαβάζουμε τα φίλτρα της σελίδας ιστορικού.
    search_term = request.args.get("search", "").strip().casefold()
    selected_type = request.args.get("type", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Φορτώνουμε όλες τις κινήσεις από τη βάση δεδομένων.
    movements = get_all_stock_movements()

    # Φιλτράρισμα ανά τύπο κίνησης.
    if selected_type in ("in", "out"):
        movements = [
            movement for movement in movements
            if movement["movement_type"] == selected_type
        ]

    # Φιλτράρισμα ανά όνομα προϊόντος ή SKU.
    if search_term:
        movements = [
            movement for movement in movements
            if search_term in movement["product_name"].casefold()
            or search_term in movement["sku"].casefold()
        ]

    # Φιλτράρισμα από ημερομηνία.
    if date_from:
        movements = [
            movement for movement in movements
            if movement["created_at"][:10] >= date_from
        ]

    # Φιλτράρισμα έως ημερομηνία.
    if date_to:
        movements = [
            movement for movement in movements
            if movement["created_at"][:10] <= date_to
        ]

    # Δημιουργία αρχείου Excel.
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Ιστορικό Κινήσεων"

    # Αφαίρεση των βοηθητικών γραμμών του Excel.
    worksheet.sheet_view.showGridLines = False

    # Επιλογή μεγέθους εμφάνισης κατά το άνοιγμα.
    worksheet.sheet_view.zoomScale = 90

    # ------------------------------------------
    # ΣΤΥΛ ΚΑΙ ΧΡΩΜΑΤΑ
    # ------------------------------------------

    from openpyxl.styles import (
        Font,
        PatternFill,
        Alignment,
        Border,
        Side
    )

    from datetime import datetime

    # Χρώματα StorePilot.
    dark_blue = "202A44"
    mint = "36C9A7"
    white = "FFFFFF"
    light_blue = "F2F5FA"
    light_green = "E8F8F2"
    light_red = "FDECEC"
    green = "15966D"
    red = "D9534F"
    gray = "667085"
    border_color = "DCE4EF"

    # ------------------------------------------
    # ΕΠΙΚΕΦΑΛΙΔΕΣ
    # ------------------------------------------

    headers = [
        "Προϊόν",
        "Κωδικός SKU",
        "Τύπος Κίνησης",
        "Ποσότητα",
        "Ημερομηνία",
        "Περιγραφή"
    ]

    worksheet.append(headers)

    # Μορφοποίηση επικεφαλίδων.
    for cell in worksheet[1]:

        cell.font = Font(
            name="Arial",
            size=11,
            bold=True,
            color=white
        )

        cell.fill = PatternFill(
            fill_type="solid",
            fgColor=dark_blue
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    worksheet.row_dimensions[1].height = 32

    # ------------------------------------------
    # ΚΑΤΑΧΩΡΙΣΗ ΚΙΝΗΣΕΩΝ
    # ------------------------------------------

    for movement in movements:

        # Μετατροπή τύπου κίνησης σε ελληνικό κείμενο.
        movement_label = (
            "Εισαγωγή"
            if movement["movement_type"] == "in"
            else "Εξαγωγή"
        )

        # Ανάκτηση ποσότητας.
        quantity = movement["quantity"]

        # Οι εξαγωγές έχουν αρνητικό πρόσημο.
        if movement["movement_type"] == "out":
            quantity = -quantity

        # Μετατροπή ημερομηνίας σε πραγματική ημερομηνία Excel.
        date_value = movement["created_at"]

        try:
            date_value = datetime.fromisoformat(
                str(date_value)
            )
        except (ValueError, TypeError):
            pass

        # Προσθήκη γραμμής στο Excel.
        worksheet.append([
            movement["product_name"],
            movement["sku"],
            movement_label,
            quantity,
            date_value,
            movement["note"] or "—"
        ])

    # ------------------------------------------
    # ΜΟΡΦΟΠΟΙΗΣΗ ΓΡΑΜΜΩΝ
    # ------------------------------------------

    thin_border = Border(
        bottom=Side(
            style="thin",
            color=border_color
        )
    )

    for row_index in range(2, worksheet.max_row + 1):

        # Εναλλαγή χρωμάτων στις γραμμές.
        row_fill = (
            white
            if row_index % 2 == 0
            else light_blue
        )

        for cell in worksheet[row_index]:

            cell.font = Font(
                name="Arial",
                size=10,
                color=dark_blue
            )

            cell.fill = PatternFill(
                fill_type="solid",
                fgColor=row_fill
            )

            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

            cell.border = thin_border

        # Μορφοποίηση ποσότητας.
        quantity_cell = worksheet.cell(
            row=row_index,
            column=4
        )

        quantity_cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        movement_cell = worksheet.cell(
            row=row_index,
            column=3
        )

        # Πράσινο για εισαγωγές.
        if movement_cell.value == "Εισαγωγή":

            movement_cell.font = Font(
                name="Arial",
                size=10,
                bold=True,
                color=green
            )

            movement_cell.fill = PatternFill(
                fill_type="solid",
                fgColor=light_green
            )

            quantity_cell.font = Font(
                name="Arial",
                size=10,
                bold=True,
                color=green
            )

        # Κόκκινο για εξαγωγές.
        else:

            movement_cell.font = Font(
                name="Arial",
                size=10,
                bold=True,
                color=red
            )

            movement_cell.fill = PatternFill(
                fill_type="solid",
                fgColor=light_red
            )

            quantity_cell.font = Font(
                name="Arial",
                size=10,
                bold=True,
                color=red
            )

        # Μορφοποίηση ημερομηνίας.
        date_cell = worksheet.cell(
            row=row_index,
            column=5
        )

        if isinstance(date_cell.value, datetime):
            date_cell.number_format = "DD/MM/YYYY HH:MM:SS"

        date_cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

        # Ύψος κάθε γραμμής.
        worksheet.row_dimensions[row_index].height = 30

    # ------------------------------------------
    # ΠΛΑΤΟΣ ΣΤΗΛΩΝ
    # ------------------------------------------

    column_widths = {
        "A": 30,
        "B": 20,
        "C": 22,
        "D": 15,
        "E": 25,
        "F": 45
    }

    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    # ------------------------------------------
    # ΦΙΛΤΡΑ ΚΑΙ ΣΤΑΘΕΡΗ ΕΠΙΚΕΦΑΛΙΔΑ
    # ------------------------------------------

    # Δυνατότητα φιλτραρίσματος από το Excel.
    worksheet.auto_filter.ref = worksheet.dimensions

    # Η πρώτη γραμμή παραμένει ορατή κατά το scroll.
    worksheet.freeze_panes = "A2"

    # ------------------------------------------
    # ΡΥΘΜΙΣΕΙΣ ΕΚΤΥΠΩΣΗΣ
    # ------------------------------------------

    worksheet.page_setup.orientation = "landscape"
    worksheet.page_setup.paperSize = worksheet.PAPERSIZE_A4

    worksheet.page_setup.fitToWidth = 1
    worksheet.page_setup.fitToHeight = 0

    worksheet.sheet_properties.pageSetUpPr.fitToPage = True

    worksheet.page_margins.left = 0.25
    worksheet.page_margins.right = 0.25
    worksheet.page_margins.top = 0.5
    worksheet.page_margins.bottom = 0.5

    # ------------------------------------------
    # ΑΠΟΘΗΚΕΥΣΗ ΑΡΧΕΙΟΥ
    # ------------------------------------------

    excel_file = BytesIO()

    workbook.save(excel_file)

    excel_file.seek(0)

    # Αποστολή αρχείου στον χρήστη.
    return send_file(
        excel_file,
        as_attachment=True,
        download_name="StorePilot_Stock_History.xlsx",
        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        )
    )


# ==========================================
# ΙΣΤΟΡΙΚΟ ΚΙΝΗΣΕΩΝ ΑΠΟΘΗΚΗΣ
# ==========================================

@app.route("/stock-history")
def stock_history():
    """Εμφανίζει το ιστορικό κινήσεων αποθήκης."""

    # Διαβάζουμε τα φίλτρα της σελίδας.
    search_term = request.args.get("search", "").strip().casefold()
    selected_type = request.args.get("type", "").strip()

    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Φορτώνουμε όλες τις κινήσεις από τη βάση.
    all_movements = get_all_stock_movements()

    # Υπολογίζουμε συνολικά στατιστικά.
    total_movements = len(all_movements)

    total_in = sum(
        movement["quantity"]
        for movement in all_movements
        if movement["movement_type"] == "in"
    )

    total_out = sum(
        movement["quantity"]
        for movement in all_movements
        if movement["movement_type"] == "out"
    )

    # Ξεκινάμε με όλες τις κινήσεις.
    movements = all_movements

    # Φιλτράρουμε ανά τύπο κίνησης.
    if selected_type in ("in", "out"):
        movements = [
            movement for movement in movements
            if movement["movement_type"] == selected_type
        ]

    # Φιλτράρουμε με βάση το όνομα ή το SKU.
    if search_term:
        movements = [
            movement for movement in movements
            if search_term in movement["product_name"].casefold()
            or search_term in movement["sku"].casefold()
        ]

    # Φιλτράρουμε από συγκεκριμένη ημερομηνία.
    if date_from:
        movements = [
            movement for movement in movements
            if movement["created_at"][:10] >= date_from
        ]

    # Φιλτράρουμε μέχρι συγκεκριμένη ημερομηνία.
    if date_to:
        movements = [
            movement for movement in movements
            if movement["created_at"][:10] <= date_to
        ]

    # Εμφανίζουμε τη σελίδα ιστορικού.
    return render_template(
        "stock_history.html",
        movements=movements,
        search_term=request.args.get("search", ""),
        selected_type=selected_type,
        date_from=date_from,
        date_to=date_to,
        total_movements=total_movements,
        total_in=total_in,
        total_out=total_out,
    )

# Εκκινούμε τον server όταν εκτελούμε αυτό το αρχείο.
if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000, debug=False)