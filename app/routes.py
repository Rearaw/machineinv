from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User, Role, Equipment, Service

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
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):  # 🔹 Verify password
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('equipments'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out successfully!', 'success')
        return redirect(url_for('index'))

    @app.route('/equipments')
    @login_required
    def equipments():
        equipments = Equipment.query.all()
        return render_template('equipments.html', equipments=equipments)

    @app.route('/update_equipment/<int:equipment_id>', methods=['GET', 'POST'])
    @login_required
    def update_equipment(equipment_id):
        equipment = Equipment.query.get_or_404(equipment_id)
        if request.method == 'POST':
            equipment.status = request.form['status']
            db.session.commit()
            flash('Equipment updated successfully!', 'success')
            return redirect(url_for('equipments'))
        return render_template('update_equipment.html', equipment=equipment)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
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

    @app.route('/categories')
    @login_required
    def categories():
        categories = Category.query.all()
        return render_template('categories.html', categories=categories)

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
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
        return redirect(url_for('categories'))


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
        component = Component.query.get_or_404(component_id)
        db.session.delete(component)
        db.session.commit()
        flash('Component deleted successfully!', 'success')
        return redirect(url_for('components'))


    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html'), 404
