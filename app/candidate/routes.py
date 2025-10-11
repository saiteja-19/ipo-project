# app/candidate/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_db
import sqlite3

candidate_bp = Blueprint('candidate', __name__)

@candidate_bp.route('/register', methods=['GET', 'POST'])
def register():
    # ... (Copy the logic from candidate_register in old app.py) ...
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        try:
            db.execute("INSERT INTO candidates (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            db.commit()
            return render_template('success.html', message="Candidate Registration Successful!", redirect_url=url_for('candidate.login'))
        except sqlite3.IntegrityError:
            error = "A candidate with this email already exists."
            return render_template('candidate_register.html', error=error)
    return render_template('candidate_register.html', title="Candidate Registration")


@candidate_bp.route('/login', methods=['GET', 'POST'])
def login():
    # ... (Copy the logic from candidate_login) ...
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        candidate = db.execute("SELECT * FROM candidates WHERE email = ? AND password = ?", (email, password)).fetchone()
        if candidate:
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
    # ... (Copy the logic from apply_ipo) ...
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate.login'))
    db = get_db()
    ipo = db.execute("SELECT * FROM ipos WHERE id = ?", (ipo_id,)).fetchone()
    if not ipo:
        return "IPO not found!", 404
    if request.method == 'POST':
        db.execute("INSERT INTO ipo_applications (candidate_id, ipo_id, lots_applied) VALUES (?, ?, ?)",
                  (session['user_id'], ipo_id, request.form['lots']))
        db.commit()
        return render_template('success.html', message="Application Submitted Successfully!", redirect_url=url_for('candidate.my_applications'))
    return render_template('apply_ipo.html', ipo=ipo, title=f"Apply for {ipo['company_name']}")

@candidate_bp.route('/applications')
def my_applications():
    # ... (Copy the logic from my_applications) ...
    if session.get('user_type') != 'candidate':
        return redirect(url_for('candidate.login'))
    db = get_db()
    applications = db.execute("""
        SELECT i.company_name, i.issue_price, a.lots_applied, a.status 
        FROM ipo_applications a JOIN ipos i ON a.ipo_id = i.id
        WHERE a.candidate_id = ? ORDER BY a.id DESC
    """, (session['user_id'],)).fetchall()
    return render_template('my_applications.html', applications=applications, title="My Applications")