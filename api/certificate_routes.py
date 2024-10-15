from flask import Blueprint, request, jsonify, g

import sqlite3
from db_operations import (
    add_domain,
    get_all_domains,
    get_domain_by_id,
    update_domain,
    delete_domain,
    get_ssl_expiry_days,
    save_to_db,
)

# Initialize the blueprint
certificate_bp = Blueprint('certificate', __name__)





# Function to get a database connection
def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect('ssl_checker.db')
    return g.db

# List all domains
@certificate_bp.route('/domain/', methods=['GET'])
def list_domains():
    conn = get_db_connection()
    domains = get_all_domains(conn)
    return jsonify(domains)

# Get details of a specific domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['GET'])
def get_domain(domain_id):
    conn = get_db_connection()
    domain = get_domain_by_id(conn, domain_id)
    if domain:
        return jsonify(domain)
    return jsonify({"error": "Domain not found"}), 404

# Add a new domain
@certificate_bp.route('/domain/', methods=['POST'])
def add_new_domain():
    conn = get_db_connection()
    data = request.json
    domain_name = data.get('name')
    add_domain(conn, domain_name)
    return jsonify({"message": "Domain added", "name": domain_name}), 201

# Edit an existing domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['PUT'])
def edit_domain(domain_id):
    conn = get_db_connection()
    data = request.json
    domain_name = data.get('name')
    update_domain(conn, domain_id, domain_name)
    return jsonify({"message": "Domain updated", "id": domain_id}), 200

# Delete a specific domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['DELETE'])
def remove_domain(domain_id):
    conn = get_db_connection()
    delete_domain(conn, domain_id)
    return jsonify({"message": "Domain deleted"}), 200

# Get the expiry for a specific domain and update the database
@certificate_bp.route('/domain/expiry/<int:domain_id>/', methods=['GET'])
def get_domain_expiry(domain_id):
    conn = get_db_connection()
    domain = get_domain_by_id(conn, domain_id)
    if domain:
        days_left = get_ssl_expiry_days(domain[1])  # Assuming the domain name is in the second column
        save_to_db(conn, domain[1], days_left)  # Save updated expiry days to DB
        return jsonify({"domain": domain[1], "days_left": days_left}), 200
    return jsonify({"error": "Domain not found"}), 404

# Get expiry for all domains and refresh the database
@certificate_bp.route('/domain/expiry/', methods=['GET'])
def get_all_domains_expiry():
    conn = get_db_connection()
    domains = get_all_domains(conn)
    expiry_info = []
    
    for domain in domains:
        days_left = get_ssl_expiry_days(domain[1])  # domain[1] is the domain name
        save_to_db(conn, domain[1], days_left)  # Update the expiry information in the database
        expiry_info.append({"domain": domain[1], "days_left": days_left})

    return jsonify(expiry_info), 200

# Close the database connection after each request
@certificate_bp.teardown_app_request
def close_db_connection(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()
