from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "a_very_secret_and_complex_key"

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = sqlite3.connect('ipo.db')
    c = conn.cursor()
    
    # Table for user/company registration details
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    cin TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    sector TEXT NOT NULL
                )''')

    # NEW: Table to store the IPO listings for the index page
    c.execute('''CREATE TABLE IF NOT EXISTS ipos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    issue_price TEXT NOT NULL,
                    lot_size INTEGER NOT NULL,
                    open_date TEXT NOT NULL,
                    close_date TEXT NOT NULL
                )''')

    # MODIFIED: Table for applications, linking a user to an IPO
    c.execute('''CREATE TABLE IF NOT EXISTS ipo_applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    applicant_id INTEGER,
                    ipo_id INTEGER,
                    lots_applied INTEGER NOT NULL,
                    status TEXT DEFAULT 'Pending',
                    FOREIGN KEY (applicant_id) REFERENCES companies (id),
                    FOREIGN KEY (ipo_id) REFERENCES ipos (id)
                )''')

    # Add sample IPO data if the table is empty
    c.execute("SELECT COUNT(*) FROM ipos")
    if c.fetchone()[0] == 0:
        sample_ipos = [
            ('Innovate Tech Ltd', '₹450 - ₹465', 32, '2025-11-10', '2025-11-14'),
            ('Green Energy Corp', '₹810 - ₹825', 18, '2025-11-18', '2025-11-22'),
            ('HealthFirst Pharma', '₹620 - ₹630', 24, '2025-11-25', '2025-11-29')
        ]
        c.executemany("INSERT INTO ipos (company_name, issue_price, lot_size, open_date, close_date) VALUES (?, ?, ?, ?, ?)", sample_ipos)

    conn.commit()
    conn.close()

@app.route('/')
def index():
    """NEW: The main index page, displaying all available IPOs."""
    conn = sqlite3.connect('ipo.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM ipos")
    ipos = c.fetchall()
    conn.close()
    return render_template('index.html', ipos=ipos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles company registration."""
    if request.method == 'POST':
        name = request.form['name']
        cin = request.form['cin']
        email = request.form['email']
        password = request.form['password']
        sector = request.form['sector']

        conn = sqlite3.connect('ipo.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO companies (name, cin, email, password, sector) VALUES (?, ?, ?, ?, ?)",
                      (name, cin, email, password, sector))
            conn.commit()
            msg = "Registration successful! You can now log in."
            return render_template('success.html', message=msg, redirect_url=url_for('login_page'))
        except sqlite3.IntegrityError:
            error = "Registration failed. A company with this CIN or Email already exists."
            return render_template('register.html', error=error)
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handles company login."""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('ipo.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM companies WHERE email=? AND password=?", (email, password))
        company = c.fetchone()
        conn.close()

        if company:
            session['company_id'] = company['id']
            session['company_name'] = company['name']
            return redirect(url_for('index'))
        else:
            error = "Invalid email or password. Please try again."
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/apply_ipo/<int:ipo_id>', methods=['GET', 'POST'])
def apply_ipo_page(ipo_id):
    """Shows the form to apply for a specific IPO and handles submission."""
    if 'company_id' not in session:
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('ipo.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM ipos WHERE id = ?", (ipo_id,))
    ipo = c.fetchone()
    
    if not ipo:
        conn.close()
        return "IPO not found!", 404

    if request.method == 'POST':
        lots_applied = request.form['lots']
        applicant_id = session['company_id']

        c.execute("INSERT INTO ipo_applications (applicant_id, ipo_id, lots_applied) VALUES (?, ?, ?)",
                  (applicant_id, ipo_id, lots_applied))
        conn.commit()
        conn.close()
        
        return render_template('success.html', message="Application Submitted Successfully!", redirect_url=url_for('view_applications'))

    conn.close()
    return render_template('apply_ipo.html', ipo=ipo)

@app.route('/applications')
def view_applications():
    """Displays a list of applications submitted by the logged-in user."""
    if 'company_id' not in session:
        return redirect(url_for('login_page'))

    conn = sqlite3.connect('ipo.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    applicant_id = session['company_id']
    c.execute("""
        SELECT 
            i.company_name, 
            i.issue_price,
            a.lots_applied, 
            a.status 
        FROM ipo_applications a
        JOIN ipos i ON a.ipo_id = i.id
        WHERE a.applicant_id = ?
    """, (applicant_id,))
    applications = c.fetchall()
    conn.close()

    return render_template('applications.html', applications=applications)

@app.route('/logout')
def logout():
    """Logs the user out."""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
