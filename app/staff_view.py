import datetime
import os 

from app import app

from flask import config, flash, jsonify, session
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
import mysql.connector
import connect
from flask_hashing import Hashing
from werkzeug.utils import secure_filename
from datetime import date, timedelta,datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from datetime import datetime


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


@app.route('/staff_dashboard')
def staff_dashboard():
    username = session.get('username')

    # Fetch staff details
    connection = getCursor()
    connection.execute(
            "select first_name,last_name,position,t.city,image,s.store_id from staff as s join store as t on s.store_id=t.store_id where username=%s;", (username,))
    name = connection.fetchone()
    
    if not session.get('loggedin') or session.get('role') != 'staff':
        return redirect(url_for('login'))
    
    # Fetch pick-up data
    store_id = name[-1]
    connection.execute("""select start_date,count(detail_id) from booking_detail where booking_id in
                       (select booking_id from booking where store_id=%s) and start_date >= CURDATE()
                       group by start_date""",(store_id,))
    pickUps = connection.fetchall()
    pickUps = [(d.isoformat(), v) for d, v in pickUps]       # Format pick-up data for display

    # Fetch return data
    connection.execute("""select end_date,count(detail_id) from booking_detail where booking_id in
                       (select booking_id from booking where store_id=%s) and end_date >= CURDATE()
                       group by end_date""",(store_id,))
    returns = connection.fetchall()
    returns = [(d.isoformat(), v) for d, v in returns]         # Format return data for display
    
    today = date.today()

    # Fetch latest news
    connection.execute("""select n.title,n.content,n.create_time
            from news as n where store_id is null
            order by n.news_id desc """)
    news = connection.fetchone()

    return render_template('./staff/staff_dashboard.html',name=name,pickUps=pickUps,returns=returns,today=today,news=news)


@app.route('/staff/personal', methods=['GET', 'POST'])
def staff_personal():
    # After replacing it with session login ok
    username= session.get('username')
    store_id=1
    if request.method == "GET":
        # Initialize an empty record dictionary
        record = {
            "last_name": "",
            "first_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "position": "",
            "Image": "",
        }
        connection = getCursor()
        connection.execute(
            "select * from staff where username=%s;", (username,))
        result = connection.fetchone()
        
        if result:
            # Populate the record if staff data exists
            record['last_name'] = result[1]
            record['first_name'] = result[2]
            record['email'] = result[3]
            record['phone'] = result[4]
            record['address'] = result[5]
            record['Image'] = result[7]
        return render_template("./staff/profile.html", record=record, username=username)
    
    else:
        # Handle POST request for updating staff information
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
            # Update staff information if it exists
            sql = "update  staff set last_name=%s,first_name=%s,email=%s,phone=%s,address=%s,image=%s where username=%s"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image, username,))
        else:
            # Insert new staff information if it doesn't exist
            sql = "insert into staff (last_name,first_name,email,phone,address,image,store_id,username) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image,store_id, username,))
        flash("Update successful")

        return redirect("/staff/personal")


@app.route('/staff/password', methods=['GET', 'POST'])
def staff_password():
    username = session.get('username')
 
    if request.method == 'POST':
        # Get the old password, new password, and confirm password from the form
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if all fields are filled out
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template("./staff/password.html")

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template("./staff/password.html")

        # Check if the new password meets the required format
        if len(new_password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            return render_template("./staff/password.html")

        # Connect to the database and fetch the hashed password of the user
        cursor = getCursor()
        cursor.execute('SELECT password FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            # Check if the old password is correct
            if check_password_hash(account[0], old_password):
                # Generate the hash of the new password and update the password in the database
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE account SET password = %s WHERE username = %s', (hashed_password, username))
                flash('Password is changed successfully.', 'success')
            else:
                flash('Old password is incorrect.', 'error')
        else:
            flash('Account not found.', 'error')

    return render_template("./staff/password.html")



@app.route('/staff/add_equipment', methods=['GET', 'POST'])
def add_equipment():

    if request.method == "GET":
        # Fetch the category list from the database
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
        return render_template("./staff/add_equipment.html", category_list=category_list)
    
    else:
        # If the request method is POST, process the form data and add the equipment to the database
        username = session.get('username')
        connection = getCursor()
        connection.execute("select store_id from staff where username =%s",(username,))
        store_id = connection.fetchone()[0]

        # Get the form data
        name=request.form.get('name')
        specifications=request.form.get('specifications')
        cost=request.form.get('cost')
        image=request.form.get('Image')
        hire_cost=request.form.get('hire_cost')
        category_id=request.form.get('category_id')
        min_hire_period=request.form.get('min_hire_period')
        max_hire_period=request.form.get('max_hire_period')
        inventory=request.form.get('inventory')
        purchase_date=request.form.get('purchase_date')

        # Insert the new equipment into the store_equipment table
        conn = getCursor()
        conn.execute(
            "insert into store_equipment (name,specifications,cost,image,hire_cost,category_id,store_id,min_hire_period,max_hire_period) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(
                name,specifications,cost,image,hire_cost,category_id,store_id,min_hire_period,max_hire_period
            ))
        
        # Add inventory entries for the new equipment
        new_id = conn.lastrowid
        for i in range(int(inventory)):
            conn.execute("insert into inventory (store_id,equipment_id,purchase_date,status) values(%s,%s,%s,%s)",(store_id,new_id,purchase_date,'available'))
        flash('New Equipment added successfully.','success')
        
        return redirect("/staff/add_equipment")


@app.route('/staff/product', methods=['GET', 'POST'])
def staff_product():
    username = session.get('username')
    store_id, role = get_staff_details(username)

    # Check if the staff member has permission to view this page
    if not store_id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('staff_dashboard'))

    categorys = category()

    # Get the category ID from the request arguments
    category_id = request.args.get('category')

    # Fetch products based on the category and store ID
    connection = getCursor()
    connection.execute("""
        SELECT equipment_id, name, image, store_id, hire_cost 
        FROM store_equipment 
        WHERE category_id = %s AND store_id = %s;
    """, (category_id, store_id))
    products = connection.fetchall()

    # Fetch the category name for display purposes
    connection.execute("""
        SELECT category_name 
        FROM category 
        WHERE category_id = %s;
    """, (category_id,))
    category_result = connection.fetchone()

    if category_result:
        category_name = category_result[0]
    else:
        category_name = ""

    return render_template('/staff/product.html', products=products, category_name=category_name, categorys=categorys)


@app.template_filter('format_price')
def format_price(value):
    return "${:,.2f}".format(value)
app.jinja_env.filters['format_price'] = format_price

@app.route('/staff/product_details', methods=['GET', 'POST'])
def staff_product_details():
    username = session.get('username')
    store_id, role = get_staff_details(username)

    if not store_id:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('staff_dashboard'))

    categorys = category()

    equipment_id = request.args.get('equipment_id')

    # SQL query to fetch product details
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

    connection = getCursor()
    connection.execute(sql, (store_id, equipment_id))
    details = connection.fetchone()

    return render_template('/staff/product_details.html', details=details, equipment_id=equipment_id, store_id=store_id, categorys=categorys)


@app.route('/staff/update_equipment', methods=['POST'])
def update_equipment():

    # Get data from the form
    store_id = request.form['store_id']
    equipment_id = request.form['equipment_id']
    name = request.form['name']
    specifications = request.form['specifications']
    hire_cost = request.form['hire_cost'].replace(',', '').replace('$', '')
    min_hire_period = int(request.form['min_hire_period'])
    max_hire_period = int(request.form['max_hire_period'])
    cost = request.form['cost'].replace(',', '').replace('$', '')

    hire_cost = float(hire_cost)
    cost = float(cost)

    image = request.files.get('image')
    upload_folder = os.path.join('static', 'images', 'products')

    # Check if an image is uploaded
    if image and image.filename != '':
        image_filename = secure_filename(image.filename)
        # Ensure the directory exists
        os.makedirs(upload_folder, exist_ok=True)
        # Save the image to the products directory
        image.save(os.path.join(upload_folder, image_filename))
    else:
        image_filename = request.form.get('current_image', '')

    # SQL query to update equipment details
    sql = """UPDATE store_equipment 
             SET name = %s, specifications = %s, hire_cost = %s, cost = %s, min_hire_period = %s, max_hire_period = %s, image = %s
             WHERE store_id = %s AND equipment_id = %s;"""

    # Execute the SQL query
    cursor = getCursor()
    cursor.execute(sql, (name, specifications, hire_cost, cost, min_hire_period, max_hire_period, image_filename, store_id, equipment_id))
    cursor.close()

    flash('Equipment updated successfully!', 'success')
    return redirect(url_for('staff_product_details', store_id=store_id, equipment_id=equipment_id))


@app.route('/staff/check_customer', methods=['GET', 'POST'])
def staff_check_customer():
    
    # Retrieve customer records from the database
    connection = getCursor()
    connection.execute("select first_name,last_name,email,phone,address from customer ;")
    records = connection.fetchall()
  
    return render_template("./staff/staff_check_customer.html", records=records)


@app.route('/staff/check_equipment', methods=['GET', 'POST'])
def staff_check_equipment():

    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    connection = getCursor()
    
    # Retrieve categories from the database
    connection.execute('select category_id, category_name from category')
    cateogrys = connection.fetchall()

    # Get the store ID of the logged-in staff member
    connection.execute('select store_id from staff where username = %s',(username,))
    store_id = connection.fetchone()[0]

    # Query to fetch equipment details for the specific store
    connection.execute("""select s.name,s.image,s.category_id,a.total from store_equipment as s 
                       join (select equipment_id, count(serial_number) as total from inventory group by equipment_id) as a 
                       on s.equipment_id = a.equipment_id where s.store_id = %s""",(store_id,))
    category_list=connection.fetchall()

    return render_template("./staff/staff_check_equipment.html", records=category_list,cateogrys=cateogrys)

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


@app.route('/staff/inventory_list', methods=['GET', 'POST'])
def inventory_list():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session['username']
    store_id = get_store_id(username)

    if store_id is None:
        flash('No store found for the logged-in user', 'danger')
        return redirect(url_for('home'))  # Redirect to an appropriate page

    # Get filters from the form
    equipment_name = request.form.get('equipment_name', '')
    category_id = request.form.get('category_id', '')
    status = request.form.get('status', '')

    # Retrieve categories from the database
    cursor = getCursor()
    cursor.execute("SELECT * FROM category;")
    categories = cursor.fetchall()

    # Prepare the WHERE clause for filtering based on the form inputs
    where_clauses = ["se.store_id = %s"]
    args = [store_id]

    if equipment_name:
        where_clauses.append("se.name LIKE %s")
        args.append(f"%{equipment_name}%")
    if category_id:
        where_clauses.append("se.category_id = %s")
        args.append(category_id)
    if status:
        where_clauses.append("i.status = %s")
        args.append(status)

    where = " AND ".join(where_clauses)

    # Execute the query to fetch inventory list based on the filters
    cursor.execute(f"""
        SELECT se.equipment_id, se.name, se.specifications, se.cost, se.image, se.hire_cost,
               se.min_hire_period, se.max_hire_period, i.serial_number, i.status
        FROM store_equipment se
        JOIN inventory i ON se.equipment_id = i.equipment_id
        WHERE {where}
    """, args)

    equipment = cursor.fetchall()
    cursor.close()

    return render_template('staff/inventory_list.html', equipment=equipment,
                           status=status, category_id=category_id, equipment_name=equipment_name,
                           categories=categories, store_id=store_id)


@app.route('/staff/search', methods=['GET', 'POST'])
def staff_search():

    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route
    
    username=session.get('username')
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s',(username,))
    store_id = connection.fetchone()[0]

    if request.method =='POST':
        
        equipment_name = request.form.get('equipment_name')
        order_id = request.form.get('order_id')


        if equipment_name:
            # Search for equipment by name
            query = "select * from store_equipment where name Like %s and store_id = %s"
            search_pattern = f"%{equipment_name}%"
            connection.execute(query, (search_pattern,store_id))
            equipment_details = connection.fetchall()
        
            return render_template('/staff/search_equipment.html',equipment_details=equipment_details)
        
        elif order_id:
            # Search for booking details by order ID
            connection.execute("""select b.booking_id,s.store_name,b.total_amount,
                               b.booking_date,b.status from booking as b join store as s 
                               on b.store_id = s.store_id where booking_id = %s and b.store_id =%s""",(order_id,store_id))
            bookings = connection.fetchone()
            
            connection.execute("""select s.image, s.name,b.quantity,b.total,b.start_date,b.end_date
                               from booking_detail as b join store_equipment as s on b.equipment_id = s.equipment_id
                               where booking_id = %s""",(order_id,))
            booking_details = connection.fetchall()

        
            return render_template('/staff/search_booking.html',bookings=bookings,booking_details=booking_details)
        
        else:
            flash('Please enter search info.')
            return redirect('/staff/search')

    return render_template('/staff/search.html')


@app.route('/staff/edit_inventory/<int:store_id>/<int:equipment_id>/<string:serial_number>', methods=['GET', 'POST'])
def edit_inventory(store_id, equipment_id, serial_number):
    cursor = getCursor()

    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        purchase_date = request.form.get('purchase_date')
        status = request.form.get('status')

        # Update the inventory and equipment details in the database
        cursor.execute("""
            UPDATE store_equipment se
            JOIN inventory i ON se.equipment_id = i.equipment_id
            SET se.name = %s, i.purchase_date = %s, i.status = %s
            WHERE se.equipment_id = %s AND se.store_id = %s AND i.serial_number = %s
        """, (name, purchase_date, status, equipment_id, store_id, serial_number))

        cursor.close()
        flash('Inventory updated successfully!', 'success')
        return redirect(url_for('inventory_list'))
    else:
        # Fetch inventory details for the specified store, equipment, and serial number
        cursor.execute("""
            SELECT se.name, i.serial_number, i.purchase_date, i.status
            FROM store_equipment se
            JOIN inventory i ON se.equipment_id = i.equipment_id
            WHERE se.store_id = %s AND se.equipment_id = %s AND i.serial_number = %s
        """, (store_id, equipment_id, serial_number))

        inventory_items = cursor.fetchone()
        cursor.fetchall()  # This will clear any unread results
        cursor.close()

        return render_template('staff/edit_inventory.html', inventory_items=inventory_items, store_id=store_id, equipment_id=equipment_id, serial_number=serial_number)

    
@app.route('/staff/verify', methods=['GET', 'POST'])
def staff_verify():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    connection = getCursor()
    connection.execute('SELECT store_id FROM staff WHERE username = %s', (username,))
    store_id = connection.fetchone()[0]

    # Initialize variables to None
    customer_details = None
    bookings = None
    booking_details = None
    error_message = None

    if request.method == 'POST':
        booking_id = request.form.get('booking_id')

        if booking_id:
            try:
                booking_id_int = int(booking_id)
                # Fetch customer details for the provided booking ID and store ID
                connection.execute("""
                    SELECT c.last_name, c.first_name, c.date_of_birth, b.booking_id, c.image
                    FROM booking AS b
                    JOIN customer AS c ON b.customer_id = c.customer_id
                    WHERE b.booking_id = %s AND b.store_id = %s
                """, (booking_id_int, store_id))
                customer_details = connection.fetchone()

                if customer_details:
                    # Fetch booking details for the provided booking ID and store ID
                    connection.execute("""
                        SELECT b.booking_id, s.store_name, b.total_amount, b.booking_date, b.status
                        FROM booking AS b
                        JOIN store AS s ON b.store_id = s.store_id
                        WHERE b.booking_id = %s AND b.store_id = %s
                    """, (booking_id_int, store_id))
                    bookings = connection.fetchone()

                    # Fetch booking details for the provided booking ID
                    connection.execute("""
                        SELECT s.image, s.name, b.quantity
                        FROM booking_detail AS b
                        JOIN store_equipment AS s ON b.equipment_id = s.equipment_id
                        WHERE b.booking_id = %s
                    """, (booking_id_int,))
                    booking_details = connection.fetchall()

                    return render_template('staff/verify_booking.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details)
                else:
                    error_message = 'No booking found with the provided booking number.'
            except ValueError:
                error_message = 'Invalid booking number. Please enter a valid number.'
        else:
            error_message = 'Please enter the booking number.'

    return render_template('staff/verify.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details, error_message=error_message)


@app.route('/staff/feedback', methods=['GET', 'POST'])
def staff_feedback():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    connection = getCursor()
    connection.execute('select store_id from staff where username = %s', (username,))
    store_id = connection.fetchone()[0]

    # Fetch feedbacks for the current store
    connection.execute(
        "select feedback_id,name,email,feedback.phone,subject,create_time,store_name from feedback left join store on store.store_id=feedback.store_id where feedback.store_id =%s order by create_time desc",
        (store_id,))
    feedbacks = connection.fetchall()

    # Process feedbacks and format date
    feedbacks_result = []
    for feedback in feedbacks:
        feedback = list(feedback)
        feedback[5] = feedback[5].strftime('%d-%m-%Y %H:%M:%S')
        feedbacks_result.append(feedback)
    return render_template('/staff/feedback.html', feedbacks=feedbacks_result)


@app.route('/staff/feedback_detail', methods=['GET', 'POST'])
def staff_feedback_detail():
    username = session.get('username')

    if not username:
        return redirect('/login/')

    connection = getCursor()
    connection.execute('select account_id from account where username=%s', (username,))
    user_id = connection.fetchone()[0]
    if request.method == "GET":
        feedback_id = request.args.get('id')

        # Fetch feedback details
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

        # Process chat records and determine chat type (customer or staff)
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
        feedback = list(feedback)
        feedback[4] = feedback[4].strftime('%d-%m-%Y %H:%M:%S')
        return render_template('/staff/feedback_detail.html', feedback=feedback, chat_result=chat_result,
                               feedback_id=feedback_id)
    else:
        feedback_id = request.form.get('feedback_id')
        content = request.form.get('content', '')
        # Add message to feedback exchange
        connection.execute(
            "insert into feedback_exchange (sender_id,create_time,feedback_id,content) values (%s,%s,%s,%s)",
            (user_id, datetime.now(), feedback_id, content)
        )
        return redirect(url_for('staff_feedback_detail', id=feedback_id))



@app.route('/staff/check_request', methods=['GET'])
def staff_check_request():
    
    # Fetch all customer request records
    connection = getCursor()
    connection.execute("select * from customer_request;")
    records = connection.fetchall()
  
    return render_template("/staff/staff_check_request.html", records=records)

@app.route('/staff/check_report', methods=['GET'])
def staff_check_report():
    
    # Fetch all customer report records
    connection = getCursor()
    connection.execute("select * from customer_report;")
    records = connection.fetchall()
  
    return render_template("/staff/staff_check_report.html", records=records)


@app.route('/staff/in_and_out', methods=['GET'])
def staff_in_and_out():

    username = session.get('username')
    day = request.args.get('day')

    # Fetch the store_id associated with the staff username
    connection = getCursor()
    connection.execute(
            "select store_id from staff where username=%s;",(username,))
    store_id = connection.fetchone()[0]

    if day:

        # Fetch pickup and return records for the specified day and store_id
        connection.execute("""SELECT b.booking_id,i.pickup_time,b.start_date,b.quantity,s.name,s.image,i.record_id 
                        FROM in_out_record as i join booking_detail as b on i.detail_id = b.detail_id
                            join store_equipment as s on b.equipment_id=s.equipment_id
                        where b.start_date =%s and s.store_id = %s ;""",(day,store_id))
        pickUps = connection.fetchall()

        connection.execute("""SELECT b.booking_id,i.return_time,b.end_date,b.quantity,s.name,s.image,i.record_id,i.pickup_time
                        FROM in_out_record as i join booking_detail as b on i.detail_id = b.detail_id
                            join store_equipment as s on b.equipment_id=s.equipment_id
                        where b.end_date =%s and s.store_id =%s;""",(day,store_id))
        returns = connection.fetchall()
    
    else:

        day = date.today()

        # Fetch pickup and return records for today and store_id
        connection.execute("""SELECT b.booking_id,i.pickup_time,b.start_date,b.quantity,s.name,s.image,i.record_id 
                        FROM in_out_record as i join booking_detail as b on i.detail_id = b.detail_id
                            join store_equipment as s on b.equipment_id=s.equipment_id
                        where b.start_date =%s and s.store_id = %s ;""",(day,store_id,))
        pickUps = connection.fetchall()

        connection.execute("""SELECT b.booking_id,i.return_time,b.end_date,b.quantity,s.name,s.image,i.record_id
                        FROM in_out_record as i join booking_detail as b on i.detail_id = b.detail_id
                            join store_equipment as s on b.equipment_id=s.equipment_id
                        where b.end_date =%s and s.store_id =%s;""",(day,store_id,))
        returns = connection.fetchall()

    return render_template('/staff/InAndOut.html',pickUps=pickUps,day=day,returns=returns)

@app.route('/staff/equipment_pickup', methods=['GET'])
def staff_equipment_pickup():

    # Get the record_id and day from the request arguments
    record_id = request.args.get('record_id')
    day = request.args.get('day')

    # Update the pickup time for the specified record_id to the current time
    connection = getCursor()
    connection.execute("Update in_out_record set pickup_time = NOW() where record_id =%s ",(record_id,))

    # Construct the redirect URL with the specified day parameter
    redirect_url = url_for('staff_in_and_out',day=day)

    return redirect(redirect_url)


@app.route('/staff/equipment_return', methods=['GET'])
def staff_equipment_return():

    # Get the record_id and day from the request arguments
    record_id = request.args.get('record_id')
    day = request.args.get('day')

    # Update the return time for the specified record_id to the current time
    connection = getCursor()
    connection.execute("Update in_out_record set return_time = NOW() where record_id =%s ",(record_id,))

    # Construct the redirect URL with the specified day parameter
    redirect_url = url_for('staff_in_and_out',day=day)

    return redirect(redirect_url)


@app.route("/staff/news", methods=['GET', 'POST'])
def staff_news():

    # Fetch news items with store_id as null, ordered by news_id descending
    connection = getCursor()
    connection.execute(
            """select n.title,n.content,n.create_time
            from news as n where store_id is null
            order by n.news_id desc;""")
    news = connection.fetchall()

    return render_template('/staff/news.html',news=news)