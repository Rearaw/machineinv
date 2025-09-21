from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), nullable=False)

    role = db.relationship("Role", back_populates="users")
    services = db.relationship("Service", back_populates="service_by")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.user_id)


class EquipmentImage(db.Model):
    __tablename__ = "equipment_images"
    image_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)  # Stores the image filename
    equipment_id = db.Column(
        db.Integer, db.ForeignKey("equipments.equipment_id"), nullable=False
    )

    equipment = db.relationship("Equipment", back_populates="images")


# Add relationship in Equipment model
class Equipment(db.Model):
    __tablename__ = "equipments"
    equipment_id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(50), unique=True, nullable=False)
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    status = db.Column(db.String(50))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.location_id"))
    category_id = db.Column(db.Integer, db.ForeignKey("categories.category_id"))

    location = db.relationship("Location", back_populates="equipments")
    category = db.relationship("Category", back_populates="equipments")
    images = db.relationship(
        "EquipmentImage", back_populates="equipment", cascade="all, delete-orphan"
    )
    services = db.relationship(
        "Service", back_populates="equipment", cascade="all, delete-orphan"
    )


class Category(db.Model):  # One-to-Many with Equipment
    __tablename__ = "categories"
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)

    equipments = db.relationship("Equipment", back_populates="category")


class Location(db.Model):  # One-to-Many with Equipment
    __tablename__ = "locations"
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    location_description = db.Column(db.String(255), nullable=False)

    equipments = db.relationship("Equipment", back_populates="location")


class Component(db.Model):  # One-to-One with Service
    __tablename__ = "components"
    component_id = db.Column(db.Integer, primary_key=True)
    component_name = db.Column(db.String(100), nullable=False)
    component_serial_number = db.Column(db.String(100), nullable=False)
    component_install_date = db.Column(db.Date, nullable=False)

    service_id = db.Column(db.Integer, db.ForeignKey("services.service_id"))
    service = db.relationship(
        "Service", back_populates="component", uselist=False
    )  # One-to-One


class Service(db.Model):  # One-to-One with Equipment & Component, Many-to-One with User
    __tablename__ = "services"
    service_id = db.Column(db.Integer, primary_key=True)
    service_date = db.Column(db.Date, nullable=False)
    service_description = db.Column(db.String(255), nullable=False)
    service_hours = db.Column(db.Integer, nullable=False)
    service_cost = db.Column(db.Float, nullable=False)
    service_next_date = db.Column(db.Date, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipments.equipment_id"))

    service_by = db.relationship("User", back_populates="services")
    equipment = db.relationship("Equipment", back_populates="services")
    component = db.relationship(
        "Component", back_populates="service", uselist=False
    )  # One-to-One


class Role(db.Model):  # One-to-Many with Users
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(100), nullable=False)

    users = db.relationship("User", back_populates="role")

    @staticmethod
    def insert_roles():
        predefined_roles = ["admin", "technician"]

        for role_name in predefined_roles:
            role = Role.query.filter_by(role_name=role_name).first()
            if role is None:
                new_role = Role(role_name=role_name)
                db.session.add(new_role)
        db.session.commit()
