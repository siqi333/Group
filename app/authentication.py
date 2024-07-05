
from app import app

from flask import session
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import Flask, flash
import mysql.connector
import connect
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_hashing import Hashing
import re
from datetime import date, timedelta,datetime
import os


hashing = Hashing(app)
app.config['SECRET_KEY'] = '5203'


dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

def category():
    connection = getCursor()
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()  
    return categorys



@app.route('/login/', methods=['POST', 'GET'])
def login():
    
    categorys = category()
    authen = request.args.get('authentication')

    if authen :
        flash('Please log in to hire.','danger')


    if request.method == 'POST':
        username = request.form.get('username')
        form_password = request.form.get('password')  # Use form_password for clarity

        if not username or not form_password:
            flash('Please enter both username and password.', 'danger')
            return redirect(url_for('login'))

        cursor = getCursor()
        cursor.execute('SELECT account_id, username, role, password FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()
  
        if account:
            account_id, account_username, account_role, stored_password = account

            if account_role.lower() in ['staff', 'local manager']:
                cursor.execute('select /*+parallel(16)*/ status from staff where username=%s;', (account_username,))
                staff_status = cursor.fetchone()[0]
				
                if str(staff_status) == 'deactive':
                    flash('Staff account is deactive.', 'danger')
                    return redirect(url_for('login'))

            if check_password_hash(stored_password, form_password):  # Assuming passwords are hashed
                
                session['loggedin'] = True
                session['id'] = account_id
                session['username'] = account_username
                session['role'] = account_role

                # Redirect to specific dashboards based on the user's role
                role_dashboard_map = {
                    'customer': 'customer_dashboard',
                    'staff': 'staff_dashboard',
                    'local_manager': 'local_dashboard',
                    'systems_admin': 'admin_dashboard',
                    'national_manager': 'national_dashboard'
                }

                return redirect(url_for(role_dashboard_map.get(account_role, 'login')))
            else:
                flash('Incorrect username or password.', 'danger')
        else:
            flash('Incorrect username or password.', 'danger')
    return render_template('./basic/login.html',categorys=categorys)

app.config['UPLOAD_FOLDER'] = 'static/identifications'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/register', methods=['GET', 'POST'])
def register():
    
    categorys = category()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        dateofbirth = request.form.get('dateofbirth')
        file = request.files.get('identification')

        validation_passed = True
        cursor = getCursor()

        cursor.execute("SELECT * FROM account WHERE username = %s", (username,))
        if cursor.fetchone():
            flash('Username already exists.', 'danger')
            validation_passed = False

        cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already exists.', 'danger')
            validation_passed = False

        if not password or not confirm_password:
            flash('Password and confirm password are required.', 'danger')
            validation_passed = False
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
            validation_passed = False
        elif len(password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            validation_passed = False

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
        else:
            flash('Invalid file type or no file uploaded.', 'danger')
            validation_passed = False

        try:
            user_dob = datetime.strptime(dateofbirth, "%Y-%m-%d").date()
            eighteen_years_ago = datetime.now().date() - timedelta(days=365.25 * 18)
            if user_dob >= eighteen_years_ago:
                flash('You must be at least 18 years old to register.', 'danger')
                validation_passed = False
        except ValueError:
            flash('Invalid date format.', 'danger')
            validation_passed = False

        if not all([username, firstname, lastname, address, phone_number, dateofbirth]):
            flash('All fields are required except optional.', 'danger')
            validation_passed = False

        if validation_passed:
            hashed_password = generate_password_hash(password)
            join_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("INSERT INTO account (username, password, role) VALUES (%s, %s, 'customer')", (username, hashed_password))
            cursor.execute("INSERT INTO customer (username, first_name, last_name, phone, email, address, date_of_birth, join_date, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (username, firstname, lastname, phone_number, email, address, dateofbirth, join_date, filename))
            cursor.close()
            flash('Registration successful! Welcome to the Agrihire Solution.', 'success')
            return redirect(url_for('login'))

    return render_template('./basic/register.html',categorys = categorys)
