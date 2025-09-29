from flask import Flask
import os.path, sys

sys.path.append(os.path.expanduser(f"~/machineinv"))
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from app.sync_handshake import sync_handler

# Create instances of extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    # Add sync handler to app context
    app.sync_handler = sync_handler
    # Import models to ensure they're registered
    from app.models import User, Role, Equipment, Service, Category, Location, Component

    # Import and register routes
    from app import routes

    routes.init_app(app)

    # Create database tables (if they don't exist)
    with app.app_context():
        db.create_all()
        Role.insert_roles()

    return app
