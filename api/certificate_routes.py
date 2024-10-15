from flask import Blueprint, request, jsonify
from urllib.parse import urlparse
from datetime import datetime
import ssl
import socket
from db_operations import save_to_db, get_stored_data

# Create a blueprint for certificate-related routes
certificate_blueprint = Blueprint('certificate', __name__)

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

# Route to check certificate expiry for a domain
@certificate_blueprint.route('/certificate_expiry', methods=['GET'])
def certificate_expiry():
    domains = request.args.get('domain')
    if not domains:
        return jsonify({"error": "No domain provided"}), 400

    domain_list = domains.split(',')
    response_data = []

    for domain in domain_list:
        domain = extract_domain(domain.strip())
        days_left = get_ssl_expiry_days(domain)
        if days_left is not None:
            save_to_db(domain, days_left)
            response_data.append({
                "domain": domain,
                "days_left": days_left
            })
        else:
            response_data.append({
                "domain": domain,
                "error": "Could not retrieve SSL certificate."
            })

    return jsonify(response_data)

# Route to fetch stored SSL info from the database
@certificate_blueprint.route('/get_stored_data', methods=['GET'])
def fetch_stored_data():
    stored_data = get_stored_data()
    return jsonify(stored_data)

# POST route to add new domains
@certificate_blueprint.route('/add_domain', methods=['POST'])
def add_domain():
    data = request.json
    if 'domain' not in data:
        return jsonify({"error": "Domain is required."}), 400

    domain = extract_domain(data['domain'].strip())
    days_left = get_ssl_expiry_days(domain)
    if days_left is not None:
        save_to_db(domain, days_left)
        return jsonify({"domain": domain, "days_left": days_left}), 201
    else:
        return jsonify({"error": f"Could not retrieve SSL certificate for {domain}."}), 400
