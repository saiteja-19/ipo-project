# app/company/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_db
import sqlite3

company_bp = Blueprint('company', __name__)

@company_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # ... (Copy the logic from company_register in your old app.py)
        # ...
        name = request.form['name']
        cin = request.form['cin']
        email = request.form['email']
        password = request.form['password']
        sector = request.form['sector']
        db = get_db()
        try:
            db.execute(
                "INSERT INTO companies (name, cin, email, password, sector) VALUES (?, ?, ?, ?, ?)",
                (name, cin, email, password, sector)
            )
            db.commit()
            return render_template('success.html', message="Company Registration Successful!", redirect_url=url_for('company.login'))
        except sqlite3.IntegrityError:
            error = "A company with this CIN or Email already exists."
            return render_template('company_register.html', error=error)
    return render_template('company_register.html', title="Company Registration")

@company_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ... (Copy the logic from company_login) ...
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        company = db.execute(
            "SELECT * FROM companies WHERE email = ? AND password = ?", (email, password)
        ).fetchone()
        if company:
            session.clear()
            session['user_id'] = company['id']
            session['user_name'] = company['name']
            session['user_type'] = 'company'
            return redirect(url_for('company.dashboard'))
        else:
            error = "Invalid company email or password."
            return render_template('company_login.html', error=error)
    return render_template('company_login.html', title="Company Login")

@company_bp.route('/dashboard')
def dashboard():
    # ... (Copy the logic from company_dashboard) ...
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))
    db = get_db()
    ipos = db.execute(
        "SELECT * FROM ipos WHERE company_id = ? ORDER BY id DESC", (session['user_id'],)
    ).fetchall()
    return render_template('company_dashboard.html', ipos=ipos, title="Company Dashboard")

@company_bp.route('/list_ipo', methods=['GET', 'POST'])
def list_ipo():
    # ... (Copy the logic from list_ipo) ...
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))
    if request.method == 'POST':
        db = get_db()
        db.execute(
        """INSERT INTO ipos 
           (company_id, company_name, issue_price, lot_size, total_lots, open_date, close_date) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""", # Add total_lots to the query
        (session['user_id'], session['user_name'], request.form['issue_price'], 
         request.form['lot_size'], request.form['total_lots'], # Get total_lots from the form
         request.form['open_date'], request.form['close_date']
         )
    )
       
        db.commit()
        return redirect(url_for('company.dashboard'))
    return render_template('list_ipo.html', title="List New IPO")

@company_bp.route('/ipo/<int:ipo_id>/applications')
def view_ipo_applications(ipo_id):
    """Allows a company to view all applications for one of its IPOs."""
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))

    db = get_db()
    
    # Security Check: Verify this IPO belongs to the logged-in company
    ipo = db.execute(
        "SELECT * FROM ipos WHERE id = ? AND company_id = ?",
        (ipo_id, session['user_id'])
    ).fetchone()

    # If the IPO doesn't exist or doesn't belong to this company, show a "Not Found" error
    if not ipo:
        abort(404)

    # Fetch all applications for this IPO, joining with candidate details
    applications = db.execute("""
        SELECT
            a.id,
            c.name as candidate_name,
            c.email as candidate_email,
            a.lots_applied,
            a.status
        FROM ipo_applications a
        JOIN candidates c ON a.candidate_id = c.id
        WHERE a.ipo_id = ?
        ORDER BY a.id DESC
    """, (ipo_id,)).fetchall()

    return render_template(
        'view_ipo_applications.html', 
        applications=applications, 
        ipo=ipo,
        title=f"Applications for {ipo['company_name']}"
    )

@company_bp.route('/application/<int:application_id>/update', methods=['POST'])
def update_application_status(application_id):
    """Updates an application's status to Approved or Rejected."""
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))

    new_status = request.form['status']
    if new_status not in ['Approved', 'Rejected']:
        abort(400) # Bad Request

    db = get_db()
    
    # Security Check: Ensure the company owns the IPO this application is for
    application = db.execute("""
        SELECT a.id, i.company_id, a.ipo_id FROM ipo_applications a
        JOIN ipos i ON a.ipo_id = i.id
        WHERE a.id = ? AND i.company_id = ?
    """, (application_id, session['user_id'])).fetchone()

    if not application:
        abort(404) # Not Found or Not Authorized

    # Update the application status in the database
    db.execute(
        "UPDATE ipo_applications SET status = ? WHERE id = ?",
        (new_status, application_id)
    )
    db.commit()

    # Redirect back to the list of applications for that IPO
    return redirect(url_for('company.view_ipo_applications', ipo_id=application['ipo_id']))
