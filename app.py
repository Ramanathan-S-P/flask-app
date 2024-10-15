from flask import Flask
from db_operations import init_db
from api.certificate_routes import certificate_bp

app = Flask(__name__)

# Register the blueprint for SSL certificate management
app.register_blueprint(certificate_bp)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
