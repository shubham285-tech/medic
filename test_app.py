import unittest
import json
import datetime
from app import app
import db

class MedicalExpiryTrackerTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        # Initialize test database
        db.init_db(force_reseed=True)

    def login_admin(self):
        return self.client.post("/login", data={
            "identity": "admin",
            "password": "admin123"
        }, follow_redirects=True)

    def test_01_login_logout(self):
        # Invalid login
        res = self.client.post("/login", data={
            "identity": "admin",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertIn(b"Invalid credentials", res.data)

        # Valid login
        res = self.login_admin()
        self.assertIn(b"Welcome back", res.data)
        self.assertIn(b"Dashboard", res.data)

        # Logout
        res = self.client.get("/logout", follow_redirects=True)
        self.assertIn(b"signed out securely", res.data)

    def test_02_dashboard_and_stats(self):
        self.login_admin()
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Total Batches", res.data)
        self.assertIn(b"Expiring Soon", res.data)
        self.assertIn(b"Expired Medicines", res.data)

        # API Charts
        chart_res = self.client.get("/api/dashboard/charts")
        self.assertEqual(chart_res.status_code, 200)
        chart_data = json.loads(chart_res.data)
        self.assertIn("status_doughnut", chart_data)
        self.assertIn("monthly_trend", chart_data)

    def test_03_inventory_crud_and_validation(self):
        self.login_admin()
        
        # 1. Test Expiry Date <= Manufacturing Date validation
        today = datetime.date.today().strftime("%Y-%m-%d")
        past_date = (datetime.date.today() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")

        invalid_res = self.client.post("/medicines/add", data={
            "name": "Test Drug Fail",
            "batch_number": "FAIL001",
            "category": "Antibiotics",
            "manufacturer": "Test Pharma",
            "quantity": "50",
            "purchase_price": "10.00",
            "selling_price": "20.00",
            "manufacturing_date": today,
            "expiry_date": past_date,  # Invalid: expiry before mfg
            "minimum_stock": "10",
            "description": "Test note"
        }, follow_redirects=True)
        self.assertIn(b"Expiry date must be strictly after the manufacturing date", invalid_res.data)

        # 2. Test successful creation
        future_date = (datetime.date.today() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        valid_res = self.client.post("/medicines/add", data={
            "name": "Test Valid Amoxicillin 500mg",
            "batch_number": "TST2026V01",
            "category": "Antibiotics",
            "manufacturer": "Apex Labs",
            "supplier": "Medix Global Pharma Distributors",
            "quantity": "5", # low stock (min is 10)
            "purchase_price": "5.50",
            "selling_price": "12.00",
            "manufacturing_date": past_date,
            "expiry_date": future_date, # expiring soon (15 days)
            "minimum_stock": "10",
            "description": "Store dry"
        }, follow_redirects=True)
        self.assertIn(b"added to inventory successfully", valid_res.data)

        # 3. Retrieve medicine details
        conn = db.get_connection()
        med = conn.execute("SELECT id FROM medicines WHERE batch_number = 'TST2026V01'").fetchone()
        conn.close()
        self.assertIsNotNone(med)
        med_id = med["id"]

        detail_res = self.client.get(f"/medicines/{med_id}", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(detail_res.status_code, 200)
        detail_data = json.loads(detail_res.data)
        self.assertEqual(detail_data["medicine"]["status"], "EXPIRING SOON")
        self.assertTrue(detail_data["medicine"]["is_low_stock"])

        # 4. Edit medicine
        edit_res = self.client.post(f"/medicines/edit/{med_id}", data={
            "name": "Test Valid Amoxicillin 500mg UPDATED",
            "batch_number": "TST2026V01",
            "category": "Antibiotics",
            "manufacturer": "Apex Labs",
            "supplier": "Medix Global Pharma Distributors",
            "quantity": "25", # now safe stock
            "purchase_price": "5.50",
            "selling_price": "12.00",
            "manufacturing_date": past_date,
            "expiry_date": future_date,
            "minimum_stock": "10",
            "description": "Updated note"
        }, follow_redirects=True)
        self.assertIn(b"updated successfully", edit_res.data)

        # 5. Delete medicine
        del_res = self.client.post(f"/medicines/delete/{med_id}", follow_redirects=True)
        self.assertIn(b"permanently removed from inventory", del_res.data)

    def test_04_alerts_management(self):
        self.login_admin()
        res = self.client.get("/alerts")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Surveillance Center", res.data)

        conn = db.get_connection()
        alert = conn.execute("SELECT id FROM alerts LIMIT 1").fetchone()
        conn.close()

        if alert:
            # Mark as read
            mark_res = self.client.post(f"/alerts/mark-read/{alert['id']}", headers={"X-Requested-With": "XMLHttpRequest"})
            self.assertEqual(mark_res.status_code, 200)
            res_data = json.loads(mark_res.data)
            self.assertTrue(res_data["success"])

    def test_05_reports_and_csv_export(self):
        self.login_admin()
        res = self.client.get("/reports?type=expiring_soon")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Audit Studio", res.data)

        # CSV Download
        csv_res = self.client.get("/reports/export/csv?type=all")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn(b"Medicine Name,Batch Number", csv_res.data)

        # Print View
        print_res = self.client.get("/reports/print?type=all")
        self.assertEqual(print_res.status_code, 200)
        self.assertIn(b"Inventory Audit Report", print_res.data)

    def test_06_settings(self):
        self.login_admin()
        res = self.client.post("/settings", data={
            "action": "save_settings",
            "pharmacy_name": "Updated Health Center",
            "contact_email": "health@center.org",
            "currency_symbol": "$",
            "theme": "dark-glass",
            "expiry_warning_days": "45",
            "low_stock_threshold": "20"
        }, follow_redirects=True)
        self.assertIn(b"System configuration updated successfully", res.data)

        settings = db.get_settings()
        self.assertEqual(settings["expiry_warning_days"], 45)
        self.assertEqual(settings["pharmacy_name"], "Updated Health Center")

if __name__ == "__main__":
    unittest.main()
