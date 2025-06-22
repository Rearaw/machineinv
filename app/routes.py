from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User, Role, Equipment, Service,Component,Category,Location,EquipmentImage
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

BASE_DIR=os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR,"static","uploads")
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp'}

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):

    os.makedirs(UPLOAD_FOLDER,exist_ok=True)


def init_app(app):
    print("Registering routes...") 

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Load user by `user_id`

    @app.route('/')
    def index():
        equipments = Equipment.query.all()
        return render_template('index.html', equipments=equipments)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):  # 🔹 Verify password
                login_user(user)
                flash('Logged in successfully!', 'success')
                next_url = session.pop('next_url', None)
                return redirect(next_url or url_for('equipments'))
                
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))
    @app.route('/admin/dashboard')
    @login_required
    def admin_dashboard():
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))

        total_machines = Equipment.query.count()
        total_users = User.query.count()

        today = datetime.today().date()
        upcoming_threshold = today + timedelta(days=3)

        # Get all equipment with upcoming/overdue services
        overdue_equipments = (
            db.session.query(Equipment)
            .join(Service)
            .filter(Service.service_next_date <= upcoming_threshold)
            .order_by(Service.service_next_date.asc())
            .all()
        )

        overdue_count = len(overdue_equipments)

        return render_template(
            'admin_dashboard.html',
            total_machines=total_machines,
            total_users=total_users,
            overdue_equipments=overdue_equipments,
            overdue_count=overdue_count
        )


        @app.route('/api/reschedule/<int:equipment_id>', methods=['POST'])
        @login_required
        def api_reschedule(equipment_id):
            data = request.get_json()
            new_date = datetime.strptime(data['new_date'], '%Y-%m-%d').date()

            latest_service = Service.query.filter_by(equipment_id=equipment_id).order_by(Service.service_date.desc()).first()
            if latest_service:
                latest_service.service_next_date = new_date
                db.session.commit()
                return jsonify({"success": True})
            return jsonify({"success": False}), 404

    @app.route('/equipments', methods=['GET'])
    @login_required
    def equipments():
        search_query = request.args.get('search', '').strip()
        location_filter = request.args.get('location', '')
        category_filter = request.args.get('category', '')
        status_filter = request.args.get('status', '')

        query = Equipment.query

        # Apply search filter (by name or serial number)
        if search_query:
            query = query.filter(
                (Equipment.equipment_name.ilike(f"%{search_query}%")) | 
                (Equipment.serial_number.ilike(f"%{search_query}%"))
            )

        # Apply location filter
        if location_filter:
            query = query.filter(Equipment.location_id == location_filter)

        # Apply category filter
        if category_filter:
            query = query.filter(Equipment.category_id == category_filter)

        # Apply status filter
        if status_filter:
            query = query.filter(Equipment.status == status_filter)

        # Get filtered results
        equipments = query.all()

        # Get all locations and categories for the filter dropdowns
        locations = Location.query.all()
        categories = Category.query.all()

        return render_template('equipments.html', equipments=equipments, locations=locations, categories=categories)

    @app.route('/register', methods=['GET', 'POST'])
    @login_required
    def register():
        if current_user.role_id != 1:
            flash("access denied: please contact your Adminstrator")
            return redirect(url_for('equipments'))
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            role_id = request.form['role_id']

            if User.query.filter_by(username=username).first():
                flash('Username already exists!', 'error')
                return redirect(url_for('register'))

            role = Role.query.get(role_id)
            if not role:
                flash('Invalid role selected!', 'error')
                return redirect(url_for('register'))

            new_user = User(username=username, role=role)
            new_user.set_password(password)  # 🔹 Hash the password before storing
            db.session.add(new_user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        roles = Role.query.all()
        return render_template('register.html', roles=roles)
    @app.route('/services')
    @login_required
    def services():
        services = Service.query.all()
        return render_template('services.html', services=services)

    @login_required
    @app.route('/categories')
    def categories():
        categories_with_counts = []
        all_categories = db.session.query(Category).all()
        for category in all_categories:
            machines = category.equipments  # Assuming backref on Equipment
            count = len(machines)
            categories_with_counts.append((category, count, machines))
        return render_template("categories.html", categories=categories_with_counts)

    
    @app.route('/add_category', methods=['GET', 'POST'])
    @login_required
    def add_category():
        if request.method == 'POST':
            category_name = request.form['category_name']
            description = request.form['description']
            new_category = Category(category_name=category_name, description=description)
            db.session.add(new_category)
            db.session.commit()
            flash('Category added successfully!', 'success')
            return redirect(url_for('categories'))
        return render_template('add_category.html')

    @app.route('/delete_category/<int:category_id>')
    @login_required
    def delete_category(category_id):
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
        return redirect(url_for('categories'))

    @app.route('/categories/<int:category_id>/machines')
    @login_required
    def view_category_machines(category_id):
        category = Category.query.get_or_404(category_id)
        equipments = Equipment.query.filter_by(category_id=category_id).all()
        return render_template('category_machines.html', category=category, equipments=equipments)

    @app.route('/add_equipment', methods=['GET', 'POST'])
    @login_required
    def add_equipment():
        if request.method == 'POST':
            equipment_name = request.form['equipment_name']
            serial_number = request.form['serial_number']
            purchase_date = request.form['purchase_date']
            warranty_expiry = request.form['warranty_expiry']
            status = request.form['status']
            location_id = request.form['location_id']
            category_id = request.form['category_id']

            # Convert dates
            purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date() if purchase_date else None
            warranty_expiry = datetime.strptime(warranty_expiry, '%Y-%m-%d').date() if warranty_expiry else None

            # ✅ Create new equipment record
            new_equipment = Equipment(
                equipment_name=equipment_name,
                serial_number=serial_number,
                purchase_date=purchase_date,
                warranty_expiry=warranty_expiry,
                status=status,
                location_id=location_id,
                category_id=category_id
            )
            db.session.add(new_equipment)
            db.session.commit()

            # ✅ Handle image uploads
            images = request.files.getlist('equipment_pictures')
            print("Uploaded files:", images)  # Debugging

            for image in images:
                if image and '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)

                    # ✅ Debugging: Check if filename is correct
                    print(f"Saving image: {filename} for equipment: {new_equipment.equipment_id}")

                    # ✅ Fix: Ensure image reference is added to the database
                    new_image = EquipmentImage(filename=filename, equipment=new_equipment)
                    db.session.add(new_image)

            db.session.commit()
            flash('Equipment added successfully with images!', 'success')
            return redirect(url_for('equipments'))

        locations = Location.query.all()
        categories = Category.query.all()
        return render_template('add_equipment.html', locations=locations, categories=categories)
    @app.route('/delete_equipment/<int:equipment_id>', methods=['POST'])
    @login_required
    def delete_equipment(equipment_id):
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))
        equipment = Equipment.query.get_or_404(equipment_id)

        try:
            # Delete all related images
            for image in equipment.images:
                image_path = os.path.join(UPLOAD_FOLDER, image.filename)
                if os.path.exists(image_path):
                    os.remove(image_path)  # ✅ Delete image file from storage
                db.session.delete(image)  # ✅ Remove image record from database

            # Delete related service records
            Service.query.filter_by(equipment_id=equipment_id).delete()

            # Delete the equipment itself
            db.session.delete(equipment)
            db.session.commit()

            return jsonify({"success": True})
        
        except Exception as e:
            print("Error deleting equipment:", e)
            return jsonify({"success": False}), 500
    
    
    
    
    @app.route('/equipment/<int:equipment_id>')
    @login_required
    def equipment_details(equipment_id):
        equipment = Equipment.query.get_or_404(equipment_id)
        
        # Fetch all service records for this equipment
        service_records = Service.query.filter_by(equipment_id=equipment_id).order_by(Service.service_date.desc()).all()

        return render_template('equipment_details.html', equipment=equipment, service_records=service_records)


    @app.route('/service_equipment/<int:equipment_id>', methods=['GET', 'POST'])
    @login_required
    def service_equipment(equipment_id):
        equipment = Equipment.query.get_or_404(equipment_id)

        if request.method == 'POST':
            service_date = request.form['service_date']
            service_description = request.form['service_description']
            service_hours = request.form['service_hours']
            service_cost = request.form['service_cost']
            service_next_date = request.form['service_next_date']
            
            # Convert dates from string to date objects
            service_date = datetime.strptime(service_date, '%Y-%m-%d').date()
            service_next_date = datetime.strptime(service_next_date, '%Y-%m-%d').date() if service_next_date else None

            new_service = Service(
                service_date=service_date,
                service_description=service_description,
                service_hours=service_hours,
                service_cost=service_cost,
                service_next_date=service_next_date,
                service_by=current_user,  # Logged-in user performing the service
                equipment=equipment
            )

            db.session.add(new_service)
            db.session.commit()
            flash('Service record added successfully!', 'success')
            return redirect(url_for('equipment_details', equipment_id=equipment_id))

        return render_template('service_equipment.html', equipment=equipment)

    @app.route('/update_equipment/<int:equipment_id>', methods=['GET', 'POST'])
    @login_required
    def update_equipment(equipment_id):
        equipment = Equipment.query.get_or_404(equipment_id)

        if request.method == 'POST':
            equipment.equipment_name = request.form['equipment_name']
            equipment.serial_number = request.form['serial_number']
            equipment.purchase_date = datetime.strptime(request.form['purchase_date'], '%Y-%m-%d').date() if request.form['purchase_date'] else None
            equipment.warranty_expiry = datetime.strptime(request.form['warranty_expiry'], '%Y-%m-%d').date() if request.form['warranty_expiry'] else None
            equipment.status = request.form['status']
            equipment.location_id = request.form['location_id']
            equipment.category_id = request.form['category_id']

            # Handle multiple image uploads
            images = request.files.getlist('equipment_pictures')
            for image in images:
                if image and '.' in image.filename and image.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    image.save(image_path)

                    # Save to database
                    new_image = EquipmentImage(filename=filename, equipment=equipment)
                    db.session.add(new_image)

            db.session.commit()
            flash('Equipment updated successfully!', 'success')
            return redirect(url_for('equipment_details', equipment_id=equipment_id))

        locations = Location.query.all()
        categories = Category.query.all()
        return render_template('update_equipment.html', equipment=equipment, locations=locations, categories=categories)

    @app.route('/add_location', methods=['GET', 'POST'])
    @login_required
    def add_location():
        if request.method == 'POST':
            location_name = request.form['location_name']
            location_description = request.form['location_description']

            new_location = Location(location_name=location_name, location_description=location_description)
            db.session.add(new_location)
            db.session.commit()

            flash('Location added successfully!', 'success')
            return redirect(url_for('locations'))

        return render_template('add_location.html')

    @app.route('/delete_location/<int:location_id>', methods=['POST'])
    @login_required
    def delete_location(location_id):
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))


        location = Location.query.get_or_404(location_id)

        try:
            db.session.delete(location)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            print("Error deleting location:", e)
            return jsonify({"success": False}), 500

    @app.route('/locations')
    @login_required
    def locations():
        locations = Location.query.all()
        locations_with_counts_and_machines = []

        for loc in locations:
            machines = Equipment.query.filter_by(location_id=loc.location_id).all()
            count = len(machines)
            locations_with_counts_and_machines.append((loc, count, machines))

        return render_template("locations.html", locations_with_counts_and_machines=locations_with_counts_and_machines)

    
    @app.route('/edit_location/<int:location_id>', methods=['GET', 'POST'])
    @login_required
    def edit_location(location_id):
        location = Location.query.get_or_404(location_id)

        if request.method == 'POST':
            location.location_name = request.form['location_name']
            location.location_description = request.form['location_description']
            db.session.commit()
            flash("Location updated successfully!", "success")
            return redirect(url_for('locations'))

        return render_template('edit_location.html', location=location)
   
    @app.route('/locations/<int:location_id>/machines')
    @login_required
    def view_location_machines(location_id):
        category = Location.query.get_or_404(location_id)
        equipments = Equipment.query.filter_by(location_id=location_id).all()
        return render_template('location_machines.html', location=category, equipments=equipments)
    

    
    
    @app.route('/components')
    @login_required
    def components():
        components = Component.query.all()
        return render_template('components.html', components=components)

    @app.route('/add_component', methods=['GET', 'POST'])
    @login_required
    def add_component():
        if request.method == 'POST':
            component_name = request.form['component_name']
            serial_number = request.form['serial_number']
            install_date = request.form['install_date']
            service_id = request.form['service_id']

            new_component = Component(
                component_name=component_name,
                component_serial_number=serial_number,
                component_install_date=install_date,
                service_id=service_id
            )

            db.session.add(new_component)
            db.session.commit()
            flash('Component added successfully!', 'success')
            return redirect(url_for('components'))
        
        return render_template('add_component.html')

    @app.route('/delete_component/<int:component_id>')
    @login_required
    def delete_component(component_id):
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))
        component = Component.query.get_or_404(component_id)
        db.session.delete(component)
        db.session.commit()
        flash('Component deleted successfully!', 'success')
        return redirect(url_for('components'))


    @app.route('/admin/add_user', methods=['GET', 'POST'])
    @login_required
    def add_user():
        if current_user.role_id != 1:
            flash("Access denied: Admins only.")
            return redirect(url_for('equipments'))

        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            role_id = request.form['role_id']

            if User.query.filter_by(username=username).first():
                flash("Username already exists.")
                return redirect(url_for('add_user'))
            role = Role.query.get(role_id)
            if not role:
                flash('Invalid role selected!', 'error')
                return redirect(url_for('register'))

            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            try:
                db.session.commit()
                flash('User added successfully.')
            except IntegrityError:
                db.session.rollback()
                flash('Failed to add user due to DB error.')

            return redirect(url_for('admin_dashboard'))
        roles = Role.query.all()
        return render_template('add_user.html',roles=roles)

    @app.route('/update_status/<int:equipment_id>', methods=['POST'])
    @login_required
    def update_status(equipment_id):
        equipment = Equipment.query.get_or_404(equipment_id)
        data = request.get_json()
        
        if 'status' in data:
            equipment.status = data['status']
            db.session.commit()
            return jsonify({"success": True, "new_status": equipment.status})
        
        return jsonify({"success": False}), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404

    @login_manager.unauthorized_handler
    def unauthorized():
        # Store the original request URL in the session
        session['next_url'] = request.url
        return redirect(url_for('login'))