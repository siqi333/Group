import datetime
from app import app
import os, json, time

from flask import session, make_response, flash
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
import mysql.connector
import connect
from flask_hashing import Hashing
from datetime import date, timedelta, datetime
from flask import flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import json

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


@app.route('/local_dashboard')
def local_dashboard():

    # Check if the user is logged in and has the role of local manager
    if not session.get('loggedin') or session.get('role') != 'local_manager':
        return redirect(url_for('login'))

    username = session.get('username')

    # Fetch the name and position of the staff member from the database
    connection = getCursor()
    connection.execute(
        "select first_name,last_name,position,t.city,image from staff as s join store as t on s.store_id=t.store_id where username=%s;",
        (username,))
    name = connection.fetchone()

    # Fetch the latest news item without a specific store_id (global news)
    connection.execute("""select n.title,n.content,n.create_time
            from news as n where store_id is null
            order by n.news_id desc""")
    news = connection.fetchone()

    return render_template('./local/local_dashboard.html', name=name,news=news)


@app.route('/local/personal', methods=['GET', 'POST'])
def local_personal():
    # After replacing it with session login ok
    username = session.get('username')

    if request.method == "GET":
        # Initialize a record dictionary to store user data
        record = {
            "last_name": "",
            "first_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "Image": "",
        }

        # Fetch user data from the database based on the username
        connection = getCursor()
        connection.execute(
            "select * from staff where username=%s;", (username,))
        result = connection.fetchone()
        print(result)

        if result:
            # If user data exists, populate the record dictionary
            record['last_name'] = result[1]
            record['first_name'] = result[2]
            record['email'] = result[3]
            record['phone'] = result[4]
            record['address'] = result[5]
            record['Image'] = result[7]
        return render_template("./local/profile.html", record=record, username=username)

    else:
        # Handle POST request to update user data
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        Image = request.form.get('Image')

        connection = getCursor()
        connection.execute(
            "select * from staff where username=%s;", (username,))
        result = connection.fetchone()
        if result:
            # If user data exists, update it in the database
            sql = "update  staff set last_name=%s,first_name=%s,email=%s,phone=%s,address=%s,image=%s where username=%s"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image, username,))
        else:
            # If user data doesn't exist, insert a new record into the database
            sql = "insert into staff (last_name,first_name,email,phone,address,image,username) values(%s,%s,%s,%s,%s,%s,%s,%s)"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image, username,))
        flash("Update successful")
        return redirect("/local/personal")


@app.route('/local/password', methods=['GET', 'POST'])
def local__password():
    username = session.get('username')

    if request.method == 'POST':

        # Get the form data for old password, new password, and confirm password
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if all fields are filled
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template("./local/password.html")

        # Check if the new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template("./local/password.html")

        # Check if the new password meets the requirements
        if len(new_password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            return render_template("./local/password.html")

        # Get the database cursor
        cursor = getCursor()
        cursor.execute('SELECT password FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            # Check if the old password matches the password in the database
            if check_password_hash(account[0], old_password):
                # Hash the new password and update it in the database
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE account SET password = %s WHERE username = %s', (hashed_password, username))
                flash('Password is changed successfully.', 'success')
            else:
                flash('Old password is incorrect.', 'error')
        else:
            flash('Account not found.', 'error')

    return render_template("./local/password.html")


@app.route("/local/promotion", methods=['GET', 'POST'])
def local_promotion():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    username = session.get('username')

    # Get the store ID for the logged-in user
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    # Query the database for promotions associated with the store
    connection = getCursor()
    connection.execute(
        """select p.promotion_name,p.description,p.start_day,p.end_day,p.discount_rate,p.promotion_id
        from promotion as p where p.store_id = %s;""", (store_id,))
    promotions = connection.fetchall()

    return render_template('/local/promotion.html', promotions=promotions)


@app.route("/local/promotion_cancel", methods=['GET', 'POST'])
def local_promotion_cancel():

    promotion_id = request.args.get('promotion_id')

    # Execute a SQL DELETE query to remove the promotion with the specified promotion_id
    connection = getCursor()
    connection.execute('Delete from promotion where promotion_id = %s', (promotion_id,))
    flash('Promotion deleted successfully!', 'success')
    
    return redirect('/local/promotion')


@app.route("/local/promotion_edit", methods=['GET', 'POST'])
def local_promotion_edit():
    promotion_id = request.args.get('promotion_id')

    # Fetch the promotion details from the database based on the promotion_id
    connection = getCursor()
    connection.execute('select * from promotion where promotion_id = %s', (promotion_id,))
    promotion = connection.fetchone()

    if request.method =='POST':
    
        # Get the updated promotion details from the form
        promotion_id = request.form.get('promotion_id')
        code = request.form.get('code')
        info = request.form.get('info')
        start = request.form.get('start')
        end = request.form.get('end')
        discount = request.form.get('discount')
        store_id = request.form.get('store_id')

        # Update the promotion in the database
        connection.execute("""Update promotion set promotion_name =%s,description=%s,start_day=%s,
                           end_day = %s, discount_rate=%s,store_id=%s
                            where promotion_id = %s""", (code, info, start, end, discount, store_id, promotion_id))
        flash('Promition updated successfully!', 'success')

        return redirect('/local/promotion')

    return render_template('/local/promotion_edit.html', promotion=promotion)


@app.route("/local/promotion_new", methods=['GET', 'POST'])
def local_promotion_new():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    username = session.get('username')

    # Fetch the store_id associated with the username
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    if request.method == 'POST':
        # Get the new promotion details from the form
        code = request.form.get('code')
        info = request.form.get('info')
        start = request.form.get('start')
        end = request.form.get('end')
        discount = request.form.get('discount')

        # Insert the new promotion into the database
        connection.execute("""Insert into promotion (promotion_name,description,start_day,end_day,discount_rate,store_id) 
                          values(%s,%s,%s,%s,%s,%s)""", (code, info, start, end, discount, store_id))
        flash('Promition added successfully!', 'success')
        return redirect('/local/promotion')

    return render_template('/local/promotion_new.html')


@app.route("/local/news", methods=['GET', 'POST'])
def local_news():

    # Execute a SQL query to fetch news entries that are not associated with any specific store
    connection = getCursor()
    connection.execute(
        """select n.title,n.content,n.create_time
        from news as n where store_id is null
        order by n.news_id desc;""")
    news = connection.fetchall()

    return render_template('/local/news.html', news=news)

@app.route("/local/add_news", methods=['GET', 'POST'])
def local_add_news():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    # Execute a SQL query to fetch the store ID associated with the current staff member
    username = session.get('username')
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    if request.method == 'POST':

        title = request.form.get('title')
        content = request.form.get('content')

        # Insert the news entry into the database
        connection.execute("""Insert into news (title,content,store_id) 
                          values(%s,%s,%s)""", (title, content, store_id))

        flash('News published successfully', 'success')

        return redirect('/local/add_news')

    return render_template('/local/add_news.html')


@app.route('/local/store_staff_profile', methods=['GET', 'POST'])
def store_staff_profile():
    username = session.get('username')

    try:
        # Retrieve the store_id associated with the current staff member
        connection = getCursor()
        connection.execute("SELECT store_id FROM staff WHERE username=%s;", (username,))
        store_id_result = connection.fetchone()

        store_id = store_id_result[0]
        # Fetch the list of staff members (excluding Local Managers) for the current store
        connection.execute(
            "SELECT staff_id, image, CONCAT(first_name, ' ', last_name) AS name FROM staff WHERE store_id=%s AND position != 'Local Manager';",
            (store_id,))
        staff_list = connection.fetchall()

    except Exception as e:
        return str(e), 500

    return render_template("./local/store_staff_profile.html", staff_list=staff_list)


@app.route('/local/manage_staff_profile', methods=['GET', 'POST'])
def manage_staff_profile():
    staff_id = request.args.get('staff_id')
    cursor = getCursor()

    if request.method == 'POST':

        # Retrieve form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        # Handle image upload
        image = request.files.get('UploadImage')

        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('static/images/profile', image_filename)
            image.save(image_path)
        else:
            image_filename = request.form['Image']

        # Update the staff profile in the database
        cursor.execute("""
            UPDATE staff 
            SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s, image=%s 
            WHERE staff_id=%s
        """, (first_name, last_name, email, phone, address, image_filename, staff_id))

        connection.commit()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('manage_staff_profile', staff_id=staff_id))
    
    # Fetch the staff profile details from the database
    cursor.execute("SELECT first_name, last_name, email, phone, address, position, image FROM staff WHERE staff_id=%s;",
                   (staff_id,))
    staff_profile = cursor.fetchone()

    if not staff_profile:
        flash('Staff profile not found', 'danger')
        return redirect(url_for('staff_dashboard'))
    
    # Construct the staff profile dictionary
    staff_profile = {
        'first_name': staff_profile[0],
        'last_name': staff_profile[1],
        'email': staff_profile[2],
        'phone': staff_profile[3],
        'address': staff_profile[4],
        'position': staff_profile[5],
        'image': staff_profile[6]
    }

    return render_template("./local/manage_staff_profile.html", staff_profile=staff_profile)


@app.route('/local/create_staff_profile', methods=['GET', 'POST'])
def create_staff_profile():
    if not session.get('loggedin') or session.get('role') != 'local_manager':
        return redirect(url_for('login'))

    if request.method == 'POST':

        # Extract form data
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        position = 'Staff'
        role = 'staff'
        image = request.files.get('UploadImage')

        # Check if username or email already exists
        cursor = getCursor()
        cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
        username_exists = cursor.fetchone()
        cursor.execute('SELECT * FROM staff WHERE email = %s', (email,))
        email_exists = cursor.fetchone()

        # Check if all required fields are filled
        if not all([username, password, confirm_password, first_name]):
            flash('Username, password, confirmed password, first name are required.', 'danger')
            return render_template("./local/create_staff_profile.html")
        
        # Validate email format
        if '@' not in email:
            flash('Please provide a valid email.', 'danger')
            return render_template("./local/create_staff_profile.html")
        if username_exists:
            flash('Username already exists!', 'danger')
            return render_template("./local/create_staff_profile.html")
        if email_exists:
            flash('Email already exists!', 'danger')
            return render_template("./local/create_staff_profile.html")

        # Check password complexity and matching confirmation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template("./local/create_staff_profile.html")
        if len(password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'danger')
            return render_template("./local/create_staff_profile.html")

        # Save the uploaded image or use default
        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('static/images/profile', image_filename)
            image.save(image_path)
        else:
            image_filename = 'default.png'

        hashed_password = generate_password_hash(password)

        cursor = getCursor()
        try:

            # Get the store_id of the logged-in local manager
            cursor.execute("SELECT store_id FROM staff WHERE username=%s;", (session.get('username'),))
            store_id_result = cursor.fetchone()
            store_id = store_id_result[0]

            # Insert data into account and staff tables
            cursor.execute("""
                INSERT INTO account (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, hashed_password, role))

            cursor.execute("""
                INSERT INTO staff (last_name, first_name, email, phone, address, position, image, username, store_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (last_name, first_name, email, phone, address, position, image_filename, username, store_id))

            connection.commit()

            flash('Staff profile created successfully', 'success')

        except mysql.connector.Error as err:
            connection.rollback()
            flash(f'Error: {err}', 'error')
        finally:
            cursor.close()
            connection.close()

    return render_template("./local/create_staff_profile.html")

    
@app.route('/local/add_equipment', methods=['GET', 'POST'])
def local_add_equipment():
    if request.method == "GET":

        # Retrieve categories from the database
        connection = getCursor()
        connection.execute(
            "select category_id,category_name from category")
        records = connection.fetchall()
        category_list = []
        for record in records:
            category_list.append({
                "category_id": record[0],
                "category_name": record[1],
            })
        return render_template("./local/add_equipment.html", category_list=category_list)

    else:

        # Handle POST request to add new equipment
        username = session.get('username')
        connection = getCursor()
        connection.execute("select store_id from staff where username =%s", (username,))
        store_id = connection.fetchone()[0]

        # Extract equipment details from the form
        name = request.form.get('name')
        specifications = request.form.get('specifications')
        cost = request.form.get('cost')
        image = request.form.get('Image')
        hire_cost = request.form.get('hire_cost')
        category_id = request.form.get('category_id')
        min_hire_period = request.form.get('min_hire_period')
        max_hire_period = request.form.get('max_hire_period')
        inventory = request.form.get('inventory')
        purchase_date = request.form.get('purchase_date')

        # Insert the equipment details into the database
        conn = getCursor()
        conn.execute(
            "insert into store_equipment (name,specifications,cost,image,hire_cost,category_id,store_id,min_hire_period,max_hire_period) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                name, specifications, cost, image, hire_cost, category_id, store_id, min_hire_period, max_hire_period
            ))
        new_id = conn.lastrowid

        # Insert inventory records for the new equipment
        for i in range(int(inventory)):
            conn.execute("insert into inventory (store_id,equipment_id,purchase_date,status) values(%s,%s,%s,%s)",
                         (store_id, new_id, purchase_date, 'available'))
        flash('New Equipment added successfully.','success')

        return redirect("/local/add_equipment")


def get_staff_details(username):
    cursor = getCursor()
    cursor.execute("""
        SELECT s.store_id, a.role
        FROM staff s
        JOIN account a ON s.username = a.username
        WHERE a.username = %s
    """, (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0], result[1]
    return None, None


def category():
    connection = getCursor()
    connection.execute(
        "select * from category;")
    categorys = connection.fetchall()
    return categorys


@app.route('/local/product', methods=['GET', 'POST'])
def local_product():
    username = session.get('username')
    store_id, role = get_staff_details(username)

    # If store_id is not found or if the role is not valid, redirect to the local_dashboard
    if not store_id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('local_dashboard'))

    categorys = category()
    category_id = request.args.get('category')

    # Fetch products based on the category_id and store_id from the database
    connection = getCursor()
    connection.execute("""
        SELECT equipment_id, name, image, store_id, hire_cost 
        FROM store_equipment 
        WHERE category_id = %s AND store_id = %s;
    """, (category_id, store_id))
    products = connection.fetchall()

    # Fetch the category name for the given category_id
    connection.execute("""
        SELECT category_name 
        FROM category 
        WHERE category_id = %s;
    """, (category_id,))
    category_result = connection.fetchone()

    # Set category_name to the fetched category_name or an empty string if not found
    if category_result:
        category_name = category_result[0]
    else:
        category_name = ""

    return render_template('/local/product.html', products=products, category_name=category_name, categorys=categorys)

@app.route('/local/product_details', methods=['GET', 'POST'])
def local_product_details():
    username = session.get('username')
    store_id, role = get_staff_details(username)

    # If store_id is not found or if the role is not valid, redirect to the local_dashboard
    if not store_id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('local_dashboard'))

    categorys = category()

    equipment_id = request.args.get('equipment_id')

    # SQL query to fetch detailed information about the product based on equipment_id and store_id
    sql = """
        SELECT name, specifications, e.image, hire_cost, min_hire_period, max_hire_period, s.stock, c.category_id, c.category_name, cost
        FROM store_equipment AS e 
        LEFT JOIN (SELECT store_id, equipment_id, IFNULL(COUNT(serial_number), 0) AS stock 
                   FROM inventory WHERE status = 'available' 
                   GROUP BY store_id, equipment_id) AS s 
        ON e.store_id = s.store_id AND e.equipment_id = s.equipment_id 
        INNER JOIN category AS c ON e.category_id = c.category_id 
        WHERE e.store_id = %s AND e.equipment_id = %s;
    """

    # Execute the SQL query with store_id and equipment_id parameters
    connection = getCursor()
    connection.execute(sql, (store_id, equipment_id))
    details = connection.fetchone()

    return render_template('/local/product_details.html', details=details, equipment_id=equipment_id, store_id=store_id, categorys=categorys)


@app.route('/local/update_equipment', methods=['POST'])
def local_update_equipment():

    # Get data from the form
    store_id = request.form['store_id']
    equipment_id = request.form['equipment_id']
    name = request.form['name']
    specifications = request.form['specifications']

    # Remove formatting characters from hire_cost and cost fields, convert to float
    hire_cost = request.form['hire_cost'].replace(',', '').replace('$', '')

    # Convert min_hire_period and max_hire_period to integers
    min_hire_period = int(request.form['min_hire_period'])
    max_hire_period = int(request.form['max_hire_period'])
    cost = request.form['cost'].replace(',', '').replace('$', '')

    hire_cost = float(hire_cost)
    cost = float(cost)

    # Handle image upload
    image = request.files.get('image')
    upload_folder = os.path.join('static', 'images', 'products')
    if image and image.filename != '':
        image_filename = secure_filename(image.filename)
        # Ensure the directory exists
        os.makedirs(upload_folder, exist_ok=True)
        # Save the image to the products directory
        image.save(os.path.join(upload_folder, image_filename))
    else:
        image_filename = request.form.get('current_image', '')

    # SQL query to update equipment details in the database
    sql = """UPDATE store_equipment 
             SET name = %s, specifications = %s, hire_cost = %s, cost = %s, min_hire_period = %s, max_hire_period = %s, image = %s
             WHERE store_id = %s AND equipment_id = %s;"""

    # Execute the SQL query with the provided parameters
    cursor = getCursor()
    cursor.execute(sql, (
    name, specifications, hire_cost, cost, min_hire_period, max_hire_period, image_filename, store_id, equipment_id))
    cursor.close()

    flash('Equipment updated successfully!', 'success')
    return redirect(url_for('local_product_details', store_id=store_id, equipment_id=equipment_id))


def get_store_id(username):
    cursor = getCursor()
    cursor.execute("""
        SELECT s.store_id 
        FROM staff s
        JOIN account a ON s.username = a.username
        WHERE a.username = %s
    """, (username,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Access the store_id by index
    return None


@app.route('/local/inventory_list', methods=['GET', 'POST'])
def local_inventory_list():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session['username']
    store_id = get_store_id(username)

    if store_id is None:
        flash('No store found for the logged-in user', 'danger')
        return redirect(url_for('home'))  # Redirect to an appropriate page

    # Get filter values from the form, default to empty strings
    equipment_name = request.form.get('equipment_name', '')
    category_id = request.form.get('category_id', '')
    status = request.form.get('status', '')
    cursor = getCursor()
    cursor.execute("SELECT * FROM category;")
    categories = cursor.fetchall()

    # Initialize a list for WHERE clauses and args list for SQL query parameters
    where_clauses = ["se.store_id = %s"]
    args = [store_id]

    # Add conditions to WHERE clauses and append corresponding args
    if equipment_name:
        where_clauses.append("se.name LIKE %s")
        args.append(f"%{equipment_name}%")
    if category_id:
        where_clauses.append("se.category_id = %s")
        args.append(category_id)
    if status:
        where_clauses.append("i.status = %s")
        args.append(status)

    # Join WHERE clauses with 'AND' and create the WHERE statement
    where = " AND ".join(where_clauses)

    # Execute the SQL query with dynamic WHERE conditions based on filters
    cursor.execute(f"""
        SELECT se.equipment_id, se.name, se.specifications, se.cost, se.image, se.hire_cost,
               se.min_hire_period, se.max_hire_period, i.serial_number, i.status
        FROM store_equipment se
        JOIN inventory i ON se.equipment_id = i.equipment_id
        WHERE {where}
    """, args)

    equipment = cursor.fetchall()
    cursor.close()

    return render_template('local/inventory_list.html', equipment=equipment,
                           status=status, category_id=category_id, equipment_name=equipment_name,
                           categories=categories, store_id=store_id)


@app.route('/local/edit_inventory/<int:store_id>/<int:equipment_id>', methods=['GET', 'POST'])
def local_edit_inventory(store_id, equipment_id):
    cursor = getCursor()

    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        serial_number = request.form.get('serial_number')
        purchase_date = request.form.get('purchase_date')
        status = request.form.get('status')

        # Update the inventory and store_equipment tables
        cursor.execute("""
            UPDATE store_equipment se
            JOIN inventory i ON se.equipment_id = i.equipment_id
            SET se.name = %s, i.serial_number = %s, i.purchase_date = %s, i.status = %s
            WHERE se.equipment_id = %s AND i.serial_number = %s AND se.store_id = %s
        """, (name, serial_number, purchase_date, status, equipment_id, serial_number, store_id))

        cursor.close()
        flash('Inventory updated successfully!', 'success')
        return redirect(url_for('local_edit_inventory', store_id=store_id, equipment_id=equipment_id))
    else:

        # Fetch existing inventory items and equipment details for display
        cursor.execute("""
            SELECT se.name, i.serial_number, i.purchase_date, i.status
            FROM store_equipment se
            JOIN inventory i ON se.equipment_id = i.equipment_id
            WHERE se.store_id = %s AND se.equipment_id = %s
        """, (store_id, equipment_id))

        inventory_items = cursor.fetchall()

        cursor.execute("""
            SELECT name
            FROM store_equipment
            WHERE store_id = %s AND equipment_id = %s
        """, (store_id, equipment_id))

        equipment = cursor.fetchone()
        cursor.close()

        return render_template('local/edit_inventory.html', inventory_items=inventory_items, equipment=equipment,
                               store_id=store_id, equipment_id=equipment_id)


@app.route('/local/report_analysis', methods=['GET', 'POST'])
def local_report_analysis():
    if not session.get('loggedin') or session.get('role') != 'local_manager':
        return redirect(url_for('login'))
    
    username = session.get('username')
    connection = getCursor()
    try:

        # Fetch the store ID associated with the current user
        connection.execute("SELECT store_id FROM staff WHERE username=%s;", (username,))
        store_id_result = connection.fetchone()
        if store_id_result is None:
            flash('Store ID not found for the current user.', 'error')
            return redirect(url_for('local_dashboard'))

        # Fetch the store name using the store ID
        store_id = store_id_result[0]
        connection.execute("SELECT store_name FROM store WHERE store_id=%s;", (store_id,))
        store_name_result = connection.fetchone()
        store_name = store_name_result[0]  

        # Fetch monthly revenue data for the current store
        connection.execute("""
            SELECT DATE_FORMAT(p.payment_date, '%Y-%m') AS Month, SUM(p.amount) AS Revenue
            FROM payment p
            JOIN booking b ON p.booking_id = b.booking_id
            WHERE p.status = 'successful' AND b.store_id = %s
            GROUP BY DATE_FORMAT(p.payment_date, '%Y-%m')
            ORDER BY DATE_FORMAT(p.payment_date, '%Y-%m');
        """, (store_id,))
        monthly_revenue = connection.fetchall()

        # Initialize a dictionary to store monthly revenue data for all months   
        all_months = ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12']
        monthly_revenue_dict = {month: 0 for month in all_months}

        # Populate the monthly revenue dictionary with fetched data
        for row in monthly_revenue:
            monthly_revenue_dict[row[0]] = row[1]

        # Separate the labels and values for monthly revenue for rendering
        monthly_revenue_labels = list(monthly_revenue_dict.keys())
        monthly_revenue_values = list(monthly_revenue_dict.values())

        # Fetching the data for top 5 most booked equipment
        connection.execute("""
            SELECT e.name, COUNT(bd.equipment_id) as bookings
            FROM booking_detail bd
            JOIN store_equipment e ON bd.equipment_id = e.equipment_id
            JOIN booking b ON bd.booking_id = b.booking_id
            JOIN payment p ON p.booking_id=b.booking_id
            WHERE b.store_id = %s AND YEAR(b.booking_date) = 2024 AND p.status = 'successful'
            GROUP BY bd.equipment_id
            ORDER BY bookings DESC
            LIMIT 5;
        """, (store_id,))
        top_5_booked = connection.fetchall()

        # Fetching the data for top 5 longest booking period by equipment
        connection.execute("""
            SELECT e.name, AVG(DATEDIFF(bd.end_date, bd.start_date)) as avg_days
            FROM booking_detail bd
            JOIN store_equipment e ON bd.equipment_id = e.equipment_id
            JOIN booking b ON bd.booking_id = b.booking_id
            JOIN payment p ON p.booking_id=b.booking_id
            WHERE b.store_id = %s AND YEAR(b.booking_date) = 2024 AND p.status='successful'
            GROUP BY bd.equipment_id
            ORDER BY avg_days DESC
            LIMIT 5;
        """, (store_id,))
        top_5_longest_booking = connection.fetchall()

        # Fetching the data for the percentage of the status by equipment
        connection.execute("""
            SELECT status, COUNT(status) as count_status
            FROM inventory i
            WHERE store_id = %s
            GROUP BY status;
        """, (store_id,))
        equipment_status = connection.fetchall()

        # Calculate total equipment status counts
        total_status_counts = sum(row[1] for row in equipment_status)
        equipment_status_labels = [row[0] for row in equipment_status]
        equipment_status_counts = [row[1] for row in equipment_status]
        equipment_status_percentages = [(count / total_status_counts) * 100 for count in equipment_status_counts]

    finally:
        connection.close()

    # Render the template with the fetched data
    return render_template(
        "local/report_analysis.html",
        store_name=store_name,
        monthly_revenue_labels=monthly_revenue_labels,
        monthly_revenue_values=monthly_revenue_values,
        top_5_booked=top_5_booked,
        top_5_longest_booking=top_5_longest_booking,
        equipment_status_labels=equipment_status_labels,
        equipment_status_percentages=equipment_status_percentages,
        total_status_counts=total_status_counts
    )



@app.route('/local/check_equipment', methods=['GET', 'POST'])
def local_check_equipment():

    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    connection = getCursor()

    # Fetch categories from the database
    connection.execute('select category_id, category_name from category')
    cateogrys = connection.fetchall()

    # Fetch the store ID associated with the logged-in user
    connection.execute('select store_id from staff where username = %s',(username,))
    store_id = connection.fetchone()[0]

    # Fetch equipment details for the store along with the total available
    connection.execute("""select s.name,s.image,s.category_id,a.total from store_equipment as s 
                       join (select equipment_id, count(serial_number) as total from inventory group by equipment_id) as a 
                       on s.equipment_id = a.equipment_id where s.store_id = %s""",(store_id,))
    category_list=connection.fetchall()

    return render_template("./local/staff_check_equipment.html", records=category_list,cateogrys=cateogrys)



@app.route('/local/feedback', methods=['GET', 'POST'])
def local_feedback():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route


    # Fetch the store ID associated with the logged-in user
    username = session.get('username')
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    # Fetch feedbacks for the store along with related details
    connection.execute(
        "select feedback_id,name,email,feedback.phone,subject,create_time,store_name from feedback left join store on store.store_id=feedback.store_id where feedback.store_id =%s order by create_time desc",
        (store_id,))
    feedbacks = connection.fetchall()

    # Format the feedback creation time and append to the result list
    feedbacks_result = []
    for feedback in feedbacks:
        feedback = list(feedback)
        feedback[5] = feedback[5].strftime('%d-%m-%Y %H:%M:%S')
        feedbacks_result.append(feedback)
    return render_template('/local/feedback.html', feedbacks=feedbacks_result)


@app.route('/local/feedback_detail', methods=['GET', 'POST'])
def local_feedback_detail():
    username = session.get('username')

    if not username:
        return redirect('/login/')

    # Fetch the user ID associated with the username
    connection = getCursor()
    connection.execute('select account_id from account where username=%s', (username,))
    user_id = connection.fetchone()[0]

    if request.method == "GET":
        feedback_id = request.args.get('id')

        # Fetch details of the feedback and related chat records
        connection.execute(
            "select name,email,feedback.phone,subject,create_time,store_name,customer_id from feedback left join store on store.store_id=feedback.store_id   where feedback_id=%s order by create_time desc",
            (feedback_id,))
        feedback = connection.fetchone()
        customer_id = feedback[-1]

        # Fetch chat records related to the feedback
        connection.execute("select * from feedback_exchange where feedback_id=%s order by create_time asc",
                           (feedback_id,))
        chat_records = connection.fetchall()
        chat_result = []
        connection.execute('select last_name,first_name from customer where customer_id=%s', (customer_id,))
        customer_name = " ".join(connection.fetchone())

        # Process chat records
        for chat_record in chat_records:
            if chat_record[1] == customer_id:
                chat_type = "customer"
                usertype = "Customer"
                username = customer_name
            else:
                connection.execute(
                    "select last_name,first_name from staff where username=(select username from account where account_id=%s)",
                    (chat_record[1],))
                username = " ".join(connection.fetchone())
                usertype = "Staff"
                chat_type = "staff"
            create_time = chat_record[2]
            content = chat_record[3]

            chat_result.append({
                "chat_type": chat_type,
                "username": username,
                "usertype": usertype,
                "create_time": create_time,
                "content": content
            })

        # Format feedback creation time
        feedback = list(feedback)
        feedback[4] = feedback[4].strftime('%d-%m-%Y %H:%M:%S')
        return render_template('/local/feedback_detail.html', feedback=feedback, chat_result=chat_result,
                               feedback_id=feedback_id)
    else:

        # Process the POST request to add a new chat message
        feedback_id = request.form.get('feedback_id')
        content = request.form.get('content', '')

        # Insert the new chat message into the database
        connection.execute(
            "insert into feedback_exchange (sender_id,create_time,feedback_id,content) values (%s,%s,%s,%s)",
            (user_id, datetime.now(), feedback_id, content)
        )
        return redirect(url_for('local_feedback_detail', id=feedback_id))


@app.route('/local/check_report', methods=['GET'])
def local_check_report():

    # Fetch all records from the customer_report table
    connection = getCursor()
    connection.execute("select * from customer_report;")
    records = connection.fetchall()

    return render_template("/local/check_report.html", records=records)


@app.route('/local/check_request', methods=['GET'])
def local_check_request():

    # Fetch all records from the customer_request table
    connection = getCursor()
    connection.execute("select * from customer_request;")
    records = connection.fetchall()

    return render_template("/local/check_request.html", records=records)


@app.route('/local/check_customer', methods=['GET', 'POST'])
def local_check_customer():

    # Fetch specific columns (first_name, last_name, email, phone, address) from the customer table
    connection = getCursor()
    connection.execute("select first_name,last_name,email,phone,address from customer ;")
    records = connection.fetchall()

    return render_template("./local/check_customer.html", records=records)


@app.route('/local/search', methods=['GET', 'POST'])
def local_search():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    # Fetch the store_id associated with the logged-in user
    username = session.get('username')
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    if request.method == 'POST':

        # Get the search parameters from the form
        equipment_name = request.form.get('equipment_name')
        order_id = request.form.get('order_id')

        if equipment_name:

            # Prepare and execute a query to search for equipment by name
            query = "select * from store_equipment where name Like %s and store_id = %s"
            search_pattern = f"%{equipment_name}%"
            connection.execute(query, (search_pattern, store_id))
            equipment_details = connection.fetchall()

            return render_template('/local/search_equipment.html', equipment_details=equipment_details)

        elif order_id:

            # Fetch booking details based on the provided order_id and store_id
            connection.execute("""select b.booking_id,s.store_name,b.total_amount,
                               b.booking_date,b.status from booking as b join store as s 
                               on b.store_id = s.store_id where booking_id = %s and b.store_id =%s""",
                               (order_id, store_id))
            bookings = connection.fetchone()

            # Fetch booking details based on the provided order_id
            connection.execute("""select s.image, s.name,b.quantity,b.total,b.start_date,b.end_date
                               from booking_detail as b join store_equipment as s on b.equipment_id = s.equipment_id
                               where booking_id = %s""", (order_id,))
            booking_details = connection.fetchall()

            return render_template('/local/search_booking.html', bookings=bookings, booking_details=booking_details)

        else:
            flash('Please enter search info.')
            return redirect('/local/search')

    return render_template('/local/search.html')


@app.route('/local/verify', methods=['GET', 'POST'])
def local_verify():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    # Fetch the store_id associated with the logged-in user
    username = session.get('username')
    connection = getCursor()
    connection.execute('SELECT store_id FROM staff WHERE username = %s', (username,))
    store_id = connection.fetchone()[0]

    # Initialize variables for storing customer details, bookings, booking details, and error message
    customer_details = None
    bookings = None
    booking_details = None
    error_message = None

    if request.method == 'POST':
        booking_id = request.form.get('booking_id')

        if booking_id:
            try:

                # Fetch customer details based on the provided booking_id and store_id
                booking_id_int = int(booking_id)
                connection.execute("""
                    SELECT c.last_name, c.first_name, c.date_of_birth, b.booking_id, c.image
                    FROM booking AS b
                    JOIN customer AS c ON b.customer_id = c.customer_id
                    WHERE b.booking_id = %s AND b.store_id = %s
                """, (booking_id_int, store_id))
                customer_details = connection.fetchone()

                if customer_details:

                    # If customer details are found, fetch bookings and booking details
                    connection.execute("""
                        SELECT b.booking_id, s.store_name, b.total_amount, b.booking_date, b.status
                        FROM booking AS b
                        JOIN store AS s ON b.store_id = s.store_id
                        WHERE b.booking_id = %s AND b.store_id = %s
                    """, (booking_id_int, store_id))
                    bookings = connection.fetchone()

                    connection.execute("""
                        SELECT s.image, s.name, b.quantity
                        FROM booking_detail AS b
                        JOIN store_equipment AS s ON b.equipment_id = s.equipment_id
                        WHERE b.booking_id = %s
                    """, (booking_id_int,))
                    booking_details = connection.fetchall()

                    return render_template('local/verify_booking.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details)
                else:
                    # If no customer details are found, set an error message
                    error_message = 'No booking found with the provided booking number.'
            except ValueError:
                error_message = 'Invalid booking number. Please enter a valid number.'
        else:
            error_message = 'Please enter the booking number.'

    return render_template('local/verify.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details, error_message=error_message)
