from app import db
from flask_login import UserMixin

from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)  # Primary key is `user_id`, not `id`
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., 'admin', 'technician'

    # Override get_id to return `user_id` instead of `id`
    def get_id(self):
        return str(self.user_id)  # Flask-Login requires the ID to be a string

class Machine(db.Model):
    __tablename__ = 'machines'
    machine_id = db.Column(db.Integer, primary_key=True)
    machine_name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    status = db.Column(db.String(50))
    last_service_date = db.Column(db.Date)