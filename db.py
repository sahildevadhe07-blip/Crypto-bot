import sqlite3
import os

DATABASE_NAME = os.environ.get("DATABASE_NAME", "alerts.db") # Use an env var for DB path

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            target_price REAL NOT NULL,
            status TEXT DEFAULT 'active' -- 'active', 'triggered', 'deactivated'
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized.")

def add_alert(chat_id, user_id, symbol, target_price):
    """Adds a new alert to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO alerts (chat_id, user_id, symbol, target_price) VALUES (?, ?, ?, ?)",
        (chat_id, user_id, symbol, target_price)
    )
    conn.commit()
    conn.close()

def get_active_alerts_for_user(user_id):
    """Retrieves all active alerts for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, symbol, target_price FROM alerts WHERE user_id=? AND status='active'",
        (user_id,)
    )
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def get_all_active_alerts():
    """Retrieves all active alerts from the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, chat_id, user_id, symbol, target_price FROM alerts WHERE status='active'"
    )
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def deactivate_alert(alert_id):
    """Deactivates an alert by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE alerts SET status='deactivated' WHERE id=?",
        (alert_id,)
    )
    conn.commit()
    conn.close()
