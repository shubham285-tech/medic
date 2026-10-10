# Product Requirements Document (PRD)
## Medical Expiry Tracker – 3D Modern Medical Inventory & Expiry Management System

---

### 1. Product Overview
**Medical Expiry Tracker** is an enterprise-grade, modern healthcare web application designed specifically for pharmacies, hospital dispensaries, clinics, medical shops, and medical inventory managers. It provides intelligent tracking of medicine stocks, real-time calculation of drug expiry dates, visual status indicators (Safe, Expiring Soon, Expired), automated low-stock warnings, proactive expiry alerts, detailed analytical reporting, and comprehensive inventory management wrapped in a modern 3D glassmorphic user interface.

### 2. Problem Statement
Every year, pharmacies and healthcare facilities discard billions of dollars worth of medicines due to undetected expiration, or worse, risk patient safety by inadvertently dispensing expired or degraded drugs. Traditional inventory tracking methods rely on error-prone paper ledgers, fragmented spreadsheets, or outdated, unintuitive legacy ERP software. 

Key challenges faced by medical facilities:
- Inability to quickly identify medicines expiring within 15, 30, or 60 days.
- Financial losses caused by unsellable expired inventory that could have been returned to distributors or prioritized for sale.
- Compliance and legal penalties from healthcare authorities for stocking expired pharmaceuticals.
- Frequent stockouts of critical life-saving medications due to lack of minimum threshold tracking.
- Cumbersome user interfaces that require extensive technical training.

### 3. Target Users & User Personas

| Persona | Role | Context & Objectives | Key Needs |
| :--- | :--- | :--- | :--- |
| **Rajesh Kumar** | Community Pharmacy Owner | Operates a high-volume retail pharmacy with 3,000+ SKUs. Needs to minimize financial write-offs and manage distributor returns. | Fast batch search, 30-day expiry heads-up, quick CSV/PDF export for auditing. |
| **Sarah Jenkins** | Hospital Dispensary Manager | Manages drug stocks across emergency and outpatient units in a busy clinic/hospital. | Real-time low-stock alerts, category-wise tracking, strict batch validation. |
| **Amit Verma** | Medical Store Assistant | Responsible for daily shelf stocking, receiving supplier deliveries, and physical inventory checks. | Intuitive 1-click medicine entry, mobile-responsive barcode/batch scanner view, clear color-coded badges. |
| **Dr. Elena Rostova** | Private Clinic Administrator | Manages a specialized pediatric and dermatology clinic with sensitive biologicals and vaccines. | Urgent alerts for short shelf-life drugs, detailed history, simple non-technical dashboard. |

### 4. Goals & Non-Goals
#### 4.1 Goals
- Provide zero-latency visibility into medicine status: **SAFE**, **EXPIRING SOON**, and **EXPIRED**.
- Automatically compute remaining days to expiry against current calendar date and configurable warning thresholds.
- Alert staff proactively to low-stock thresholds to prevent stockouts of vital medication.
- Deliver a state-of-the-art 3D healthcare SaaS UI that eliminates friction and delights users.
- Provide exportable audit reports (CSV, printable PDF format) for regulatory compliance and distributor returns.
- Enable instantaneous search, multi-facet filtering (category, status, supplier, manufacturer, date range), and rapid batch lookup.

#### 4.2 Non-Goals
- Direct integration with national e-prescription APIs (reserved for v2.0).
- Multi-warehouse cross-docking logistics (this version focuses on store/hospital unit inventory).
- POS credit card hardware processing (focus is strictly on inventory and expiry governance).

### 5. Functional Requirements

#### 5.1 Authentication & Security
- Secure session-based authentication with password hashing using PBKDF2 / SHA-256 via Werkzeug.
- Dedicated Login view featuring 3D interactive hero visuals, "Remember Me" toggle, and responsive input validation.
- Forgot Password flow UI with simulated token/security verification.
- Route protection decorator ensuring unauthenticated users cannot access sensitive inventory records.

#### 5.2 Interactive Dashboard
- **Top Metrics Overview Cards** with 3D depth and subtle floating animations:
  - Total Medicines (Count of unique drug batches)
  - Total Stock Units (Aggregate physical inventory)
  - Expiring Soon Count (Drugs within threshold days)
  - Expired Medicines Count (Urgent disposal candidates)
  - Safe Medicines Count
  - Low Stock Medicines Count (Quantity $\le$ Minimum Stock Threshold)
- **Interactive Visual Charts** (Powered by Chart.js):
  - Expiry Status Distribution (Doughnut chart with status palette)
  - Monthly Expiry Timeline (Bar chart showing impending expirations by month)
  - Stock Breakdown by Category (Polar/Doughnut distribution)
- **Live Alert Feed**: Immediate view of highest-urgency drug alerts.
- **Recently Added Batches**: Quick table of latest inventory entries.

#### 5.3 Medicine Inventory Management (CRUD)
- **Inventory Data Fields**:
  - `id`: Unique Auto-increment Primary Key
  - `name`: Commercial & Generic Name (e.g., Paracetamol 500mg)
  - `batch_number`: Manufacturer Lot/Batch identifier (Required, Unique per manufacturer)
  - `category`: Therapeutic classification (Pain Relief, Antibiotics, Cardiovascular, etc.)
  - `manufacturer`: Pharmaceutical producer (e.g., GlaxoSmithKline, Pfizer, Sun Pharma)
  - `supplier`: Distributor or wholesale vendor
  - `quantity`: Current units in stock (Integer $\ge$ 0)
  - `purchase_price`: Unit acquisition cost (Decimal $\ge$ 0)
  - `selling_price`: Unit retail price (Decimal $\ge$ 0)
  - `manufacturing_date`: Production date (YYYY-MM-DD)
  - `expiry_date`: Official expiration date (YYYY-MM-DD, must be > manufacturing_date)
  - `minimum_stock`: Threshold for triggering Low Stock warning (Integer $\ge$ 1)
  - `description`: Usage instructions, storage conditions (e.g., "Store below 25°C"), or notes
- **Actions**:
  - Add New Medicine Form with live client and server validation.
  - Edit Medicine Form with pre-populated values.
  - Delete Medicine with confirmation modal safeguards.
  - Quick View Medicine Details Modal showing complete metadata, remaining days counter, and status badges.

#### 5.4 Automated Business Logic & Status Calculation
- **Expiry Status Logic**:
  - Today = Current Date ($T$)
  - Expiry Date = $E$
  - Threshold = Configurable warning period $W$ (Default: 30 days)
  - If $E < T$: Status is **EXPIRED** (Badge: Crimson Red #EF4444).
  - If $T \le E \le (T + W\text{ days})$: Status is **EXPIRING SOON** (Badge: Amber Warning #F59E0B).
  - If $E > (T + W\text{ days})$: Status is **SAFE** (Badge: Emerald Green #10B981).
- **Stock Status Logic**:
  - If $\text{Quantity} \le \text{Minimum Stock}$: Flag as **LOW STOCK** (Badge: Coral / Orange).
  - If $\text{Quantity} == 0$: Flag as **OUT OF STOCK**.

#### 5.5 Advanced Search, Filtering & Sorting
- Real-time text search across Medicine Name, Generic Name, and Batch Number.
- Dropdown filters for:
  - Category (All, Antibiotics, Pain Relief, Cardiology, etc.)
  - Expiry Status (All, Safe, Expiring Soon, Expired)
  - Stock Status (All, Normal, Low Stock, Out of Stock)
  - Manufacturer / Supplier
- Multi-column sorting (Name, Expiry Date, Quantity, Price).

#### 5.6 Expiry Alerts & Notification Center
- Dedicated Alerts view and top navigation notification dropdown with unread badge counter.
- Automated system alert generator based on batch status.
- Alert actions: Mark as Read, Mark All as Read, View Medicine, and Dismiss/Delete Alert.

#### 5.7 Reports & Data Export
- Pre-built segmented reports:
  - Expired Medicines Audit (Disposal / write-off report)
  - Expiring Soon Inventory (Distributor return & priority clearance list)
  - Current Comprehensive Stock Valuation
  - Low Stock Reorder List
  - Category-wise Distribution Breakdown
- Export capabilities:
  - **CSV Export**: Instant download of raw inventory data.
  - **Printable / PDF Preview**: Clean, printable stylesheet with print headers and barcode-friendly layout.

#### 5.8 System Settings & Customization
- User profile display and update.
- Configurable **Expiry Warning Period** (e.g., 15, 30, 60, 90 days; default 30 days).
- Configurable **Global Low-Stock Threshold** default.
- UI Theme Preferences (Dark / Modern Glassmorphism).
- Database reset / demo data repopulation utility for testing.

---

### 6. Non-Functional Requirements
- **Performance**: Page load times under 300ms; sub-50ms query execution on SQLite index.
- **Visual Design**: Premium 3D healthcare aesthetics with glassmorphic cards, layered depth, CSS 3D transforms, vibrant medical palettes, and micro-interactions.
- **Responsiveness**: Flawless experience across Ultra-wide monitors (1920px+), Laptops (1366px), Tablets (768px-1024px), and Mobile devices (360px-480px).
- **Accessibility & UX**: High color contrast ratios (WCAG AA compliant), clear typographic hierarchy, intuitive keyboard navigation, and descriptive empty/loading states.
- **Reliability & Data Integrity**: Foreign key constraints, atomic transactions, and zero data loss on restart.

---

### 7. User Stories & Acceptance Criteria

#### US-1: Add Medicine with Expiry Validation
- **As a** pharmacy staff member,
- **I want to** register a new batch of Amoxicillin with manufacturing and expiry dates,
- **So that** the inventory system can track its longevity and notify me before it expires.
- **Acceptance Criteria**:
  - System rejects form if Expiry Date $\le$ Manufacturing Date with an inline error message.
  - System checks that Quantity and Prices are non-negative.
  - Upon submission, medicine is stored in SQLite and immediately reflects in Inventory and Dashboard.

#### US-2: Real-time Expiry Status Tracking
- **As an** inventory manager,
- **I want to** immediately spot medicines expiring within 30 days,
- **So that** I can discount them or return them to the distributor for full credit.
- **Acceptance Criteria**:
  - Medicines with expiry between today and +30 days display an amber "EXPIRING SOON" badge with exact days remaining (e.g., "16 days left").
  - Medicines with expiry past today display a bold red "EXPIRED" badge with days overdue.

#### US-3: Low Stock Warning
- **As a** dispensary manager,
- **I want to** see an alert when emergency drugs fall below their minimum safety stock,
- **So that** patients never face life-threatening drug shortages.
- **Acceptance Criteria**:
  - When medicine quantity $\le$ minimum_stock, a prominent "LOW STOCK" badge is displayed.
  - Dashboard Low Stock metric increments automatically.

---

### 8. Success Metrics
1. **Zero Expired Medication Dispensed**: 100% detection rate of expiring/expired items.
2. **Reduced Wastage**: 40% reduction in discarded inventory due to early 30-day return alerts.
3. **Speed to Onboard**: New pharmacy staff can add, search, and audit medicines within 2 minutes of first login.
4. **Zero Stockout Incidents**: Timely reorders driven by minimum stock alerts.
