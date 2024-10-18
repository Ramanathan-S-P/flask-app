from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import ssl
import socket
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(levelname)s - %(message)s',  
    handlers=[
        logging.FileHandler("ssl_checker.log"), 
        logging.StreamHandler()  
    ]
)

# MySQL connection setup (adjust with your MySQL credentials)
DATABASE_URL = 'mysql+pymysql://root:ramanathan@localhost/ssl_checker'

# Set up SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()

# Define the Domain model
class Domain(Base):
    __tablename__ = 'domains'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    days_left = Column(Integer, nullable=True)
    last_checked = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('name', name='uix_1'),  # Ensure domain names are unique
    )

# Create the table
def init_db():
    Base.metadata.create_all(bind=engine)

# Session setup
SessionLocal = sessionmaker(bind=engine)
session=SessionLocal()

def add_domain(domain_name):
    try:
        domain = Domain(name=domain_name)
        session.add(domain)
        session.commit()
    except Exception as e:
        session.rollback()  # Rollback on error
        logging.error(f"Error adding domain {domain_name}: {e}")

def get_all_domains():
    try:
        domains = session.query(Domain).all()
        return domains
    except Exception as e:
        logging.error(f"Error retrieving domains: {e}")
        return []

def get_domain_by_id(domain_id):
    try:
        domain = session.query(Domain).get(domain_id)
        return domain
    except Exception as e:
        logging.error(f"Error retrieving domain with ID {domain_id}: {e}")
        return None

def update_domain(domain_id, domain_name):
    try:
        domain = session.query(Domain).get(domain_id)
        if domain:
            domain.name = domain_name
            session.commit()
        else:
            logging.error(f"Domain with ID {domain_id} not found.")
    except Exception as e:
        session.rollback()
        logging.error(f"Error updating domain {domain_name}: {e}")

def delete_domain(domain_id):
    try:
        domain = session.query(Domain).get(domain_id)
        if domain:
            session.delete(domain)
            session.commit()
        else:
            logging.error(f"Domain with ID {domain_id} not found.")
    except Exception as e:
        session.rollback()
        logging.error(f"Error deleting domain {domain_id}: {e}")

def save_to_db(domain, days_left):
    try:
        last_checked = datetime.utcnow()
        domain_record = session.query(Domain).filter_by(name=domain).first()
        if domain_record:
            domain_record.days_left = days_left
            domain_record.last_checked = last_checked
        else:
            new_domain = Domain(name=domain, days_left=days_left, last_checked=last_checked)
            session.add(new_domain)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"Error saving domain {domain}: {e}")

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
