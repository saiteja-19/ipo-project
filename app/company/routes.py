from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.db import get_db
import sqlite3
# --- IMPORT HASHING TOOLS ---
from werkzeug.security import generate_password_hash, check_password_hash

company_bp = Blueprint('company', __name__)

@company_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        cin = request.form['cin']
        email = request.form['email']
        password = request.form['password']
        sector = request.form['sector']
        db = get_db()
        
        try:
            # --- HASH THE PASSWORD ---
            hashed_password = generate_password_hash(password)
            
            db.execute(
                "INSERT INTO companies (name, cin, email, password, sector) VALUES (?, ?, ?, ?, ?)",
                (name, cin, email, hashed_password, sector) # Store the hash
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
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        
        # --- MODIFY LOGIN LOGIC ---
        company = db.execute(
            "SELECT * FROM companies WHERE email = ?", (email,)
        ).fetchone()

        # Check if user exists and password hash matches
        if company and check_password_hash(company['password'], password):
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
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))
    db = get_db()
    ipos = db.execute(
        "SELECT * FROM ipos WHERE company_id = ? ORDER BY id DESC", (session['user_id'],)
    ).fetchall()
    return render_template('company_dashboard.html', ipos=ipos, title="Company Dashboard")

@company_bp.route('/list_ipo', methods=['GET', 'POST'])
def list_ipo():
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))
    if request.method == 'POST':
        db = get_db()
        db.execute(
            """INSERT INTO ipos 
               (company_id, company_name, issue_price, lot_size, total_lots, open_date, close_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session['user_id'], session['user_name'], request.form['issue_price'], 
             request.form['lot_size'], request.form['total_lots'],
             request.form['open_date'], request.form['close_date'])
        )
        db.commit()
        return redirect(url_for('company.dashboard'))
    return render_template('list_ipo.html', title="List New IPO")

@company_bp.route('/ipo/<int:ipo_id>/applications')
def view_ipo_applications(ipo_id):
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))

    db = get_db()
    
    ipo = db.execute(
        "SELECT * FROM ipos WHERE id = ? AND company_id = ?",
        (ipo_id, session['user_id'])
    ).fetchone()

    if not ipo:
        abort(404) 

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
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))

    new_status = request.form['status']
    if new_status not in ['Approved', 'Rejected']:
        abort(400) 

    db = get_db()
    
    application = db.execute("""
        SELECT a.id, i.company_id, a.ipo_id FROM ipo_applications a
        JOIN ipos i ON a.ipo_id = i.id
        WHERE a.id = ? AND i.company_id = ?
    """, (application_id, session['user_id'])).fetchone()

    if not application:
        abort(404) # Not Found or Not Authorized

    db.execute(
        "UPDATE ipo_applications SET status = ? WHERE id = ?",
        (new_status, application_id)
    )
    db.commit()

    return redirect(url_for('company.view_ipo_applications', ipo_id=application['ipo_id']))

@company_bp.route('/ipo/<int:ipo_id>/report')
def allotment_report(ipo_id):
    """Displays a statistical summary of applications for an IPO."""
    if session.get('user_type') != 'company':
        return redirect(url_for('company.login'))
    
    db = get_db()
    
    # Security Check: Verify this IPO belongs to the logged-in company
    ipo = db.execute(
        "SELECT * FROM ipos WHERE id = ? AND company_id = ?",
        (ipo_id, session['user_id'])
    ).fetchone()

    if not ipo:
        abort(404) # Not found or not authorized

    # Run aggregation query to get all stats
    report_stats = db.execute("""
        SELECT
            COUNT(id) as total_applications,
            COALESCE(SUM(lots_applied), 0) as total_lots_applied,
            COALESCE(SUM(CASE WHEN status = 'Approved' THEN lots_applied ELSE 0 END), 0) as approved_lots,
            COALESCE(SUM(CASE WHEN status = 'Rejected' THEN lots_applied ELSE 0 END), 0) as rejected_lots,
            COALESCE(SUM(CASE WHEN status = 'Pending' THEN lots_applied ELSE 0 END), 0) as pending_lots
        FROM ipo_applications
        WHERE ipo_id = ?
    """, (ipo_id,)).fetchone()

    return render_template(
        'company_report.html',
        ipo=ipo,
        report=report_stats,
        title=f"Allotment Report for {ipo['company_name']}"
    )