import sqlite3
from datetime import datetime

# Initialize SQLite DB and create a table if it doesn't exist
def init_db():
    conn = sqlite3.connect('ssl_checker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ssl_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE,
            days_left INTEGER,
            last_checked TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Save SSL info to the database
def save_to_db(domain, days_left):
    conn = sqlite3.connect('ssl_checker.db')
    cursor = conn.cursor()
    last_checked = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT OR REPLACE INTO ssl_info (domain, days_left, last_checked)
        VALUES (?, ?, ?)
    ''', (domain, days_left, last_checked))
    conn.commit()
    conn.close()

# Fetch stored SSL info from the database
def get_stored_data():
    conn = sqlite3.connect('ssl_checker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT domain, days_left, last_checked FROM ssl_info ORDER BY days_left ASC')
    rows = cursor.fetchall()
    conn.close()
    return [{"domain": row[0], "days_left": row[1], "last_checked": row[2]} for row in rows]
