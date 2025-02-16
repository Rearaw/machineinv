from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Create instances of extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)

    # Import and register routes
    from app import routes
    routes.init_app(app)

    # Create database tables (if they don't exist)
    with app.app_context():
        db.create_all()

    return app