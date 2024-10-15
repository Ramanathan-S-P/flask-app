import sqlite3
from datetime import datetime
import ssl
import socket
import logging
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
        logging.FileHandler("ssl_checker.log"), 
        logging.StreamHandler()  
    ]
)
def init_db():
    conn = sqlite3.connect('ssl_checker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            days_left INTEGER,
            last_checked TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_domain(conn, domain_name):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO domains (name) VALUES (?)
    ''', (domain_name,))
    conn.commit()

def get_all_domains(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM domains')
    rows = cursor.fetchall()
    return rows

def get_domain_by_id(conn, domain_id):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM domains WHERE id = ?', (domain_id,))
    row = cursor.fetchone()
    return row

def update_domain(conn, domain_id, domain_name):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE domains SET name = ? WHERE id = ?
    ''', (domain_name, domain_id))
    conn.commit()

def delete_domain(conn, domain_id):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM domains WHERE id = ?', (domain_id,))
    conn.commit()

def save_to_db(conn, domain, days_left):
    cursor = conn.cursor()
    last_checked = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT OR REPLACE INTO domains (name, days_left, last_checked)
        VALUES (?, ?, ?)
    ''', (domain, days_left, last_checked))
    conn.commit()

def get_ssl_expiry_days(domain):
    try:
        context = ssl.create_default_context()
        conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=domain)
        conn.settimeout(5.0)
        conn.connect((domain, 443))
        cert = conn.getpeercert()
        expiry_date_str = cert['notAfter']
        expiry_date = datetime.strptime(expiry_date_str, "%b %d %H:%M:%S %Y %Z")
        days_left = (expiry_date - datetime.utcnow()).days
        return days_left
    except Exception as e:
        logging.error(f"{domain}: Could not retrieve SSL certificate. Error: {e}")
        return None
