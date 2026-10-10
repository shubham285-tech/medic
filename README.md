# Medical Expiry Tracker – 3D Modern Medical Inventory & Expiry Management System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![SQLite 3](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![UI Style](https://img.shields.io/badge/UI-3D%20Glassmorphism-06B6D4.svg)]()

> A modern, responsive healthcare web application engineered for pharmacies, hospital dispensaries, clinics, and medical store managers to track pharmaceuticals, calculate real-time drug expiry, detect stock depletion, and receive automated clinical alerts before products expire.

---

## 🌟 Key Highlights & Features

- **3D Modern Healthcare Aesthetics**: Custom CSS 3D perspectives, interactive 3D medicine capsule hero visualization, ambient mesh glow, glassmorphic frosted cards, and micro-interactions.
- **Dynamic Real-Time Expiry Engine**: Calculates exact remaining days to expiry automatically against the system date:
  - 🟢 **SAFE**: Beyond warning threshold days.
  - 🟡 **EXPIRING SOON**: Within configurable threshold window (default: 30 days) with countdown badges.
  - 🔴 **EXPIRED**: Past expiry date with immediate quarantine warnings.
- **Low Stock & Depletion Surveillance**: Automatically flags batches when `Quantity <= Minimum Stock Level` and generates reorder alerts.
- **Interactive Analytics Dashboard**:
  - Live 3D metric cards (Total Batches, Total Units, Expiring Soon, Expired, Safe, Low Stock).
  - Visual charts powered by **Chart.js**: Expiry distribution doughnut chart and monthly expiry forecast timeline.
  - Urgent live alert notifications and recently registered batch activity feed.
- **Full Medicine Inventory CRUD**:
  - Add, edit, delete, and inspect medicine batches.
  - Live input validation enforcing clinical business rules (e.g. Expiry Date > Manufacturing Date, non-negative quantities and pricing).
  - Quick inspection modal with complete pharmaceutical metadata, profit margins, and storage instructions.
- **Instant Search & Multi-Faceted Filters**:
  - Instant search across Medicine Name, Batch Number, and Manufacturer.
  - Category, Expiry Status, and Stock Level multi-filters.
  - Multi-column sorting (soonest expiry, quantity, name).
- **Audit & Regulatory Reports Studio**:
  - Filterable reports: Expiring Soon, Expired Disposal Audit, Low Stock Reorder List, and Full Inventory Valuation.
  - Instant RFC-4180 compliant **CSV Export**.
  - **Printable / PDF-Ready View** with official pharmaceutical audit signature blocks.
- **Configurable Settings**:
  - Adjustable expiry warning window (e.g. 15, 30, 45, 60 days).
  - Global low-stock threshold configuration.
  - User profile management with secure password hashing.
  - One-click demo database restoration.

---

## 🛠️ Technology Stack

- **Frontend**: Semantic HTML5, Vanilla CSS3 (3D Transforms, Glassmorphism, CSS Custom Properties), Vanilla JavaScript (ES6+ modular, responsive drawer, modal loader, AJAX toast notifications).
- **Data Visualizations**: [Chart.js](https://www.chart.js/) for responsive, hardware-accelerated clinical analytics.
- **Backend**: Python 3.11 + Flask 3.1.
- **Authentication & Security**: Werkzeug cryptographic password hashing (PBKDF2-SHA256), session hardening (`HttpOnly`, `SameSite`), parameterized SQL queries preventing injection, and `@login_required` route decorators.
- **Database**: SQLite 3 locally and Firebase Cloud Firestore in production.

---

## 📁 Project Structure

```
medical-expiry-tracker/
│
├── app.py                     # Main Flask web application & API controllers
├── db.py                      # Database schema, seeding engine, & status calculator
├── requirements.txt           # Project Python dependencies
├── vercel.json                # Vercel function configuration
│
├── prd.md                     # Product Requirements Document
├── Architecture.md            # System Architecture & Mermaid Diagrams
├── rules.md                   # Development & Business Rules
├── phases.md                  # Development Roadmap & Implementation Phases
├── design.md                  # UI/UX Design System Specification
├── flow.md                    # User Flows & Sequence Diagrams
│
├── templates/
│   ├── base.html              # Master layout with responsive sidebar & top-bar
│   ├── login.html             # Login/Register view with 3D medicine hero scene
│   ├── dashboard.html         # Analytics dashboard with 3D KPI cards & charts
│   ├── medicines.html         # Main inventory grid with live filtering & actions
│   ├── add_medicine.html      # Add medicine batch form with validation
│   ├── edit_medicine.html     # Edit medicine batch form
│   ├── medicine_details.html  # Comprehensive medicine dossier modal/page
│   ├── alerts.html            # Expiry & stock alerts management center
│   ├── reports.html           # Reports studio with CSV export
│   ├── reports_print.html     # Clean printable/PDF audit report view
│   └── settings.html          # Configuration & warning threshold settings
│
├── public/
│   └── static/
│       ├── css/
│       │   └── style.css      # Core 3D glassmorphic styling & responsive rules
│       └── js/
│           ├── app.js         # Global 3D card tilts, modals, & AJAX handlers
│           ├── dashboard.js  # Chart.js analytics charts controller
│           └── validation.js # Live form validation enforcing business rules
│
└── README.md                  # System overview & execution guide
```

---

## 🚀 Getting Started (Run Locally)

### 1. Prerequisites
- Python 3.10+ (Python 3.11 recommended) or `uv` package manager.

### 2. Setup Virtual Environment & Install Dependencies
Open your terminal (PowerShell, Command Prompt, or Bash) in the project directory:

```bash
# Using python directly:
python -m venv .venv

# Activate the virtual environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install dependencies:
pip install -r requirements.txt
```

*(Alternatively, if using `uv`)*:
```bash
uv venv .venv
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

### 3. Initialize Database & Seed Realistic Demo Data
The system automatically initializes and seeds realistic clinical data on first run. To manually seed or re-seed:
```bash
python db.py
```

### 4. Run the Web Application
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Credentials

These credentials are for local development only. Vercel deployments do not create a default demo account; register your first account from the login page.

| Field | Value |
| :--- | :--- |
| **Username** | `admin` |
| **Password** | `admin123` |
| **Role** | Chief Pharmacist |

*(Note: The login page includes a **"Auto Fill"** button that automatically inputs demo credentials for quick access.)*

---

## ☁️ Deploy to Vercel with Firebase Firestore

Production uses Firebase Cloud Firestore. The local `database.db` remains for local development and is intentionally excluded from Git. Firestore collections are initialized automatically; no demo login or medicines are added to a new Firebase project.

1. Create a Firebase project in the [Firebase Console](https://console.firebase.google.com/).
2. Create a **Cloud Firestore** database in **production mode**. Choose a nearby region; Firestore's location cannot be changed later.
3. In Google Cloud Console for that project, create a service account with the **Cloud Datastore User** role and generate a JSON key. Keep the key private.
4. Import this GitHub repository into Vercel. Vercel detects the Flask application in `app.py`.
5. Add these Vercel environment variables for Production:
   - `FIREBASE_PROJECT_ID` — the Firebase project ID.
   - `FIREBASE_SERVICE_ACCOUNT_KEY` — the complete service-account JSON as one environment-variable value.
   - `SECRET_KEY` — generate a long random value locally: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
6. Redeploy after saving the variables. Register the first account from the deployed login page.

Never commit or share the service-account key or secret key. The server uses Firebase Admin credentials; do not use a client-side Firebase API key for database access.

### Import existing SQLite data

To copy local users (password hashes), inventory, alerts, categories, suppliers, and settings into a new Firestore database:

1. Back up `database.db` and create the Firebase project, Firestore database, and service-account key described above.
2. In PowerShell, set the local credentials for the migration process (use the actual file location and project ID):
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account.json"
   $env:FIREBASE_PROJECT_ID = "your-firebase-project-id"
   .\.venv\Scripts\python.exe migrate_to_firebase.py
   ```
3. Review the imported document counts. Then add the Vercel environment variables and deploy.

The importer skips destination documents that already exist and excludes the built-in `admin` / `admin123` demo account for security. Run it against a fresh Firestore database before deploying the app; register a new account after deployment if there are no other imported users. Back up `database.db`; do not upload the database or service-account JSON to GitHub.

---

## 🧪 Acceptance Testing Checklist

- [x] **Authentication**: Secure login, session persistence, logout, registration, and protected routes.
- [x] **3D Dashboard**: Live KPI cards (Total Medicines, Stock Units, Expiring Soon, Expired, Safe, Low Stock) and responsive Chart.js visualizations.
- [x] **Inventory Management**: Complete CRUD (Create, Read, Update, Delete) with batch search, category filters, and sorting.
- [x] **Automatic Expiry Logic**: Dynamic calculation based on system date and configurable warning thresholds (default: 30 days).
- [x] **Visual Status Differentiation**: Distinct color palettes and badges for **SAFE**, **EXPIRING SOON**, **EXPIRED**, and **LOW STOCK**.
- [x] **Clinical Validation**: Rejection of expiry dates occurring before manufacturing dates, and non-negative constraints on quantities and prices.
- [x] **Alert Center**: Automated notifications for expired, expiring, and low-stock batches with 1-click "Mark as Read" and dismissal.
- [x] **Reports & Exports**: Filtered audit tables with instant RFC-4180 **CSV Export** and **Printable / PDF** views.
- [x] **Responsive Design**: Tested across Desktop, Tablet, and Mobile viewports with collapsible sidebar navigation and responsive table-to-card transformations.
