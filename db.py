import os
import sqlite3
import datetime
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", "database.db")


def uses_remote_database():
    return bool(os.environ.get("TURSO_DATABASE_URL"))

def get_connection():
    database_url = os.environ.get("TURSO_DATABASE_URL")
    auth_token = os.environ.get("TURSO_AUTH_TOKEN")

    if database_url or auth_token:
        if not database_url or not auth_token:
            raise RuntimeError(
                "Both TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be configured."
            )

        import turso_serverless

        conn = turso_serverless.connect(database_url, auth_token=auth_token)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    if os.environ.get("VERCEL"):
        raise RuntimeError(
            "Configure TURSO_DATABASE_URL and TURSO_AUTH_TOKEN for Vercel deployments."
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(force_reseed=False):
    if force_reseed and uses_remote_database():
        raise RuntimeError("Demo data reset is disabled for the persistent database.")

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
    if (user_count == 0 or force_reseed) and not uses_remote_database():
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

    if (med_count == 0 or force_reseed) and not uses_remote_database():
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
    conn = get_connection()
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "pharmacy_name": "Apex Medical Care & Pharmacy",
        "expiry_warning_days": 30,
        "low_stock_threshold": 15,
        "currency_symbol": "$",
        "theme": "dark-glass",
        "contact_email": "admin@apexmed.com",
        "auto_alert": 1
    }

def refresh_alerts():
    """
    Scans medicines and synchronizes the alerts table so that:
    - Expired medicines have EXPIRED alerts
    - Expiring soon medicines have EXPIRING_SOON alerts
    - Low stock medicines have LOW_STOCK alerts
    """
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

if __name__ == "__main__":
    init_db(force_reseed=True)
    print("Database initialized and seeded successfully.")
