# StorePilot

Εφαρμογή διαχείρισης αποθήκης και προϊόντων με Flask και SQLite.

## Δυνατότητες

- Dashboard με συνολικά προϊόντα, τεμάχια, χαμηλό απόθεμα και αξία αποθήκης.
- Κατάλογος προϊόντων με αναζήτηση και φίλτρα κατηγορίας.
- Αναζήτηση με ελληνικά, χωρίς τόνους, Greeklish και εναλλακτικές ονομασίες.
- Προσθήκη, επεξεργασία και διαγραφή προϊόντων.
- Καταγραφή εισαγωγών και εξαγωγών στο ιστορικό αποθήκης.
- Φίλτρα ιστορικού και εξαγωγή σε Excel.
- Ειδοποίηση χαμηλού αποθέματος με πρόοδο προς τον επιθυμητό στόχο.
- Responsive σχεδιασμός.

## Τεχνολογίες

- Python
- Flask
- SQLite
- HTML / CSS / JavaScript
- Flask-WTF (CSRF protection)
- openpyxl (Excel export)

## Εγκατάσταση

Απαιτείται Python 3.10 ή νεότερη.

1. Κάνε clone το repository:
   ```bash
   git clone <REPOSITORY-URL>
   cd StorePilot
   ```

2. Δημιούργησε virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Ενεργοποίησέ το στα Windows:
   ```powershell
   .venv\\Scripts\\Activate.ps1
   ```

   Σε macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. Εγκατάστησε τις εξαρτήσεις:
   ```bash
   pip install -r requirements.txt
   ```

5. Εκκίνησε την εφαρμογή:
   ```bash
   python app.py
   ```

6. Άνοιξε στον browser:
   `http://127.0.0.1:5000`

Η εφαρμογή χρησιμοποιεί από προεπιλογή το `storepilot.db` που βρίσκεται στον βασικό φάκελο του project. Αν το αρχείο δεν υπάρχει, οι πίνακες δημιουργούνται αυτόματα κατά την εκκίνηση. Το αρχείο βάσης που περιλαμβάνεται στο repository περιέχει ενδεικτικά δεδομένα επίδειξης.

## Ρυθμίσεις

Μπορείς να ορίσεις τις μεταβλητές περιβάλλοντος `SECRET_KEY` και `DATABASE_NAME`. Για τοπική ανάπτυξη η εφαρμογή δημιουργεί προσωρινό secret key αν δεν έχει οριστεί `SECRET_KEY`. Για deployment πρέπει να οριστεί ισχυρό, μόνιμο secret key από τις ρυθμίσεις του hosting provider.

## Δομή φακέλων

```text
StorePilot/
├── app.py
├── database.py
├── create_demo_database.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── storepilot.db
├── static/
│   ├── css/style.css
│   └── images/
└── templates/
    ├── index.html
    ├── add_product.html
    ├── edit_product.html
    └── stock_history.html
```

## Σημείωση

Το `create_demo_database.py` δημιουργεί ξεχωριστή βάση επίδειξης και δεν εκτελείται αυτόματα κατά την εκκίνηση της εφαρμογής.
