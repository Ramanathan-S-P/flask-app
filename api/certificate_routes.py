from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from db_operations import (
    add_domain,
    get_all_domains,
    get_domain_by_id,
    update_domain,
    delete_domain,
    get_ssl_expiry_days,
    save_to_db,
    SessionLocal  # Import the session factory from db_operations
)

# Initialize the blueprint
certificate_bp = Blueprint('certificate', __name__)

# Dependency to get the database session
def get_db_session():
    """Opens a new database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# List all domains
@certificate_bp.route('/domain/', methods=['GET'])
def list_domains():
    with SessionLocal() as session:
        domains = get_all_domains()
        res = [{"id": row.id, "name": row.name, "days_left": row.days_left, "last_checked": row.last_checked} for row in domains]
    return jsonify({"Domains": res}), 200

# Get details of a specific domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['GET'])
def get_domain(domain_id):
    with SessionLocal() as session:
        domain = get_domain_by_id( domain_id)
        if domain:
            return jsonify({"id": domain.id, "name": domain.name, "days_left": domain.days_left, "last_checked": domain.last_checked}), 200
        return jsonify({"error": "Domain not found"}), 404

# Add a new domain
@certificate_bp.route('/domain/', methods=['POST'])
def add_new_domain():
    data = request.json
    domain_name = data.get('name')

    with SessionLocal() as session:
        add_domain( domain_name)
        session.commit()
    
    return jsonify({"message": "Domain added", "name": domain_name}), 201

# Edit an existing domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['PUT'])
def edit_domain(domain_id):
    data = request.json
    domain_name = data.get('name')

    with SessionLocal() as session:
        update_domain( domain_id, domain_name)
        session.commit()

    return jsonify({"message": "Domain updated", "id": domain_id}), 200

# Delete a specific domain
@certificate_bp.route('/domain/<int:domain_id>/', methods=['DELETE'])
def remove_domain(domain_id):
    with SessionLocal() as session:
        delete_domain( domain_id)
        session.commit()

    return jsonify({"message": "Domain deleted"}), 200

# Get the SSL expiry for a specific domain and update the database
@certificate_bp.route('/domain/expiry/<int:domain_id>/', methods=['GET'])
def get_domain_expiry(domain_id):
    with SessionLocal() as session:
        domain = get_domain_by_id( domain_id)
        if domain:
            days_left = get_ssl_expiry_days(domain.name)  # domain.name refers to the domain name
            save_to_db( domain.name, days_left)  # Save updated expiry days to DB
            session.commit()
            return jsonify({"domain": domain.name, "days_left": days_left}), 200
        return jsonify({"error": "Domain not found"}), 404

# Get expiry for all domains and refresh the database
@certificate_bp.route('/domain/expiry/', methods=['GET'])
def get_all_domains_expiry():
    expiry_info = []

    with SessionLocal() as session:
        domains = get_all_domains()
        for domain in domains:
            days_left = get_ssl_expiry_days(domain.name)  # domain.name refers to the domain name
            save_to_db( domain.name, days_left)  # Update the expiry information in the database
            expiry_info.append({"domain": domain.name, "days_left": days_left})
        session.commit()

    return jsonify(expiry_info), 200
