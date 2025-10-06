from flask import Flask, render_template, request, redirect, url_for
import sqlite3, random

app = Flask(__name__)

# -------- Database Setup --------
def init_db():
    conn = sqlite3.connect("ipo.db")
    c = conn.cursor()

    # IPO table
    c.execute("""CREATE TABLE IF NOT EXISTS ipo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    price_low INTEGER,
                    price_high INTEGER,
                    lot_size INTEGER,
                    open_date TEXT,
                    close_date TEXT
                )""")

    # Applications table
    c.execute("""CREATE TABLE IF NOT EXISTS application (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor TEXT,
                    ipo_id INTEGER,
                    lots INTEGER,
                    bid_price INTEGER,
                    payment_mode TEXT,
                    payment_status TEXT,
                    exchange_ack TEXT
                )""")

    # Insert sample IPOs if empty
    c.execute("SELECT COUNT(*) FROM ipo")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO ipo (name, price_low, price_high, lot_size, open_date, close_date) VALUES (?, ?, ?, ?, ?, ?)",
                  ("Acme Corp", 90, 100, 10, "2025-10-01", "2025-10-05"))
        c.execute("INSERT INTO ipo (name, price_low, price_high, lot_size, open_date, close_date) VALUES (?, ?, ?, ?, ?, ?)",
                  ("Globex Ltd", 120, 130, 15, "2025-10-06", "2025-10-14"))
    conn.commit()
    conn.close()

# -------- Routes --------
@app.route("/")
def home():
    conn = sqlite3.connect("ipo.db")
    c = conn.cursor()
    c.execute("SELECT * FROM ipo")
    ipos = c.fetchall()

    c.execute("SELECT a.id, a.investor, i.name, a.lots, a.bid_price, a.payment_mode, a.payment_status, a.exchange_ack \
               FROM application a JOIN ipo i ON a.ipo_id = i.id")
    applications = c.fetchall()
    conn.close()
    return render_template("index.html", ipos=ipos, applications=applications)

@app.route("/apply/<int:ipo_id>", methods=["GET", "POST"])
def apply(ipo_id):
    conn = sqlite3.connect("ipo.db")
    c = conn.cursor()
    c.execute("SELECT * FROM ipo WHERE id=?", (ipo_id,))
    ipo = c.fetchone()

    if request.method == "POST":
        investor = "Demo Investor"
        lots = int(request.form["lots"])
        bid_price = int(request.form["bid_price"])
        payment_mode = request.form["payment_mode"]
        payment_status = "SUBMITTED"
        exchange_ack = "EXCH_ACK_" + str(random.randint(10000, 99999))

        c.execute("INSERT INTO application (investor, ipo_id, lots, bid_price, payment_mode, payment_status, exchange_ack) \
                   VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (investor, ipo_id, lots, bid_price, payment_mode, payment_status, exchange_ack))
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    conn.close()
    return render_template("apply.html", ipo=ipo)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)