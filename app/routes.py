from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import User, Machine
from app import create_app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    machines = Machine.query.all()
    return render_template('index.html', machines=machines)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == password:  # In real apps, use password hashing
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('machines'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/machines')
@login_required
def machines():
    machines = Machine.query.all()
    return render_template('machines.html', machines=machines)

@app.route('/update_machine/<int:machine_id>', methods=['GET', 'POST'])
@login_required
def update_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if request.method == 'POST':
        machine.last_service_date = request.form['last_service_date']
        db.session.commit()
        flash('Machine updated successfully!', 'success')
        return redirect(url_for('machines'))
    return render_template('update_machine.html', machine=machine)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        
        # Create a new user
        new_user = User(username=username, password_hash=password, role=role)  # In real apps, hash the password
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')



@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
