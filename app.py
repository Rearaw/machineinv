from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.String(50), nullable=False)
    machine_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'online' or 'offline'
    time = db.Column(db.DateTime, default=datetime.now)
    updated_by = db.Column(db.String(100), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        machine_id = request.form['machine_id']
        machine_name = request.form['machine_name']
        status = request.form['status']
        updated_by = request.form['updated_by']

        new_machine = Machine(
            machine_id=machine_id,
            machine_name=machine_name,
            status=status,
            updated_by=updated_by
        )
        db.session.add(new_machine)
        db.session.commit()
        return redirect(url_for('index'))

    machines = Machine.query.order_by(Machine.time.desc()).all()
    return render_template('index.html', machines=machines)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)