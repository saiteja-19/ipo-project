# app/db.py

import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    """Connect to the application's configured database. The connection is unique for each request and will be reused if this is called again."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            'ipo.db', # We'll keep the db file in the root for simplicity
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """If this request connected to the database, close the connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Clear existing data and create new tables."""
    db = get_db()
    
    # Run the CREATE TABLE statements
    # (Same SQL statements from your original app.py)
    db.executescript('''
        DROP TABLE IF EXISTS companies;
        DROP TABLE IF EXISTS candidates;
        DROP TABLE IF EXISTS ipos;
        DROP TABLE IF EXISTS ipo_applications;

        CREATE TABLE companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cin TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            sector TEXT NOT NULL
        );
        CREATE TABLE candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        CREATE TABLE ipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            issue_price TEXT NOT NULL,
            lot_size INTEGER NOT NULL,
            total_lots INTEGER NOT NULL, 
            open_date TEXT NOT NULL,
            close_date TEXT NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        CREATE TABLE ipo_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            ipo_id INTEGER NOT NULL,
            lots_applied INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (candidate_id) REFERENCES candidates (id),
            FOREIGN KEY (ipo_id) REFERENCES ipos (id)
        );
    ''')

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Command to initialize the database."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app. This is called by the application factory."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)