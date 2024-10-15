import ssl
import socket
import click
from datetime import datetime
from urllib.parse import urlparse

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

# Simple URL validation and domain extraction
def extract_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path
    return domain

# Click command-line interface setup
@click.command()
@click.argument('text_file', type=click.File('r'))
def check_ssl_expiry(text_file):
    """
    Script to check SSL expiry days for websites provided in a text file.
    Each line of the text file should contain one website URL.
    """
    # Declare a list to store expiry days and domains
    expiry_info = []

    # Read the text file and process each line
    for line in text_file:
        website = line.strip()  # Removing any surrounding whitespace
        if website:
            domain = extract_domain(website)
            days_left = get_ssl_expiry_days(domain)
            if days_left is not None:
                expiry_info.append((days_left, domain))
            else:
                print(f"{website}: Invalid URL or error occurred, skipping.")

    # Sort the expiry information by days remaining and display it
    print("website =>=>=> days_left")
    print("------- =>=>=> ---------")
    for days_left, domain in sorted(expiry_info):
        print(f"{domain} =>=>=> {days_left}")

if __name__ == "__main__":
    check_ssl_expiry()
