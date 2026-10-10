import os
import csv
import io
import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response, make_response
)
from werkzeug.security import generate_password_hash, check_password_hash
import db

app = Flask(__name__, static_folder="public/static")
secret_key = os.environ.get("SECRET_KEY")
is_production = bool(os.environ.get("VERCEL")) or db.uses_firebase()
if is_production and not secret_key:
    raise RuntimeError("Configure SECRET_KEY for production deployments.")
if os.environ.get("VERCEL") and not db.uses_firebase():
    raise RuntimeError("Configure Firebase Admin credentials to use Firestore on Vercel.")
app.secret_key = secret_key or "local-development-only-secret"
app.config.update(
    IS_PRODUCTION=is_production,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=is_production,
)

if os.environ.get("VERCEL"):
    db.init_db()

# Template helpers & context processors
@app.context_processor
def inject_global_data():
    settings = db.get_settings()
    unread_alerts_count = 0
    current_user = None

    if "user_id" in session:
        current_user = db.get_user_by_id(session["user_id"])
        unread_alerts_count = db.count_alerts(unread_only=True)

    today_str = datetime.date.today().strftime("%B %d, %Y")
    current_year = datetime.date.today().year

    return {
        "settings": settings,
        "current_user": current_user,
        "unread_alerts_count": unread_alerts_count,
        "today_str": today_str,
        "current_year": current_year
    }

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access the Medical Expiry Tracker.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        password = request.form.get("password", "").strip()
        remember = request.form.get("remember")

        if not identity or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("login.html", identity=identity)

        user = db.get_user_by_identity(identity)

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            if remember:
                session.permanent = True

            flash(f"Welcome back, {user['full_name']}!", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))
        else:
            flash("Invalid credentials. Please verify your username/email and password.", "danger")
            return render_template("login.html", identity=identity)

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "Pharmacist").strip()

        if not full_name or not username or not email or not password:
            flash("All fields are required for registration.", "danger")
            return render_template("login.html", register_mode=True)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("login.html", register_mode=True)

        if db.find_user_conflict(username, email):
            flash("Username or email already registered. Please sign in.", "warning")
            return render_template("login.html", register_mode=True)

        pwd_hash = generate_password_hash(password, method="pbkdf2:sha256")
        try:
            db.create_user({
                "full_name": full_name,
                "username": username,
                "email": email,
                "password_hash": pwd_hash,
                "role": role,
            })
        except ValueError:
            flash("Username or email already registered. Please sign in.", "warning")
            return render_template("login.html", register_mode=True)

        flash("Account created successfully! Please sign in with your credentials.", "success")
        return redirect(url_for("login"))

    return render_template("login.html", register_mode=True)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out securely.", "info")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please provide your registered email address.", "danger")
        else:
            flash("If the email exists, a password reset link has been dispatched to your inbox.", "info")
        return redirect(url_for("login"))
    return render_template("login.html", forgot_mode=True)

# ==========================================
# DASHBOARD
# ==========================================

@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    # Make sure alerts are fresh
    db.refresh_alerts()

    # Query all medicines
    medicines = db.get_medicines()

    total_medicines = len(medicines)
    total_stock_units = sum(m["quantity"] for m in medicines)

    expired_count = 0
    expiring_soon_count = 0
    safe_count = 0
    low_stock_count = 0

    evaluated_medicines = []
    for med in medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        med_dict = dict(med)
        med_dict.update(calc)
        evaluated_medicines.append(med_dict)

        if calc["is_expired"]:
            expired_count += 1
        elif calc["is_expiring_soon"]:
            expiring_soon_count += 1
        else:
            safe_count += 1

        if calc["is_low_stock"]:
            low_stock_count += 1

    # Fetch top 5 recent alerts
    recent_alerts = sorted(
        db.get_alerts(),
        key=lambda alert: alert.get("created_at", ""),
        reverse=True,
    )[:5]

    # Fetch 5 recently added medicines
    recently_added = db.get_medicines(sort_by="id_desc")[:5]
    
    recent_added_evaluated = []
    for r in recently_added:
        calc = db.calculate_medicine_status(
            r["expiry_date"], r["quantity"], r["minimum_stock"], warning_days
        )
        d = dict(r)
        d.update(calc)
        recent_added_evaluated.append(d)

    stats = {
        "total_medicines": total_medicines,
        "total_stock": total_stock_units,
        "expired": expired_count,
        "expiring_soon": expiring_soon_count,
        "safe": safe_count,
        "low_stock": low_stock_count
    }

    # Determine user greeting
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    return render_template(
        "dashboard.html",
        stats=stats,
        greeting=greeting,
        recent_alerts=recent_alerts,
        recently_added=recent_added_evaluated,
        warning_days=warning_days
    )

# Dashboard Chart Data API
@app.route("/api/dashboard/charts")
@login_required
def api_dashboard_charts():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    medicines = db.get_medicines()

    # 1. Expiry status distribution
    status_counts = {"SAFE": 0, "EXPIRING SOON": 0, "EXPIRED": 0}
    category_counts = {}
    monthly_expiry = {}

    today = datetime.date.today()

    for med in medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        status_counts[calc["status"]] = status_counts.get(calc["status"], 0) + 1

        cat = med["category"]
        category_counts[cat] = category_counts.get(cat, 0) + med["quantity"]

        # Parse expiry month
        try:
            exp_date = datetime.datetime.strptime(med["expiry_date"], "%Y-%m-%d").date()
            month_key = exp_date.strftime("%b %Y")
            monthly_expiry[month_key] = monthly_expiry.get(month_key, 0) + 1
        except Exception:
            pass

    # Sort monthly expiry by chronological order (next 6-12 months)
    # Generate list of upcoming months
    timeline_labels = []
    timeline_values = []
    for i in range(-2, 10):
        target_month = today.replace(day=1) + datetime.timedelta(days=i * 30.5)
        m_str = target_month.strftime("%b %Y")
        if m_str not in timeline_labels:
            timeline_labels.append(m_str)
            timeline_values.append(monthly_expiry.get(m_str, 0))

    return jsonify({
        "status_doughnut": {
            "labels": ["Safe", "Expiring Soon", "Expired"],
            "data": [status_counts["SAFE"], status_counts["EXPIRING SOON"], status_counts["EXPIRED"]],
            "colors": ["#10b981", "#f59e0b", "#ef4444"]
        },
        "monthly_trend": {
            "labels": timeline_labels,
            "data": timeline_values
        },
        "category_polar": {
            "labels": list(category_counts.keys()),
            "data": list(category_counts.values())
        }
    })

# ==========================================
# MEDICINE INVENTORY CRUD
# ==========================================

@app.route("/medicines")
@login_required
def medicines():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()
    status_filter = request.args.get("status", "").strip()
    stock_filter = request.args.get("stock", "").strip()
    sort_by = request.args.get("sort", "expiry_asc")

    raw_medicines = db.get_medicines(search_query, category_filter, sort_by)
    categories = db.get_category_names()

    # Evaluate dynamic status on results
    filtered_medicines = []
    for med in raw_medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        med_dict = dict(med)
        med_dict.update(calc)

        # Apply status filter if requested
        if status_filter:
            if status_filter == "EXPIRED" and not calc["is_expired"]:
                continue
            if status_filter == "EXPIRING_SOON" and not calc["is_expiring_soon"]:
                continue
            if status_filter == "SAFE" and not calc["is_safe"]:
                continue

        # Apply stock filter if requested
        if stock_filter:
            if stock_filter == "LOW_STOCK" and not calc["is_low_stock"]:
                continue
            if stock_filter == "OUT_OF_STOCK" and not calc["is_out_of_stock"]:
                continue
            if stock_filter == "IN_STOCK" and calc["is_low_stock"]:
                continue

        filtered_medicines.append(med_dict)

    return render_template(
        "medicines.html",
        medicines=filtered_medicines,
        categories=categories,
        search_query=search_query,
        category_filter=category_filter,
        status_filter=status_filter,
        stock_filter=stock_filter,
        sort_by=sort_by,
        total_count=len(filtered_medicines)
    )

@app.route("/medicines/add", methods=["GET", "POST"])
@login_required
def add_medicine():
    categories = db.get_category_names()
    suppliers = db.get_supplier_names()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        batch_number = request.form.get("batch_number", "").strip().upper()
        category = request.form.get("category", "").strip()
        manufacturer = request.form.get("manufacturer", "").strip()
        supplier = request.form.get("supplier", "").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        purchase_price_str = request.form.get("purchase_price", "0.0").strip()
        selling_price_str = request.form.get("selling_price", "0.0").strip()
        manufacturing_date = request.form.get("manufacturing_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()
        minimum_stock_str = request.form.get("minimum_stock", "10").strip()
        description = request.form.get("description", "").strip()

        # Validation rules
        errors = []
        if not name:
            errors.append("Medicine name is required.")
        if not batch_number:
            errors.append("Batch number is required.")
        if not category:
            errors.append("Please select a category.")
        if not manufacturer:
            errors.append("Manufacturer name is required.")
        if not manufacturing_date:
            errors.append("Manufacturing date is required.")
        if not expiry_date:
            errors.append("Expiry date is required.")

        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity cannot be negative.")
        except ValueError:
            errors.append("Quantity must be a valid integer.")
            quantity = 0

        try:
            purchase_price = float(purchase_price_str)
            if purchase_price < 0:
                errors.append("Purchase price cannot be negative.")
        except ValueError:
            errors.append("Purchase price must be a valid number.")
            purchase_price = 0.0

        try:
            selling_price = float(selling_price_str)
            if selling_price < 0:
                errors.append("Selling price cannot be negative.")
        except ValueError:
            errors.append("Selling price must be a valid number.")
            selling_price = 0.0

        try:
            minimum_stock = int(minimum_stock_str)
            if minimum_stock < 1:
                errors.append("Minimum stock level must be at least 1.")
        except ValueError:
            errors.append("Minimum stock level must be a valid integer.")
            minimum_stock = 10

        # Business Rule: Expiry date >= Manufacturing date
        if manufacturing_date and expiry_date:
            if expiry_date <= manufacturing_date:
                errors.append("Expiry date must be strictly after the manufacturing date.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "add_medicine.html",
                categories=categories,
                suppliers=suppliers,
                form_data=request.form
            )

        db.create_medicine({
            "name": name,
            "batch_number": batch_number,
            "category": category,
            "manufacturer": manufacturer,
            "supplier": supplier,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "manufacturing_date": manufacturing_date,
            "expiry_date": expiry_date,
            "minimum_stock": minimum_stock,
            "description": description,
        })

        # Update alerts automatically
        db.refresh_alerts()

        flash(f"Medicine '{name}' (Batch: {batch_number}) added to inventory successfully.", "success")
        return redirect(url_for("medicines"))

    return render_template(
        "add_medicine.html",
        categories=categories,
        suppliers=suppliers,
        form_data={}
    )

@app.route("/medicines/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_medicine(id):
    medicine = db.get_medicine(id)

    if not medicine:
        flash("Medicine not found.", "danger")
        return redirect(url_for("medicines"))

    categories = db.get_category_names()
    suppliers = db.get_supplier_names()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        batch_number = request.form.get("batch_number", "").strip().upper()
        category = request.form.get("category", "").strip()
        manufacturer = request.form.get("manufacturer", "").strip()
        supplier = request.form.get("supplier", "").strip()
        quantity_str = request.form.get("quantity", "0").strip()
        purchase_price_str = request.form.get("purchase_price", "0.0").strip()
        selling_price_str = request.form.get("selling_price", "0.0").strip()
        manufacturing_date = request.form.get("manufacturing_date", "").strip()
        expiry_date = request.form.get("expiry_date", "").strip()
        minimum_stock_str = request.form.get("minimum_stock", "10").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not name:
            errors.append("Medicine name is required.")
        if not batch_number:
            errors.append("Batch number is required.")
        if not category:
            errors.append("Category is required.")
        if not manufacturer:
            errors.append("Manufacturer is required.")
        if not manufacturing_date or not expiry_date:
            errors.append("Manufacturing and Expiry dates are required.")

        try:
            quantity = int(quantity_str)
            if quantity < 0:
                errors.append("Quantity cannot be negative.")
        except ValueError:
            errors.append("Quantity must be a valid integer.")
            quantity = medicine["quantity"]

        try:
            purchase_price = float(purchase_price_str)
            if purchase_price < 0:
                errors.append("Purchase price cannot be negative.")
        except ValueError:
            errors.append("Purchase price must be a valid number.")
            purchase_price = medicine["purchase_price"]

        try:
            selling_price = float(selling_price_str)
            if selling_price < 0:
                errors.append("Selling price cannot be negative.")
        except ValueError:
            errors.append("Selling price must be a valid number.")
            selling_price = medicine["selling_price"]

        try:
            minimum_stock = int(minimum_stock_str)
            if minimum_stock < 1:
                errors.append("Minimum stock level must be at least 1.")
        except ValueError:
            errors.append("Minimum stock level must be a valid integer.")
            minimum_stock = medicine["minimum_stock"]

        if manufacturing_date and expiry_date and expiry_date <= manufacturing_date:
            errors.append("Expiry date must be strictly after the manufacturing date.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template(
                "edit_medicine.html",
                medicine=medicine,
                categories=categories,
                suppliers=suppliers
            )

        db.update_medicine(id, {
            "name": name,
            "batch_number": batch_number,
            "category": category,
            "manufacturer": manufacturer,
            "supplier": supplier,
            "quantity": quantity,
            "purchase_price": purchase_price,
            "selling_price": selling_price,
            "manufacturing_date": manufacturing_date,
            "expiry_date": expiry_date,
            "minimum_stock": minimum_stock,
            "description": description,
        })

        db.refresh_alerts()
        flash(f"Medicine '{name}' updated successfully.", "success")
        return redirect(url_for("medicines"))

    return render_template(
        "edit_medicine.html",
        medicine=medicine,
        categories=categories,
        suppliers=suppliers
    )

@app.route("/medicines/delete/<int:id>", methods=["POST"])
@login_required
def delete_medicine(id):
    med = db.delete_medicine(id)
    if med:
        name = med["name"]
        db.refresh_alerts()
        flash(f"Medicine '{name}' has been permanently removed from inventory.", "info")
    else:
        flash("Medicine not found.", "danger")

    return redirect(url_for("medicines"))

@app.route("/medicines/<int:id>")
@login_required
def medicine_details(id):
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    med = db.get_medicine(id)
    if not med:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"error": "Medicine not found"}), 404
        flash("Medicine not found.", "danger")
        return redirect(url_for("medicines"))

    calc = db.calculate_medicine_status(
        med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
    )
    med_dict = dict(med)
    med_dict.update(calc)

    # Fetch alerts for this medicine
    alerts = db.get_alerts(medicine_id=id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.args.get("format") == "json":
        return jsonify({
            "medicine": med_dict,
            "alerts": [dict(a) for a in alerts]
        })

    return render_template("medicine_details.html", medicine=med_dict, alerts=alerts)

# ==========================================
# ALERTS CENTER
# ==========================================

@app.route("/alerts")
@login_required
def alerts():
    db.refresh_alerts()

    alert_type = request.args.get("type", "").strip()
    alerts_list = db.get_alerts(alert_type=alert_type or None)
    unread_count = db.count_alerts(unread_only=True)
    total_count = db.count_alerts()

    return render_template(
        "alerts.html",
        alerts=alerts_list,
        unread_count=unread_count,
        total_count=total_count,
        current_filter=alert_type
    )

@app.route("/alerts/mark-read/<int:id>", methods=["POST"])
@login_required
def mark_alert_read(id):
    db.set_alert_read(id)
    unread_count = db.count_alerts(unread_only=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "unread_count": unread_count})

    flash("Alert marked as read.", "success")
    return redirect(url_for("alerts"))

@app.route("/alerts/mark-all-read", methods=["POST"])
@login_required
def mark_all_alerts_read():
    db.mark_all_alerts_read()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "unread_count": 0})

    flash("All alerts marked as read.", "success")
    return redirect(url_for("alerts"))

@app.route("/alerts/delete/<int:id>", methods=["POST"])
@login_required
def delete_alert(id):
    db.delete_alert(id)
    unread_count = db.count_alerts(unread_only=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "unread_count": unread_count})

    flash("Alert removed.", "info")
    return redirect(url_for("alerts"))

@app.route("/alerts/clear-all", methods=["POST"])
@login_required
def clear_all_alerts():
    db.clear_alerts()

    flash("All alerts have been cleared.", "info")
    return redirect(url_for("alerts"))

# ==========================================
# REPORTS & DATA EXPORT
# ==========================================

@app.route("/reports")
@login_required
def reports():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)

    report_type = request.args.get("type", "expiring_soon")
    medicines = db.get_medicines()
    categories = db.get_category_names()

    evaluated = []
    total_valuation = 0.0

    for med in medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        d = dict(med)
        d.update(calc)
        total_valuation += (med["quantity"] * med["purchase_price"])

        if report_type == "expired" and calc["is_expired"]:
            evaluated.append(d)
        elif report_type == "expiring_soon" and calc["is_expiring_soon"]:
            evaluated.append(d)
        elif report_type == "low_stock" and calc["is_low_stock"]:
            evaluated.append(d)
        elif report_type == "all":
            evaluated.append(d)
        elif report_type.startswith("cat_"):
            cat_name = report_type.replace("cat_", "")
            if med["category"] == cat_name:
                evaluated.append(d)
        elif report_type == "expiring_soon" and not calc["is_expiring_soon"]:
            pass # default logic handled above

    return render_template(
        "reports.html",
        medicines=evaluated,
        report_type=report_type,
        categories=categories,
        total_count=len(evaluated),
        total_valuation=total_valuation,
        warning_days=warning_days
    )

@app.route("/reports/export/csv")
@login_required
def export_csv():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)
    report_type = request.args.get("type", "all")

    medicines = db.get_medicines()

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    writer.writerow([
        "ID", "Medicine Name", "Batch Number", "Category", "Manufacturer",
        "Supplier", "Quantity", "Purchase Price", "Selling Price",
        "Manufacturing Date", "Expiry Date", "Days Remaining", "Expiry Status", "Stock Status"
    ])

    for med in medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )

        include = False
        if report_type == "all":
            include = True
        elif report_type == "expired" and calc["is_expired"]:
            include = True
        elif report_type == "expiring_soon" and calc["is_expiring_soon"]:
            include = True
        elif report_type == "low_stock" and calc["is_low_stock"]:
            include = True
        elif report_type.startswith("cat_"):
            cat_name = report_type.replace("cat_", "")
            if med["category"] == cat_name:
                include = True

        if include:
            writer.writerow([
                med["id"],
                med["name"],
                med["batch_number"],
                med["category"],
                med["manufacturer"],
                med["supplier"] or "N/A",
                med["quantity"],
                f"{med['purchase_price']:.2f}",
                f"{med['selling_price']:.2f}",
                med["manufacturing_date"],
                med["expiry_date"],
                calc["days_remaining"],
                calc["status"],
                calc["stock_status"]
            ])

    filename = f"medicine_report_{report_type}_{datetime.date.today().strftime('%Y%m%d')}.csv"
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response

@app.route("/reports/print")
@login_required
def print_report():
    settings = db.get_settings()
    warning_days = settings.get("expiry_warning_days", 30)
    report_type = request.args.get("type", "all")

    medicines = db.get_medicines()

    evaluated = []
    for med in medicines:
        calc = db.calculate_medicine_status(
            med["expiry_date"], med["quantity"], med["minimum_stock"], warning_days
        )
        d = dict(med)
        d.update(calc)

        if report_type == "all":
            evaluated.append(d)
        elif report_type == "expired" and calc["is_expired"]:
            evaluated.append(d)
        elif report_type == "expiring_soon" and calc["is_expiring_soon"]:
            evaluated.append(d)
        elif report_type == "low_stock" and calc["is_low_stock"]:
            evaluated.append(d)
        elif report_type.startswith("cat_") and med["category"] == report_type.replace("cat_", ""):
            evaluated.append(d)

    return render_template(
        "reports_print.html",
        medicines=evaluated,
        report_type=report_type,
        settings=settings,
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

# ==========================================
# SETTINGS & CONFIGURATION
# ==========================================

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action", "save_settings")

        if action == "save_settings":
            pharmacy_name = request.form.get("pharmacy_name", "Apex Medical Care & Pharmacy").strip()
            contact_email = request.form.get("contact_email", "admin@apexmed.com").strip()
            currency_symbol = request.form.get("currency_symbol", "$").strip()
            theme = request.form.get("theme", "dark-glass").strip()

            try:
                expiry_warning_days = int(request.form.get("expiry_warning_days", 30))
                if expiry_warning_days < 1:
                    expiry_warning_days = 30
            except ValueError:
                expiry_warning_days = 30

            try:
                low_stock_threshold = int(request.form.get("low_stock_threshold", 15))
                if low_stock_threshold < 1:
                    low_stock_threshold = 15
            except ValueError:
                low_stock_threshold = 15

            db.update_settings({
                "pharmacy_name": pharmacy_name,
                "contact_email": contact_email,
                "currency_symbol": currency_symbol,
                "theme": theme,
                "expiry_warning_days": expiry_warning_days,
                "low_stock_threshold": low_stock_threshold,
            })

            # Refresh alerts with new threshold
            db.refresh_alerts()
            flash("System configuration updated successfully! Inventory re-evaluated.", "success")

        elif action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip()
            new_password = request.form.get("new_password", "").strip()

            if not full_name or not email:
                flash("Full name and email are required.", "danger")
            else:
                if new_password:
                    if len(new_password) < 6:
                        flash("New password must be at least 6 characters.", "danger")
                    else:
                        pwd_hash = generate_password_hash(new_password, method="pbkdf2:sha256")
                        try:
                            db.update_user(session["user_id"], {
                                "full_name": full_name,
                                "email": email,
                                "password_hash": pwd_hash,
                            })
                            session["full_name"] = full_name
                            flash("Profile and password updated successfully.", "success")
                        except ValueError:
                            flash("Email address already registered.", "danger")
                else:
                    try:
                        db.update_user(session["user_id"], {
                            "full_name": full_name,
                            "email": email,
                        })
                        session["full_name"] = full_name
                        flash("Profile updated successfully.", "success")
                    except ValueError:
                        flash("Email address already registered.", "danger")

        elif action == "reset_demo_data":
            if db.uses_firebase():
                flash("Demo data reset is disabled for the persistent database.", "warning")
            else:
                db.reset_demo_data()
                flash("Database reset! All demo medicines and alerts restored to pristine state.", "info")

        return redirect(url_for("settings"))

    current_settings = db.get_settings()
    user_row = db.get_user_by_id(session["user_id"])

    return render_template("settings.html", settings=current_settings, user=user_row)

if __name__ == "__main__":
    db.init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", host="0.0.0.0", port=5000)
