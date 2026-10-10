# Development and Business Rules
## Medical Expiry Tracker – 3D Modern Medical Inventory & Expiry Management System

---

### 1. Mandatory Business Rules
1. **Expiry Date Chronology**: The expiry date (`expiry_date`) must always be strictly greater than or equal to the manufacturing date (`manufacturing_date`). Submissions violating this rule must be rejected on both client-side and server-side.
2. **Non-Negative Quantities**: Physical medicine stock count (`quantity`) must be an integer $\ge 0$. Stock can never be negative.
3. **Non-Negative Pricing**: Both Purchase Price (`purchase_price`) and Selling Price (`selling_price`) must be decimal values $\ge 0.00$.
4. **Mandatory Identity**: `name` (Medicine Name) and `batch_number` (Manufacturer Batch / Lot Number) are strictly required.
5. **Batch Number Integrity**: Batch numbers must be trimmed of surrounding whitespace and formatted consistently.
6. **Automatic Dynamic Status**: Expiry status must **never** be manually edited by users. It is computed deterministically in real time based on system date and user warning thresholds.
7. **Visual Severity Differentiation**:
   - **EXPIRED**: Must be styled with high-priority crimson red badges, distinct alert banners, and visual urgency tags.
   - **EXPIRING SOON**: Must be prominently marked with amber/warning badges displaying exact remaining days.
   - **SAFE**: Must display crisp emerald green badges.
8. **Automated Alert Generation**: Adding or viewing an inventory item that is Expiring Soon or Expired must automatically ensure a corresponding notification exists in the Alert Center.
9. **Low Stock Detection**: When `quantity <= minimum_stock`, the application must flag the batch as **LOW STOCK** and increment the dashboard low-stock counter. If `quantity == 0`, it must be flagged as **OUT OF STOCK**.
10. **Route Authentication Lockdown**: All core pages (`/dashboard`, `/medicines`, `/add`, `/edit`, `/alerts`, `/reports`, `/settings`) require an active authenticated user session. Unauthenticated access attempts redirect to `/login` with an informative flash message.

---

### 2. Coding & Implementation Rules

#### 2.1 Python / Flask Backend
- **PEP 8 Compliance**: Follow Python standard naming conventions (`snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants).
- **Parameterized SQL Queries**: Absolutely no raw string concatenation or f-strings for SQL query construction. Always use `?` placeholders.
- **Transactional Safety**: Always use Python database context managers or explicit `try...except...finally` blocks with `db.commit()` and `db.rollback()`.
- **Date Handling**: Treat all dates as ISO-8601 (`YYYY-MM-DD`). Always use `datetime.date.today()` as the evaluation anchor.
- **Modular Route Functions**: Route functions must remain lean; complex calculations (e.g., expiry evaluation, alert consolidation) must be encapsulated in helper functions.

#### 2.2 Frontend (HTML5, CSS3, JavaScript)
- **Modern Vanilla Web Technologies**:
  - No massive JavaScript frameworks (keep it pure, high-performance, modular ES6+).
  - Modern Vanilla CSS3 with CSS Custom Properties (Variables) for theming, typography, shadows, and color scales.
  - Strict semantic HTML5 (`<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`).
- **Interactive Visuals (Chart.js)**:
  - Chart instances must be properly created, styled to match the dark/light medical palette, and cleanly destroyed/re-instantiated if re-rendered.
- **Component Modularity**:
  - CSS components must be reusable (`.btn`, `.badge`, `.glass-card`, `.stat-card-3d`, `.table-container`).

---

### 3. UI/UX Design Rules
1. **Premium 3D & Glassmorphic Look**:
   - Use subtle backdrop blurs (`backdrop-filter: blur(12px)`), multi-layered soft drop shadows, and subtle translucent border highlights (`border: 1px solid rgba(255, 255, 255, 0.15)`).
   - Use CSS 3D perspectives (`perspective: 1000px`) and smooth hover tilts for dashboard stat cards.
2. **Typography**: Use modern Google Fonts (`Outfit` or `Inter`) with clear hierarchy, comfortable line-heights, and crisp font weights.
3. **No Placeholders or Broken Elements**: Every button, modal trigger, filter dropdown, and export action must be fully wired up and functional.
4. **Empty States**: If a table, search result, or alert list is empty, display a branded empty state with an icon, explanatory text, and a call-to-action button (e.g., "Add your first medicine").
5. **Micro-interactions**: Hover transitions on buttons, cards, and navigation links must use smooth easing (`transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1)`).

---

### 4. Validation Rules

| Field | Client Validation | Server Validation | Error Message |
| :--- | :--- | :--- | :--- |
| `name` | `required`, minlength 2 | `not empty`, stripped | "Medicine name is required." |
| `batch_number` | `required`, alphanumeric | `not empty`, stripped | "Batch number is required." |
| `category` | `required` select | valid category string | "Please select a category." |
| `quantity` | `min="0"`, integer | `int >= 0` | "Quantity must be 0 or greater." |
| `purchase_price` | `min="0"`, step="0.01" | `float >= 0.0` | "Purchase price cannot be negative." |
| `selling_price` | `min="0"`, step="0.01" | `float >= 0.0` | "Selling price cannot be negative." |
| `manufacturing_date`| `required`, date format | valid YYYY-MM-DD | "Invalid manufacturing date." |
| `expiry_date` | `required`, date $\ge$ mfg | valid date $\ge$ mfg | "Expiry date must be after manufacturing date." |
| `minimum_stock` | `min="1"`, integer | `int >= 1` | "Minimum stock must be at least 1." |

---

### 5. Security Rules
- **Password Hashes**: Store passwords hashed using `generate_password_hash(password, method='pbkdf2:sha256')`.
- **Session Protection**: Flask secret key must be set to a secure 32-byte hexadecimal string.
- **CSRF & Input Sanitization**: Clean all inputs against whitespace and potential script injection.
- **Safe Error Messaging**: Never leak database tracebacks or raw database schema in user flash messages. Provide friendly, actionable feedback.

---

### 6. Responsive Design Rules
- **Breakpoints**:
  - Mobile: `< 768px` (Sidebar collapses into responsive hamburger slide-over menu; tables render as mobile cards; stat cards collapse to single column).
  - Tablet: `768px - 1024px` (Two-column layout, compact sidebar).
  - Desktop: `> 1024px` (Full expanded dashboard, multi-column analytics grid, full-width data tables).
- **Touch-Friendly Targets**: All buttons, links, and form inputs must have a minimum interactive tap target of $44 \times 44\text{ px}$ on mobile screens.
