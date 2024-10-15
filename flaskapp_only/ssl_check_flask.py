from flask import Flask, request, jsonify
from datetime import datetime
from urllib.parse import urlparse
import ssl
import socket
import sqlite3

app = Flask(__name__)

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

# Function to get the number of days until the SSL certificate expires for a domain
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
        print(f"{domain}: Could not retrieve SSL certificate. Error: {e}")
        return None

# Extract domain from URL
def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    return domain

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

# Flask route for certificate expiry API
@app.route('/certificate_expiry', methods=['GET'])
def certificate_expiry():
    # Get the query parameter for the domain(s)
    domains = request.args.get('domain')
    if not domains:
        return jsonify({"error": "No domain provided"}), 400

    # Split multiple domains by comma
    domain_list = domains.split(',')

    # Initialize a list to hold the response data
    response_data = []

    # Iterate through each domain
    for domain in domain_list:
        domain = extract_domain(domain.strip())
        days_left = get_ssl_expiry_days(domain)
        if days_left is not None:
            # Save result to the database
            save_to_db(domain, days_left)
            # Add to the response list
            response_data.append({
                "domain": domain,
                "days_left": days_left
            })
        else:
            response_data.append({
                "domain": domain,
                "error": "Could not retrieve SSL certificate."
            })

    # Return the list of results as JSON
    return jsonify(response_data)

# Flask route to get stored SSL info from the database
@app.route('/get_stored_data', methods=['GET'])
def get_stored_data():
    conn = sqlite3.connect('ssl_checker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT domain, days_left, last_checked FROM ssl_info ORDER BY days_left ASC')
    rows = cursor.fetchall()
    conn.close()

    # Convert the rows into a list of dictionaries
    result = [{"domain": row[0], "days_left": row[1], "last_checked": row[2]} for row in rows]


    return jsonify(result)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
