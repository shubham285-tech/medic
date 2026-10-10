import os
import sqlite3
import datetime
import hashlib
import json
import threading
from datetime import timezone
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", "database.db")
_firestore_db = None
_firestore_lock = threading.Lock()


def uses_firebase():
    return bool(
        os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    )


def _firestore():
    global _firestore_db
    if _firestore_db is None:
        with _firestore_lock:
            if _firestore_db is None:
                import firebase_admin
                from firebase_admin import credentials, firestore

                try:
                    firebase_admin.get_app()
                except ValueError:
                    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
                    if service_account_json:
                        try:
                            service_account = json.loads(service_account_json)
                        except json.JSONDecodeError as exc:
                            raise RuntimeError(
                                "FIREBASE_SERVICE_ACCOUNT_KEY must contain valid service-account JSON."
                            ) from exc
                        credential = credentials.Certificate(service_account)
                    else:
                        credential = credentials.ApplicationDefault()

                    firebase_admin.initialize_app(
                        credential,
                        options={"projectId": os.environ.get("FIREBASE_PROJECT_ID")}
                        if os.environ.get("FIREBASE_PROJECT_ID")
                        else None,
                    )

                _firestore_db = firestore.client()
    return _firestore_db


def _timestamp():
    return datetime.datetime.now(timezone.utc).isoformat()


def _collection(name):
    return _firestore().collection(name)


def _firebase_next_id(name):
    from firebase_admin import firestore

    counter = _collection("_counters").document(name)
    transaction = _firestore().transaction()

    @firestore.transactional
    def increment(transaction):
        snapshot = counter.get(transaction=transaction)
        next_value = (snapshot.get("value") if snapshot.exists else 0) + 1
        transaction.set(counter, {"value": next_value})
        return next_value

    return increment(transaction)

def get_connection():
    if uses_firebase() or os.environ.get("VERCEL"):
        raise RuntimeError("Direct SQL connections are unavailable with the Firebase backend.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(force_reseed=False):
    if uses_firebase():
        if force_reseed:
            raise RuntimeError("Demo data reset is disabled for the Firebase database.")
        initialize_firebase_data()
        return
    if os.environ.get("VERCEL"):
        raise RuntimeError(
            "Configure Firebase Admin credentials to use Firestore on Vercel."
        )

    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT DEFAULT 'Chief Pharmacist',
        avatar TEXT DEFAULT 'user-doctor',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        contact_email TEXT,
        phone TEXT,
        address TEXT
    );

    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        batch_number TEXT NOT NULL,
        category TEXT NOT NULL,
        manufacturer TEXT NOT NULL,
        supplier TEXT,
        quantity INTEGER NOT NULL DEFAULT 0,
        purchase_price REAL NOT NULL DEFAULT 0.0,
        selling_price REAL NOT NULL DEFAULT 0.0,
        manufacturing_date TEXT NOT NULL,
        expiry_date TEXT NOT NULL,
        minimum_stock INTEGER NOT NULL DEFAULT 10,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pharmacy_name TEXT DEFAULT 'Apex Medical Care & Pharmacy',
        expiry_warning_days INTEGER DEFAULT 30,
        low_stock_threshold INTEGER DEFAULT 15,
        currency_symbol TEXT DEFAULT '$',
        theme TEXT DEFAULT 'dark-glass',
        contact_email TEXT DEFAULT 'admin@apexmed.com',
        auto_alert INTEGER DEFAULT 1
    );
    ''')

    # Check if settings row exists
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (id, pharmacy_name, expiry_warning_days, low_stock_threshold, currency_symbol, theme, contact_email)
            VALUES (1, 'Apex Medical Care & Pharmacy', 30, 15, '$', 'dark-glass', 'admin@apexmed.com')
        ''')

    # Seed Default User if not exists
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    if (user_count == 0 or force_reseed) and not uses_firebase():
        cursor.execute("DELETE FROM users")
        # Default admin user: admin / admin123
        demo_pwd_hash = generate_password_hash("admin123", method="pbkdf2:sha256")
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", "admin@apexmed.com", demo_pwd_hash, "Dr. Alex Vance", "Chief Pharmacist"))

    # Seed Categories
    default_categories = [
        ("Antibiotics", "Broad and narrow spectrum bacterial infection treatments"),
        ("Pain Relief & Analgesics", "Fever, headache, inflammation, and pain management"),
        ("Cardiovascular & Hypertension", "Blood pressure, cardiac rhythm, and cholesterol control"),
        ("Respiratory & Anti-Allergy", "Antihistamines, bronchodilators, and asthma inhalers"),
        ("Diabetes & Endocrine", "Insulin, Metformin, and metabolic regulators"),
        ("Gastrointestinal", "Antacids, proton-pump inhibitors, and digestive aids"),
        ("Vitamins & Supplements", "Essential minerals, immunity boosters, and multivitamins"),
        ("Dermatology & Topicals", "Topical corticosteroids, antifungals, and antiseptics")
    ]
    for cat_name, cat_desc in default_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)", (cat_name, cat_desc))

    # Seed Suppliers
    default_suppliers = [
        ("Medix Global Pharma Distributors", "contact@medixpharma.com", "+1 (555) 234-5678", "450 Innovation Parkway, New Jersey"),
        ("Apex Bio-Health Supply Co.", "sales@apexbio.org", "+1 (555) 890-1234", "12 Healthcare Boulevard, Boston"),
        ("Novis Life Sciences Logistics", "orders@novislife.com", "+1 (555) 456-7890", "88 Zenith Drive, Chicago"),
        ("CureWell Wholesale Meds", "support@curewell.com", "+1 (555) 321-6540", "104 Gateway Plaza, Dallas")
    ]
    for sup_name, sup_email, sup_phone, sup_addr in default_suppliers:
        supplier = cursor.execute(
            "SELECT 1 FROM suppliers WHERE name = ?", (sup_name,)
        ).fetchone()
        if not supplier:
            cursor.execute('''
                INSERT INTO suppliers (name, contact_email, phone, address)
                VALUES (?, ?, ?, ?)
            ''', (sup_name, sup_email, sup_phone, sup_addr))

    # Seed Realistic Demo Medicines
    cursor.execute("SELECT COUNT(*) FROM medicines")
    med_count = cursor.fetchone()[0]

    if (med_count == 0 or force_reseed) and not uses_firebase():
        if force_reseed:
            cursor.execute("DELETE FROM medicines")
            cursor.execute("DELETE FROM alerts")

        today = datetime.date.today()

        # Helper to offset days from today
        def d(offset_days):
            return (today + datetime.timedelta(days=offset_days)).strftime("%Y-%m-%d")

        # Past offset for mfg
        def mfg(months_ago):
            return (today - datetime.timedelta(days=months_ago * 30)).strftime("%Y-%m-%d")

        demo_medicines = [
            # 1. EXPIRED MEDICINES
            (
                "Cetirizine Hydrochloride 10mg", "CTZ2025C02", "Respiratory & Anti-Allergy",
                "Cipla Ltd", "Medix Global Pharma Distributors", 80, 4.50, 8.50,
                mfg(14), d(-14), 20, "2nd generation antihistamine for allergic rhinitis. Store in a cool dry place."
            ),
            (
                "Amoxicillin & Clavulanate 625mg", "AUG2025X91", "Antibiotics",
                "GlaxoSmithKline", "Apex Bio-Health Supply Co.", 24, 12.00, 19.99,
                mfg(18), d(-5), 15, "Potent broad-spectrum antibacterial tablets for bacterial sinusitis and respiratory infections."
            ),
            (
                "Doxycycline Hyclate 100mg", "DOX2025A09", "Antibiotics",
                "Pfizer", "CureWell Wholesale Meds", 12, 8.20, 14.50,
                mfg(20), d(-32), 15, "Oral capsule tetracycline antibiotic for acne and bacterial infections."
            ),

            # 2. EXPIRING SOON MEDICINES (Within 30 days)
            (
                "Amoxicillin Trihydrate 250mg", "AMX2026B04", "Antibiotics",
                "Sun Pharma", "Apex Bio-Health Supply Co.", 18, 5.00, 9.50,
                mfg(12), d(7), 25, "Bactericidal penicillin antibiotic. Priority dispatch recommended before shelf expiry."
            ),
            (
                "Ciprofloxacin 500mg Film-Coated", "CIP2026D11", "Antibiotics",
                "Bayer Healthcare", "Medix Global Pharma Distributors", 35, 9.40, 16.00,
                mfg(10), d(16), 15, "Fluoroquinolone antibiotic for urinary tract and systemic bacterial infections."
            ),
            (
                "Salbutamol Inhaler 100mcg", "SLB2026M03", "Respiratory & Anti-Allergy",
                "Cipla Ltd", "Novis Life Sciences Logistics", 8, 14.00, 24.50,
                mfg(11), d(22), 10, "Rapid-acting beta-2 agonist bronchodilator aerosol for acute asthma attacks."
            ),
            (
                "Ibuprofen 400mg Softgels", "IBU2026G88", "Pain Relief & Analgesics",
                "Abbott Labs", "CureWell Wholesale Meds", 45, 6.20, 11.00,
                mfg(9), d(28), 20, "Non-steroidal anti-inflammatory drug (NSAID) for muscle aches, toothache, and fever."
            ),

            # 3. LOW STOCK ONLY (Safe expiry, but quantity <= minimum_stock)
            (
                "Insulin Glargine 100 IU/ml Pen", "INS2027K01", "Diabetes & Endocrine",
                "Sanofi Aventis", "Novis Life Sciences Logistics", 4, 38.50, 58.00,
                mfg(4), d(180), 12, "Long-acting basal recombinant human insulin analog. Must refrigerate at 2°C to 8°C."
            ),
            (
                "Atorvastatin Calcium 20mg", "ATV2027P05", "Cardiovascular & Hypertension",
                "Pfizer", "Medix Global Pharma Distributors", 7, 11.50, 21.00,
                mfg(5), d(320), 25, "HMG-CoA reductase inhibitor for lowering LDL cholesterol and cardiovascular risk."
            ),

            # 4. SAFE MEDICINES (Healthy stock & long shelf life)
            (
                "Paracetamol 500mg Tablets", "PCM2026A01", "Pain Relief & Analgesics",
                "GlaxoSmithKline", "Medix Global Pharma Distributors", 150, 2.10, 4.99,
                mfg(2), d(240), 30, "Fast-acting analgesic and antipyretic for mild-to-moderate pain and reduction of fever."
            ),
            (
                "Metformin Hydrochloride 500mg", "MET2027J14", "Diabetes & Endocrine",
                "Merck Serono", "Apex Bio-Health Supply Co.", 210, 3.80, 7.50,
                mfg(3), d(400), 40, "First-line biguanide oral antihyperglycemic medication for type 2 diabetes management."
            ),
            (
                "Pantoprazole Sodium 40mg Delayed-Release", "PAN2027R22", "Gastrointestinal",
                "Sun Pharma", "CureWell Wholesale Meds", 95, 7.00, 13.50,
                mfg(4), d(290), 20, "Proton pump inhibitor (PPI) for gastric acidity, GERD, and peptic ulcers."
            ),
            (
                "Azithromycin 500mg Tablets", "AZM2027L33", "Antibiotics",
                "Pfizer", "Novis Life Sciences Logistics", 65, 8.50, 15.20,
                mfg(3), d(310), 15, "Macrolide antibiotic for respiratory tract infections and acute bacterial exacerbations."
            ),
            (
                "Vitamin C + Zinc 500mg Chewables", "VIT2028Z01", "Vitamins & Supplements",
                "Bayer Healthcare", "Medix Global Pharma Distributors", 180, 5.20, 10.50,
                mfg(1), d(480), 25, "Immune system support dietary supplement with bioflavonoids."
            ),
            (
                "Hydrocortisone Cream 1% 30g", "HYD2027C19", "Dermatology & Topicals",
                "Johnson & Johnson", "Apex Bio-Health Supply Co.", 42, 6.80, 12.00,
                mfg(6), d(260), 15, "Mild corticosteroid topical soothing cream for eczema, dermatitis, and insect bites."
            )
        ]

        cursor.executemany('''
            INSERT INTO medicines (
                name, batch_number, category, manufacturer, supplier,
                quantity, purchase_price, selling_price, manufacturing_date,
                expiry_date, minimum_stock, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', demo_medicines)

        conn.commit()

    conn.commit()
    conn.close()

    # Regenerate alerts based on seeded data
    refresh_alerts()

def calculate_medicine_status(expiry_date_str, quantity, minimum_stock, warning_days=30):
    """
    Computes exact expiry status, stock status, remaining days, and badge metadata.
    """
    today = datetime.date.today()
    try:
        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {
            "status": "UNKNOWN",
            "days_remaining": 0,
            "badge_class": "badge-secondary",
            "badge_text": "UNKNOWN",
            "is_expired": False,
            "is_expiring_soon": False,
            "is_safe": False,
            "is_low_stock": False,
            "is_out_of_stock": False,
            "stock_status": "NORMAL"
        }

    delta_days = (expiry_date - today).days

    if delta_days < 0:
        status = "EXPIRED"
        badge_class = "badge-expired"
        badge_text = f"EXPIRED ({abs(delta_days)}d ago)"
        is_expired = True
        is_expiring_soon = False
        is_safe = False
    elif delta_days <= warning_days:
        status = "EXPIRING SOON"
        badge_class = "badge-expiring"
        badge_text = f"EXPIRING SOON ({delta_days}d left)"
        is_expired = False
        is_expiring_soon = True
        is_safe = False
    else:
        status = "SAFE"
        badge_class = "badge-safe"
        badge_text = f"SAFE ({delta_days}d left)"
        is_expired = False
        is_expiring_soon = False
        is_safe = True

    # Stock status
    if quantity <= 0:
        is_out_of_stock = True
        is_low_stock = True
        stock_status = "OUT OF STOCK"
    elif quantity <= minimum_stock:
        is_out_of_stock = False
        is_low_stock = True
        stock_status = "LOW STOCK"
    else:
        is_out_of_stock = False
        is_low_stock = False
        stock_status = "IN STOCK"

    return {
        "status": status,
        "days_remaining": delta_days,
        "badge_class": badge_class,
        "badge_text": badge_text,
        "is_expired": is_expired,
        "is_expiring_soon": is_expiring_soon,
        "is_safe": is_safe,
        "is_low_stock": is_low_stock,
        "is_out_of_stock": is_out_of_stock,
        "stock_status": stock_status
    }

def get_settings():
    if uses_firebase():
        row = _collection("settings").document("1").get()
        if row.exists:
            return row.to_dict()
        return _default_settings()

    conn = get_connection()
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return _default_settings()


def _default_settings():
    return {
        "id": 1,
        "pharmacy_name": "Apex Medical Care & Pharmacy",
        "expiry_warning_days": 30,
        "low_stock_threshold": 15,
        "currency_symbol": "$",
        "theme": "dark-glass",
        "contact_email": "admin@apexmed.com",
        "auto_alert": 1,
    }

def refresh_alerts():
    """
    Scans medicines and synchronizes the alerts table so that:
    - Expired medicines have EXPIRED alerts
    - Expiring soon medicines have EXPIRING_SOON alerts
    - Low stock medicines have LOW_STOCK alerts
    """
    if uses_firebase():
        warning_days = get_settings().get("expiry_warning_days", 30)
        medicines = get_medicines()
        existing_keys = {
            (str(row.get("medicine_id")), row.get("type"))
            for row in _firebase_documents("alerts")
        }
        needed = []
        for med in medicines:
            calc = calculate_medicine_status(
                med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
            )
            if calc["is_expired"]:
                needed.append((
                    med["id"], "EXPIRED",
                    f"{med['name']} (Batch: {med['batch_number']}) has EXPIRED "
                    f"({abs(calc['days_remaining'])} days ago). Quarantine immediately.",
                ))
            elif calc["is_expiring_soon"]:
                needed.append((
                    med["id"], "EXPIRING_SOON",
                    f"{med['name']} (Batch: {med['batch_number']}) expires in "
                    f"{calc['days_remaining']} days. Prioritize dispensing or initiate distributor return.",
                ))
            if calc["is_low_stock"]:
                needed.append((
                    med["id"], "LOW_STOCK",
                    f"Low stock alert: {med['name']} has only {med['quantity']} units remaining "
                    f"(Min threshold: {med['minimum_stock']}).",
                ))
        for medicine_id, alert_type, message in needed:
            if (str(medicine_id), alert_type) not in existing_keys:
                create_alert(medicine_id, alert_type, message)
        return

    conn = get_connection()
    settings = get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    medicines = conn.execute("SELECT * FROM medicines").fetchall()
    
    # Existing alerts dictionary: (medicine_id, type) -> id
    existing = conn.execute("SELECT id, medicine_id, type FROM alerts").fetchall()
    existing_keys = {(r["medicine_id"], r["type"]): r["id"] for r in existing}

    current_needed_alerts = set()

    for med in medicines:
        calc = calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        
        # Expired alert
        if calc["is_expired"]:
            msg = f"{med['name']} (Batch: {med['batch_number']}) has EXPIRED ({abs(calc['days_remaining'])} days ago). Quarantine immediately."
            current_needed_alerts.add((med["id"], "EXPIRED", msg))

        # Expiring soon alert
        elif calc["is_expiring_soon"]:
            msg = f"{med['name']} (Batch: {med['batch_number']}) expires in {calc['days_remaining']} days. Prioritize dispensing or initiate distributor return."
            current_needed_alerts.add((med["id"], "EXPIRING_SOON", msg))

        # Low stock alert
        if calc["is_low_stock"]:
            msg = f"Low stock alert: {med['name']} has only {med['quantity']} units remaining (Min threshold: {med['minimum_stock']})."
            current_needed_alerts.add((med["id"], "LOW_STOCK", msg))

    # Insert missing alerts
    for med_id, alert_type, msg in current_needed_alerts:
        if (med_id, alert_type) not in existing_keys:
            conn.execute('''
                INSERT INTO alerts (medicine_id, type, message, is_read)
                VALUES (?, ?, ?, 0)
            ''', (med_id, alert_type, msg))

    conn.commit()
    conn.close()


def create_alert(medicine_id, alert_type, message):
    if uses_firebase():
        alert_id = _firebase_next_id("alerts")
        _collection("alerts").document(str(alert_id)).set({
            "id": alert_id,
            "medicine_id": medicine_id,
            "type": alert_type,
            "message": message,
            "is_read": 0,
            "created_at": _timestamp(),
        })
        return alert_id
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO alerts (medicine_id, type, message, is_read) VALUES (?, ?, ?, 0)",
        (medicine_id, alert_type, message),
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id


def initialize_firebase_data():
    client = _firestore()
    settings_ref = client.collection("settings").document("1")
    if not settings_ref.get().exists:
        settings_ref.set(_default_settings())

    categories = [
        ("Antibiotics", "Broad and narrow spectrum bacterial infection treatments"),
        ("Pain Relief & Analgesics", "Fever, headache, inflammation, and pain management"),
        ("Cardiovascular & Hypertension", "Blood pressure, cardiac rhythm, and cholesterol control"),
        ("Respiratory & Anti-Allergy", "Antihistamines, bronchodilators, and asthma inhalers"),
        ("Diabetes & Endocrine", "Insulin, Metformin, and metabolic regulators"),
        ("Gastrointestinal", "Antacids, proton-pump inhibitors, and digestive aids"),
        ("Vitamins & Supplements", "Essential minerals, immunity boosters, and multivitamins"),
        ("Dermatology & Topicals", "Topical corticosteroids, antifungals, and antiseptics"),
    ]
    suppliers = [
        ("Medix Global Pharma Distributors", "contact@medixpharma.com", "+1 (555) 234-5678", "450 Innovation Parkway, New Jersey"),
        ("Apex Bio-Health Supply Co.", "sales@apexbio.org", "+1 (555) 890-1234", "12 Healthcare Boulevard, Boston"),
        ("Novis Life Sciences Logistics", "orders@novislife.com", "+1 (555) 456-7890", "88 Zenith Drive, Chicago"),
        ("CureWell Wholesale Meds", "support@curewell.com", "+1 (555) 321-6540", "104 Gateway Plaza, Dallas"),
    ]
    for name, description in categories:
        ref = client.collection("categories").document(name)
        if not ref.get().exists:
            ref.set({"name": name, "description": description})
    for name, email, phone, address in suppliers:
        ref = client.collection("suppliers").document(name)
        if not ref.get().exists:
            ref.set({"name": name, "contact_email": email, "phone": phone, "address": address})

    for collection_name in ("users", "medicines", "alerts"):
        counter_ref = client.collection("_counters").document(collection_name)
        if not counter_ref.get().exists:
            snapshots = client.collection(collection_name).stream()
            max_id = max((int(item.id) for item in snapshots if item.id.isdigit()), default=0)
            counter_ref.set({"value": max_id})


def _firebase_documents(collection_name):
    rows = []
    for snapshot in _collection(collection_name).stream():
        data = snapshot.to_dict() or {}
        data.setdefault("id", int(snapshot.id) if snapshot.id.isdigit() else snapshot.id)
        rows.append(data)
    return rows


def get_user_by_id(user_id):
    if uses_firebase():
        snapshot = _collection("users").document(str(user_id)).get()
        return ({"id": int(user_id), **snapshot.to_dict()} if snapshot.exists else None)
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_identity(identity):
    if uses_firebase():
        for field in ("username", "email"):
            result = _collection("users").where(field, "==", identity).limit(1).get()
            if result:
                snapshot = result[0]
                user = snapshot.to_dict() or {}
                user.setdefault("id", int(snapshot.id) if snapshot.id.isdigit() else snapshot.id)
                return user
        return None
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?", (identity, identity)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def find_user_conflict(username, email, exclude_id=None):
    if uses_firebase():
        for field, value in (("username", username), ("email", email)):
            matches = _collection("users").where(field, "==", value).limit(1).get()
            for snapshot in matches:
                user = snapshot.to_dict() or {}
                user_id = user.get("id", snapshot.id)
                if str(user_id) != str(exclude_id):
                    return True
        return False
    conn = get_connection()
    if exclude_id is None:
        row = conn.execute(
            "SELECT 1 FROM users WHERE username = ? OR email = ?", (username, email)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT 1 FROM users WHERE (username = ? OR email = ?) AND id != ?",
            (username, email, exclude_id),
        ).fetchone()
    conn.close()
    return row is not None


def create_user(user_data):
    if uses_firebase():
        client = _firestore()
        from firebase_admin import firestore

        normalized_keys = {
            hashlib.sha256(f"{field}:{user_data[field].strip().casefold()}".encode()).hexdigest()
            for field in ("username", "email")
        }
        user_id = _firebase_next_id("users")
        transaction = client.transaction()

        @firestore.transactional
        def reserve_keys(transaction):
            refs = [client.collection("_user_keys").document(key) for key in normalized_keys]
            if any(ref.get(transaction=transaction).exists for ref in refs):
                raise ValueError("Username or email already registered.")
            user_ref = client.collection("users").document(str(user_id))
            transaction.set(user_ref, {"id": user_id, **user_data})
            for ref in refs:
                transaction.set(ref, {"user_id": user_id})
            return user_id

        return reserve_keys(transaction)

    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO users (full_name, username, email, password_hash, role)
           VALUES (?, ?, ?, ?, ?)""",
        (
            user_data["full_name"], user_data["username"], user_data["email"],
            user_data["password_hash"], user_data.get("role", "Pharmacist"),
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def update_user(user_id, fields):
    if uses_firebase():
        ref = _collection("users").document(str(user_id))
        snapshot = ref.get()
        if not snapshot.exists:
            return False
        old = snapshot.to_dict()
        new_username = fields.get("username", old.get("username"))
        new_email = fields.get("email", old.get("email"))
        if find_user_conflict(new_username, new_email, user_id):
            raise ValueError("Username or email already registered.")
        if new_username != old.get("username") or new_email != old.get("email"):
            client = _firestore()
            for field, value in (("username", old.get("username")), ("email", old.get("email"))):
                key = hashlib.sha256(f"{field}:{value.strip().casefold()}".encode()).hexdigest()
                client.collection("_user_keys").document(key).delete()
            for field, value in (("username", new_username), ("email", new_email)):
                key = hashlib.sha256(f"{field}:{value.strip().casefold()}".encode()).hexdigest()
                client.collection("_user_keys").document(key).set({"user_id": int(user_id)})
        ref.update(fields)
        return True

    if "email" in fields:
        existing_user = get_user_by_id(user_id)
        if existing_user and find_user_conflict(
            existing_user["username"], fields["email"], user_id
        ):
            raise ValueError("Username or email already registered.")
    allowed = {"full_name", "email", "password_hash"}
    fields = {key: value for key, value in fields.items() if key in allowed}
    if not fields:
        return False
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn = get_connection()
    conn.execute(
        f"UPDATE users SET {assignments} WHERE id = ?",
        (*fields.values(), user_id),
    )
    conn.commit()
    conn.close()
    return True


def get_category_names():
    if uses_firebase():
        return sorted(
            (item["name"] for item in _firebase_documents("categories")),
            key=str.casefold,
        )
    conn = get_connection()
    rows = conn.execute("SELECT name FROM categories ORDER BY name ASC").fetchall()
    conn.close()
    return [row["name"] for row in rows]


def get_supplier_names():
    if uses_firebase():
        return sorted(
            (item["name"] for item in _firebase_documents("suppliers")),
            key=str.casefold,
        )
    conn = get_connection()
    rows = conn.execute("SELECT name FROM suppliers ORDER BY name ASC").fetchall()
    conn.close()
    return [row["name"] for row in rows]


def get_medicines(search="", category="", sort_by="expiry_asc"):
    if uses_firebase():
        rows = _firebase_documents("medicines")
        if search:
            term = search.casefold()
            rows = [
                row for row in rows
                if any(term in str(row.get(field, "")).casefold()
                       for field in ("name", "batch_number", "manufacturer"))
            ]
        if category:
            rows = [row for row in rows if row.get("category") == category]
        sort_fields = {
            "name_asc": ("name", False), "name_desc": ("name", True),
            "qty_desc": ("quantity", True), "qty_asc": ("quantity", False),
            "expiry_desc": ("expiry_date", True), "expiry_asc": ("expiry_date", False),
            "id_desc": ("id", True),
        }
        field, reverse = sort_fields.get(sort_by, ("expiry_date", False))
        return sorted(rows, key=lambda row: row.get(field) or (0 if field == "id" else ""), reverse=reverse)
    conn = get_connection()
    rows = conn.execute("SELECT * FROM medicines").fetchall()
    conn.close()
    result = [dict(row) for row in rows]
    if search:
        term = search.casefold()
        result = [
            row for row in result
            if any(term in str(row.get(field, "")).casefold()
                   for field in ("name", "batch_number", "manufacturer"))
        ]
    if category:
        result = [row for row in result if row.get("category") == category]
    sort_fields = {
        "name_asc": ("name", False), "name_desc": ("name", True),
        "qty_desc": ("quantity", True), "qty_asc": ("quantity", False),
        "expiry_desc": ("expiry_date", True), "expiry_asc": ("expiry_date", False),
        "id_desc": ("id", True),
    }
    field, reverse = sort_fields.get(sort_by, ("expiry_date", False))
    return sorted(result, key=lambda row: row.get(field) or (0 if field == "id" else ""), reverse=reverse)


def get_medicine(medicine_id):
    if uses_firebase():
        snapshot = _collection("medicines").document(str(medicine_id)).get()
        return {"id": int(medicine_id), **snapshot.to_dict()} if snapshot.exists else None
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_medicine(fields):
    if uses_firebase():
        medicine_id = _firebase_next_id("medicines")
        created = _timestamp()
        _collection("medicines").document(str(medicine_id)).set({
            "id": medicine_id, "created_at": created, "updated_at": created, **fields,
        })
        return medicine_id
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO medicines (
            name, batch_number, category, manufacturer, supplier, quantity,
            purchase_price, selling_price, manufacturing_date, expiry_date,
            minimum_stock, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        tuple(fields[key] for key in (
            "name", "batch_number", "category", "manufacturer", "supplier",
            "quantity", "purchase_price", "selling_price", "manufacturing_date",
            "expiry_date", "minimum_stock", "description",
        )),
    )
    conn.commit()
    medicine_id = cursor.lastrowid
    conn.close()
    return medicine_id


def update_medicine(medicine_id, fields):
    if uses_firebase():
        ref = _collection("medicines").document(str(medicine_id))
        if not ref.get().exists:
            return False
        ref.update({**fields, "updated_at": _timestamp()})
        return True
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn = get_connection()
    conn.execute(
        f"UPDATE medicines SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (*fields.values(), medicine_id),
    )
    conn.commit()
    conn.close()
    return True


def delete_medicine(medicine_id):
    medicine = get_medicine(medicine_id)
    if not medicine:
        return None
    if uses_firebase():
        _collection("medicines").document(str(medicine_id)).delete()
        for alert in _firebase_documents("alerts"):
            if str(alert.get("medicine_id")) == str(medicine_id):
                _collection("alerts").document(str(alert["id"])).delete()
        return medicine
    conn = get_connection()
    conn.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
    conn.commit()
    conn.close()
    return medicine


def get_alerts(alert_type=None, medicine_id=None):
    if uses_firebase():
        medicines_by_id = {
            str(row["id"]): row for row in _firebase_documents("medicines")
        }
        rows = _firebase_documents("alerts")
        if alert_type:
            rows = [row for row in rows if row.get("type") == alert_type]
        if medicine_id is not None:
            rows = [
                row for row in rows
                if str(row.get("medicine_id")) == str(medicine_id)
            ]
        for row in rows:
            medicine = medicines_by_id.get(str(row.get("medicine_id")), {})
            for field in ("name", "batch_number", "category", "expiry_date", "quantity"):
                row[f"medicine_{field}" if field == "name" else field] = medicine.get(field)
        rows.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        rows.sort(key=lambda row: bool(row.get("is_read")))
        return rows
    conn = get_connection()
    if medicine_id is not None:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE medicine_id = ? ORDER BY created_at DESC",
            (medicine_id,),
        ).fetchall()
    elif alert_type:
        rows = conn.execute(
            """SELECT a.*, m.name AS medicine_name, m.batch_number, m.category,
                      m.expiry_date, m.quantity
               FROM alerts a LEFT JOIN medicines m ON a.medicine_id = m.id
               WHERE a.type = ? ORDER BY a.is_read ASC, a.created_at DESC""",
            (alert_type,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT a.*, m.name AS medicine_name, m.batch_number, m.category,
                      m.expiry_date, m.quantity
               FROM alerts a LEFT JOIN medicines m ON a.medicine_id = m.id
               ORDER BY a.is_read ASC, a.created_at DESC"""
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_alert(alert_id):
    if uses_firebase():
        snapshot = _collection("alerts").document(str(alert_id)).get()
        return {"id": int(alert_id), **snapshot.to_dict()} if snapshot.exists else None
    conn = get_connection()
    row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def count_alerts(unread_only=False):
    if uses_firebase():
        rows = _firebase_documents("alerts")
        return sum(not row.get("is_read", 0) for row in rows) if unread_only else len(rows)
    conn = get_connection()
    where = " WHERE is_read = 0" if unread_only else ""
    count = conn.execute(f"SELECT COUNT(*) FROM alerts{where}").fetchone()[0]
    conn.close()
    return count


def set_alert_read(alert_id):
    if uses_firebase():
        ref = _collection("alerts").document(str(alert_id))
        if ref.get().exists:
            ref.update({"is_read": 1})
    else:
        conn = get_connection()
        conn.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()


def mark_all_alerts_read():
    if uses_firebase():
        _commit_firestore_batches(
            lambda batch, snapshot: batch.update(snapshot.reference, {"is_read": 1}),
            _collection("alerts").stream(),
        )
    else:
        conn = get_connection()
        conn.execute("UPDATE alerts SET is_read = 1")
        conn.commit()
        conn.close()


def delete_alert(alert_id):
    if uses_firebase():
        _collection("alerts").document(str(alert_id)).delete()
    else:
        conn = get_connection()
        conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()


def clear_alerts():
    if uses_firebase():
        _commit_firestore_batches(
            lambda batch, snapshot: batch.delete(snapshot.reference),
            _collection("alerts").stream(),
        )
    else:
        conn = get_connection()
        conn.execute("DELETE FROM alerts")
        conn.commit()
        conn.close()


def update_settings(fields):
    if uses_firebase():
        _collection("settings").document("1").set(fields, merge=True)
        return
    assignments = ", ".join(f"{key} = ?" for key in fields)
    conn = get_connection()
    conn.execute(
        f"UPDATE settings SET {assignments} WHERE id = 1", tuple(fields.values())
    )
    conn.commit()
    conn.close()


def _commit_firestore_batches(add_operation, snapshots):
    client = _firestore()
    batch = client.batch()
    operation_count = 0
    for snapshot in snapshots:
        add_operation(batch, snapshot)
        operation_count += 1
        if operation_count == 450:
            batch.commit()
            batch = client.batch()
            operation_count = 0
    if operation_count:
        batch.commit()


def reset_demo_data():
    if uses_firebase():
        raise RuntimeError("Demo data reset is disabled for the Firebase database.")
    init_db(force_reseed=True)


def import_sqlite_database(sqlite_path, overwrite=False):
    if not uses_firebase():
        raise RuntimeError("Configure Firebase credentials before importing data.")
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    client = _firestore()
    collection_names = ("users", "categories", "suppliers", "medicines", "alerts", "settings")
    imported_counts = {}
    max_ids = {}

    try:
        for collection_name in collection_names:
            rows = source.execute(f"SELECT * FROM {collection_name}").fetchall()
            imported_counts[collection_name] = 0
            max_id = 0
            for row in rows:
                record = dict(row)
                record_id = record.pop("id", None)
                if (
                    collection_name == "users"
                    and record.get("username") == "admin"
                    and record.get("email") == "admin@apexmed.com"
                ):
                    continue
                if collection_name == "settings":
                    document_id = "1"
                elif collection_name in ("categories", "suppliers"):
                    document_id = str(record["name"])
                else:
                    document_id = str(record_id)
                target = client.collection(collection_name).document(document_id)
                if target.get().exists and not overwrite:
                    continue
                if collection_name == "settings":
                    record["id"] = 1
                elif record_id is not None:
                    record["id"] = int(record_id)
                    max_id = max(max_id, int(record_id))
                target.set(record)
                imported_counts[collection_name] += 1
            if collection_name in ("users", "medicines", "alerts"):
                max_ids[collection_name] = max_id

        for collection_name, max_id in max_ids.items():
            counter_ref = client.collection("_counters").document(collection_name)
            current = counter_ref.get()
            current_max = current.get("value") if current.exists else 0
            counter_ref.set({"value": max(max_id, current_max)})
        for user in _firebase_documents("users"):
            for field in ("username", "email"):
                value = user.get(field)
                if value:
                    key = hashlib.sha256(f"{field}:{value.strip().casefold()}".encode()).hexdigest()
                    client.collection("_user_keys").document(key).set({"user_id": user["id"]})
    finally:
        source.close()

    return imported_counts


if __name__ == "__main__":
    init_db(force_reseed=True)
    print("Database initialized and seeded successfully.")
