# app/main/routes.py

from flask import Blueprint, render_template, session, redirect, url_for
from app.db import get_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    db = get_db()
    # This query now calculates total approved lots for each IPO
    ipos = db.execute("""
        SELECT
            i.id,
            i.company_name,
            i.issue_price,
            i.lot_size,
            i.total_lots,
            i.open_date,
            i.close_date,
            COALESCE(SUM(CASE WHEN a.status = 'Approved' THEN a.lots_applied ELSE 0 END), 0) as approved_lots
        FROM ipos i
        LEFT JOIN ipo_applications a ON i.id = a.ipo_id
        GROUP BY i.id
        ORDER BY i.id DESC
    """).fetchall()
    return render_template('index.html', ipos=ipos, title="Available IPOs")

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))