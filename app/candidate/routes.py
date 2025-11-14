from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.db import get_db
import sqlite3
# --- IMPORT HASHING TOOLS ---
from werkzeug.security import generate_password_hash, check_password_hash

candidate_bp = Blueprint('candidate', __name__)

@candidate_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        try:
            # --- HASH THE PASSWORD ---
            hashed_password = generate_password_hash(password)
            db.execute("INSERT INTO candidates (name, email, password) VALUES (?, ?, ?)", (name, email, hashed_password))
            db.commit()
            return render_template('success.html', message="Candidate Registration Successful!", redirect_url=url_for('candidate.login'))
        except sqlite3.IntegrityError:
            error = "A candidate with this email already exists."
            return render_template('candidate_register.html', error=error)
    return render_template('candidate_register.html', title="Candidate Registration")


@candidate_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        
        # --- MODIFY LOGIN LOGIC ---
        candidate = db.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

        if candidate and check_password_hash(candidate['password'], password):
            session.clear()
            session['user_id'] = candidate['id']
            session['user_name'] = candidate['name']
            session['user_type'] = 'candidate'
            return redirect(url_for('main.index'))
        else:
            error = "Invalid candidate email or password."
            return render_template('candidate_login.html', error=error)
    return render_template('candidate_login.html', title="Candidate Login")

@candidate_bp.route('/apply/<int:ipo_id>', methods=['GET', 'POST'])
def apply_ipo(ipo_id):
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate.login'))

    db = get_db()
    
    ipo_details = db.execute("""
        SELECT
            i.id, i.company_name, i.issue_price, i.lot_size, i.total_lots,
            i.open_date, i.close_date,
            COALESCE(SUM(CASE WHEN a.status = 'Approved' THEN a.lots_applied ELSE 0 END), 0) as approved_lots
        FROM ipos i
        LEFT JOIN ipo_applications a ON i.id = a.ipo_id
        WHERE i.id = ?
        GROUP BY i.id
    """, (ipo_id,)).fetchone()

    if not ipo_details:
        abort(404) 
    
    remaining_lots = ipo_details['total_lots'] - ipo_details['approved_lots']

    if request.method == 'POST':
        lots_applied = int(request.form['lots'])
        candidate_id = session['user_id']
        
        # --- FRAUD CHECK (DUPLICATE APPLICATION) ---
        existing_application = db.execute("""
            SELECT id FROM ipo_applications
            WHERE candidate_id = ? AND ipo_id = ?
        """, (candidate_id, ipo_id)).fetchone()
        
        if existing_application:
            return render_template(
                'success.html',
                message="Error: You have already applied for this IPO. You cannot apply more than once.",
                redirect_url=url_for('candidate.my_applications')
            )
        
        # --- Auto-rejection check ---
        if lots_applied > remaining_lots:
            db.execute(
                """INSERT INTO ipo_applications (candidate_id, ipo_id, lots_applied, status) 
                   VALUES (?, ?, ?, 'Rejected')""",
                (candidate_id, ipo_id, lots_applied)
            )
            db.commit()
            
            return render_template(
                'success.html', 
                message=f"Application Auto-Rejected: You applied for {lots_applied} lots, but only {remaining_lots} are available.", 
                redirect_url=url_for('candidate.my_applications')
            )

        # If all checks pass, insert as 'Pending'
        db.execute(
            "INSERT INTO ipo_applications (candidate_id, ipo_id, lots_applied) VALUES (?, ?, ?)",
            (candidate_id, ipo_id, lots_applied)
        )
        db.commit()
        
        return render_template(
            'success.html', 
            message="Application Submitted Successfully!", 
            redirect_url=url_for('candidate.my_applications')
        )

    # For GET request
    return render_template(
        'apply_ipo.html', 
        ipo=ipo_details, 
        remaining_lots=remaining_lots, 
        title=f"Apply for {ipo_details['company_name']}"
    )

@candidate_bp.route('/applications')
def my_applications():
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate.login'))
    db = get_db()
    # --- THIS QUERY IS NOW CORRECT ---
    applications = db.execute("""
        SELECT 
            i.company_name, 
            i.issue_price, 
            a.lots_applied, 
            a.status,
            a.id as application_id -- This line is required
        FROM ipo_applications a 
        JOIN ipos i ON a.ipo_id = i.id
        WHERE a.candidate_id = ? ORDER BY a.id DESC
    """, (session['user_id'],)).fetchall()
    return render_template('my_applications.html', applications=applications, title="My Applications")

# --- THIS IS THE NEW ROUTE FOR THE ALLOTMENT REPORT ---
@candidate_bp.route('/allotment/<int:application_id>')
def view_allotment(application_id):
    """Shows a candidate their personal allotment confirmation."""
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate.login'))
    
    db = get_db()
    
    # Security Check: Fetch the application AND join IPO details
    # Make sure this application belongs to the logged-in candidate and is Approved
    allotment_data = db.execute("""
        SELECT
            a.id,
            a.lots_applied,
            i.company_name,
            i.issue_price,
            i.lot_size
        FROM ipo_applications a
        JOIN ipos i ON a.ipo_id = i.id
        WHERE a.id = ? AND a.candidate_id = ? AND a.status = 'Approved'
    """, (application_id, session['user_id'])).fetchone()

    if not allotment_data:
        abort(404) # Not found, not theirs, or not approved yet

    return render_template(
        'candidate_allotment.html',
        allotment=allotment_data,
        title="Allotment Confirmation"
    )