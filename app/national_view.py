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

def get_national_details(username):
    cursor = getCursor()
    cursor.execute("""
        SELECT a.role
        FROM account a
        JOIN management m ON a.username = m.username
        WHERE a.username = %s
    """, (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    return None

@app.route('/national_dashboard')
def national_dashboard():
    if not session.get('loggedin') or session.get('role') != 'national_manager':
        return redirect(url_for('login'))

    # Fetch user details including first name, last name, position, and image
    username = session.get('username')
    connection = getCursor()
    connection.execute(
        "select first_name,last_name,position,image from management where username=%s;", (username,))
    name = connection.fetchone()

    # Fetch the latest news that is not specific to any store (store_id is null)
    connection.execute("""select n.title,n.content,n.create_time
            from news as n where store_id is null
            order by n.news_id desc """)
    news = connection.fetchone()


    return render_template('./national/national_dashboard.html', name=name,news=news)


@app.route('/national/personal', methods=['GET', 'POST'])
def national_personal():
    # After replacing it with session login ok
    username = session.get('username')

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

        # Fetch user details from the management table
        connection = getCursor()
        connection.execute(
            "select * from management where username=%s;", (username,))
        result = connection.fetchone()

        if result:
            # Update the record dictionary with fetched user details
            record['last_name'] = result[1]
            record['first_name'] = result[2]
            record['email'] = result[3]
            record['phone'] = result[4]
            record['address'] = result[5]
            record['Image'] = result[7]
        return render_template("./national/profile.html", record=record, username=username)
    else:

        # Get form data
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        Image = request.form.get('Image')

        # Update or insert user details into the management table
        connection = getCursor()
        connection.execute(
            "select * from management where username=%s;", (username,))
        result = connection.fetchone()
        if result:
            sql = "update  management set last_name=%s,first_name=%s,email=%s,phone=%s,address=%s,image=%s where username=%s"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image, username,))
        else:
            sql = "insert into management (last_name,first_name,email,phone,address,image,username) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            connection.execute(sql, (last_name, first_name, email, phone, address, Image, username,))
        flash("Update successful")
        return redirect("/national/personal")


@app.route('/national/password', methods=['GET', 'POST'])
def national_password():
    username = session.get('username')

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if all fields are filled
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template("./national/password.html")

        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template("./national/password.html")

        # Check password strength
        if len(new_password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            return render_template("./national/password.html")

        # Fetch the hashed password from the database
        cursor = getCursor()
        cursor.execute('SELECT password FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            # Verify old password
            if check_password_hash(account[0], old_password):
                # Hash and update new password
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE account SET password = %s WHERE username = %s', (hashed_password, username))
                flash('Password is changed successfully.', 'success')
            else:
                flash('Old password is incorrect.', 'error')
        else:
            flash('Account not found.', 'error')
            
    return render_template("./national/password.html")


@app.route('/national/promotion', methods=['GET', 'POST'])
def national_promotion():

    # Fetch all stores for display
    connection = getCursor()
    connection.execute(
        "select store_id,store_name from store;")
    stores = connection.fetchall()

    # Fetch promotions for all stores
    connection.execute("select p.*,s.store_name from promotion as p join store as s on p.store_id = s.store_id;")
    promotions= connection.fetchall()


    return render_template('/national/promotion.html',stores=stores,promotions=promotions)


@app.route('/national/promotion_edit', methods=['GET', 'POST'])
def national_promotion_edit():

    # Get the promotion_id from the query string
    promotion_id = request.args.get('promotion_id')

    connection = getCursor()
    connection.execute("""select p.*,s.store_name from promotion as p join store as s 
                       on p.store_id = s.store_id where promotion_id = %s""",(promotion_id,))
    promotion = connection.fetchone()


    if request.method =='POST':
        # Fetch form data
        promotion_id = request.form.get('promotion_id')
        code= request.form.get('code')
        info = request.form.get('info')
        start = request.form.get('start')
        end= request.form.get('end')
        discount = request.form.get('discount')
        store_id = request.form.get('store_id')

        # Update the promotion details in the database
        connection.execute("""Update promotion set promotion_name =%s,description=%s,start_day=%s,
                            end_day = %s, discount_rate=%s,store_id=%s
                            where promotion_id = %s""",(code,info,start,end,discount,store_id,promotion_id))
        flash('Promition updated successfully!','success')

        return redirect('/national/promotion')


    return render_template('/national/promotion_edit.html',promotion=promotion)


@app.route('/national/promotion_cancel', methods=['GET', 'POST'])
def national_promotion_cancel():

    # Get the promotion_id from the query string
    promotion_id = request.args.get('promotion_id')

    # Execute the SQL delete statement to delete the promotion
    connection = getCursor()
    connection.execute('Delete from promotion where promotion_id = %s',(promotion_id,))
    flash('Promotion deleted successfully!','success')
    return redirect('/national/promotion')

@app.route('/national/promotion_new', methods=['GET', 'POST'])
def national_promotion_new():
 
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  
    
    # Fetch all stores from the database
    connection = getCursor()
    connection.execute('select store_id,store_name from store')
    stores= connection.fetchall()

    if request.method =='POST':
       store_id = request.form.get('store')
       code = request.form.get('code')
       info = request.form.get('info')
       start = request.form.get('start')
       end = request.form.get('end')
       discount = request.form.get('discount')

       if store_id =='all':

           # If 'all' stores selected, iterate over all stores and insert a promotion for each
           for i in range(1,len(stores)+1):
              
            connection.execute("""Insert into promotion (promotion_name,description,start_day,end_day,discount_rate,store_id) 
                            values(%s,%s,%s,%s,%s,%s)""",(code,info,start,end,discount,i))
       else:
            # Insert a promotion for the selected store only
            connection.execute("""Insert into promotion (promotion_name,description,start_day,end_day,discount_rate,store_id) 
                            values(%s,%s,%s,%s,%s,%s)""",(code,info,start,end,discount,store_id))
        
       flash('Promition added successfully!','success')
       return redirect('/national/promotion')
    
    return render_template('/national/promotion_new.html',stores=stores)

@app.route('/national/national_add_new_equipment', methods=['GET', 'POST'])
def national_add_new_equipment():
    if request.method == "GET":

        # Fetch category records from the database
        connection = getCursor()
        connection.execute("SELECT category_id, category_name FROM category")
        category_records = connection.fetchall()

        # Format category records into a list of dictionaries
        category_list = [{"category_id": record[0], "category_name": record[1]} for record in category_records]

        # Fetch store records from the database
        connection.execute("SELECT store_id, store_name FROM store")
        store_records = connection.fetchall()

        # Format store records into a list of dictionaries
        store_list = [{"store_id": record[0], "store_name": record[1]} for record in store_records]

        return render_template("/national/national_add_new_equipment.html", category_list=category_list, store_list=store_list)
    
    else:
        # Get form data from the request
        store_id = request.form.get('store_id')
        name = request.form.get('name')
        specifications = request.form.get('specifications')
        cost = request.form.get('cost')
        image = request.form.get('Image')  # Note: This should match the hidden input field's name
        hire_cost = request.form.get('hire_cost')
        category_id = request.form.get('category_id')
        min_hire_period = request.form.get('min_hire_period')
        max_hire_period = request.form.get('max_hire_period')
        inventory = request.form.get('inventory')
        purchase_date = request.form.get('purchase_date')

        # Insert new equipment details into the store_equipment table
        conn = getCursor()
        conn.execute(
            "INSERT INTO store_equipment (name, specifications, cost, image, hire_cost, category_id, store_id, min_hire_period, max_hire_period) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (name, specifications, cost, image, hire_cost, category_id, store_id, min_hire_period, max_hire_period)
        )
        new_id = conn.lastrowid

        # Insert inventory records for the new equipment
        for i in range(int(inventory)):
            conn.execute(
                "INSERT INTO inventory (store_id, equipment_id, purchase_date, status) "
                "VALUES (%s, %s, %s, %s)",
                (store_id, new_id, purchase_date, 'available')
            )
        flash('New equipment added successfully!', 'success')
        return redirect("/national_dashboard")


def category():
    connection = getCursor()
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()  
    return categorys

@app.route('/national/national_product', methods=['GET', 'POST'])
def national_product():
    print(f"Session Data: {session}")

    # Check if the user is logged in and has the role of a national manager
    if not session.get('loggedin') or session.get('role') != 'national_manager':
        print(f"Access Denied: loggedin={session.get('loggedin')}, role={session.get('role')}")  
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('login'))

    categorys = category()
    category_id = request.args.get('category')
    
    # Fetch stores data
    cursor = getCursor()
    cursor.execute("SELECT store_id, store_name FROM store")
    stores = cursor.fetchall()

    # Fetch products based on the category ID
    connection = getCursor()
    connection.execute("""
        SELECT equipment_id, name, image, store_id, hire_cost 
        FROM store_equipment 
        WHERE category_id = %s;
    """, (category_id,))
    products = connection.fetchall()

    # Fetch the category name based on the category ID
    connection.execute("""
        SELECT category_name 
        FROM category 
        WHERE category_id = %s;
    """, (category_id,))
    category_result = connection.fetchone()

    # Check if the category name is fetched successfully
    if category_result:
        category_name = category_result[0]
    else:
        category_name = ""

    return render_template('/national/national_product.html', products=products, category_name=category_name, categorys=categorys, stores=stores)


@app.template_filter('format_price')
def format_price(value):
    return "${:,.2f}".format(value)
app.jinja_env.filters['format_price'] = format_price

@app.route('/national/national_product_details', methods=['GET', 'POST'])
def national_product_details():
    username = session.get('username')
    role = get_national_details(username)

    if role != 'national_manager':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('national_dashboard'))

    categorys = category()

    equipment_id = request.args.get('equipment_id')

    # SQL query to fetch product details based on equipment ID
    sql = """
        SELECT name, specifications, e.image, hire_cost, min_hire_period, max_hire_period, s.stock, c.category_id, c.category_name, cost
        FROM store_equipment AS e 
        LEFT JOIN (SELECT store_id, equipment_id, IFNULL(COUNT(serial_number), 0) AS stock 
                   FROM inventory WHERE status = 'available' 
                   GROUP BY store_id, equipment_id) AS s 
        ON e.store_id = s.store_id AND e.equipment_id = s.equipment_id 
        INNER JOIN category AS c ON e.category_id = c.category_id 
        WHERE e.equipment_id = %s;
    """

    # Execute the SQL query to fetch product details
    connection = getCursor()
    connection.execute(sql, (equipment_id,))
    details = connection.fetchone()

    return render_template('/national/national_product_details.html', details=details, equipment_id=equipment_id, categorys=categorys)


@app.route('/national/national_update_equipment', methods=['POST'])
def national_update_equipment_route():
    username = session.get('username')
    role = get_national_details(username)

    if role != 'national_manager':
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('national_dashboard'))

    # Get form data from the request
    equipment_id = request.form['equipment_id']
    name = request.form['name']
    specifications = request.form['specifications']
    hire_cost = request.form['hire_cost'].replace(',', '').replace('$', '')
    min_hire_period = int(request.form['min_hire_period'])
    max_hire_period = int(request.form['max_hire_period'])
    cost = request.form['cost'].replace(',', '').replace('$', '')

    # Convert hire_cost and cost to float values
    hire_cost = float(hire_cost)
    cost = float(cost)
    
    # Define the upload folder path
    image = request.files.get('image')
    upload_folder = os.path.join('static', 'images', 'products')

    # Check if an image was uploaded
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
             WHERE equipment_id = %s;"""

    # Execute the SQL query to update equipment details
    cursor = getCursor()
    cursor.execute(sql, (name, specifications, hire_cost, cost, min_hire_period, max_hire_period, image_filename, equipment_id))
    cursor.close()

    flash('Equipment updated successfully!', 'success')
    return redirect(url_for('national_product_details', equipment_id=equipment_id))


@app.route('/national/national_check_customer', methods=['GET', 'POST'])
def national_check_customer():
    connection = getCursor()

    # Fetch customer data with store information
    connection.execute("""
        SELECT c.first_name, c.last_name, c.email, c.phone, c.address, s.store_name, s.store_id
        FROM customer c
        LEFT JOIN store s ON c.store_id = s.store_id
    """)
    records = connection.fetchall()

    # Fetch store list
    connection.execute("SELECT store_id, store_name FROM store")
    stores = connection.fetchall()

    return render_template("national/national_check_customer.html", records=records, stores=stores)

@app.route('/national/national_check_equipment', methods=['GET', 'POST'])
def national_check_equipment():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure a login route

    username = session.get('username')
    connection = getCursor()

    # Fetch categories from the database
    connection.execute('SELECT category_id, category_name FROM category')
    cateogrys = connection.fetchall()

    # Fetch stores from the database
    connection.execute('SELECT store_id, store_name FROM store')
    stores = connection.fetchall()

    # Fetch equipment details along with the total count from inventory
    connection.execute("""SELECT s.store_id, s.name, s.image, s.category_id, a.total 
                          FROM store_equipment AS s 
                          JOIN (SELECT equipment_id, COUNT(serial_number) AS total 
                                FROM inventory 
                                GROUP BY equipment_id) AS a 
                          ON s.equipment_id = a.equipment_id""")
    category_list = connection.fetchall()

    return render_template("national/national_check_equipment.html", records=category_list, cateogrys=cateogrys, stores=stores)

@app.route('/national/national_inventory_list', methods=['GET', 'POST'])
def national_inventory_list():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    connection = getCursor()

    # Get filter parameters from the form
    equipment_name = request.form.get('equipment_name', '')
    category_id = request.form.get('category_id', '')
    store_id = request.form.get('store_id', '')
    status = request.form.get('status', '')

    # Fetch categories and stores from the database
    cursor = getCursor()
    cursor.execute("SELECT * FROM category;")
    categories = cursor.fetchall()
    cursor.execute("SELECT store_id, store_name FROM store;")
    stores = cursor.fetchall()
    
    where_clauses = []
    args = []

    # Check each filter parameter and construct WHERE clauses accordingly
    if equipment_name:
        where_clauses.append("se.name LIKE %s")
        args.append(f"%{equipment_name}%")
    if category_id:
        where_clauses.append("se.category_id = %s")
        args.append(category_id)
    if store_id:
        where_clauses.append("se.store_id = %s")
        args.append(store_id)
    if status:
        where_clauses.append("i.status = %s")
        args.append(status)

    # Join WHERE clauses using AND if any are present, otherwise use 1=1 (always true)
    where = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Execute SQL query with dynamic WHERE clauses and arguments
    cursor.execute(f"""
        SELECT se.equipment_id, se.name, se.specifications, se.cost, se.image, se.hire_cost,
               se.min_hire_period, se.max_hire_period, i.serial_number, i.status, st.store_name, se.store_id
        FROM store_equipment se
        JOIN inventory i ON se.equipment_id = i.equipment_id
        JOIN store st ON se.store_id = st.store_id
        WHERE {where}
    """, args)

    equipment = cursor.fetchall()
    cursor.close()

    return render_template('national/national_inventory_list.html', equipment=equipment,
                           status=status, category_id=category_id, equipment_name=equipment_name,
                           categories=categories, stores=stores, store_id=store_id)


@app.route('/national/national_search', methods=['GET', 'POST'])
def national_search():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    connection = getCursor()

    if request.method == 'POST':
        equipment_name = request.form.get('equipment_name')
        order_id = request.form.get('order_id')

        if equipment_name:

            # Search for equipment by name
            query = "SELECT * FROM store_equipment WHERE name LIKE %s"
            search_pattern = f"%{equipment_name}%"
            connection.execute(query, (search_pattern,))
            equipment_details = connection.fetchall()

            return render_template('national/national_search_equipment.html', equipment_details=equipment_details)

        elif order_id:

            # Search for booking details by order ID
            connection.execute("""SELECT b.booking_id, s.store_name, b.total_amount,
                               b.booking_date, b.status 
                               FROM booking AS b 
                               JOIN store AS s ON b.store_id = s.store_id 
                               WHERE b.booking_id = %s""", (order_id,))
            bookings = connection.fetchone()

            connection.execute("""SELECT s.image, s.name, b.quantity, b.total, b.start_date, b.end_date
                               FROM booking_detail AS b 
                               JOIN store_equipment AS s ON b.equipment_id = s.equipment_id 
                               WHERE b.booking_id = %s""", (order_id,))
            booking_details = connection.fetchall()

            return render_template('national/national_search_booking.html', bookings=bookings, booking_details=booking_details)
        
        else:
            flash('Please enter search info.')
            return redirect(url_for('national_search'))

    return render_template('national/national_search.html')



@app.route('/national/national_edit_inventory/<int:store_id>/<int:equipment_id>/<string:serial_number>', methods=['GET', 'POST'])
def national_edit_inventory(store_id, equipment_id, serial_number):
    cursor = getCursor()

    if request.method == 'POST':
        # Fetch form data
        name = request.form.get('name')
        purchase_date = request.form.get('purchase_date')
        status = request.form.get('status')
        new_store_id = request.form.get('store_id')

        try:
            # Update inventory information
            cursor.execute("""
                UPDATE store_equipment se
                JOIN inventory i ON se.equipment_id = i.equipment_id
                SET se.name = %s, i.purchase_date = %s, i.status = %s, se.store_id = %s
                WHERE se.equipment_id = %s AND se.store_id = %s AND i.serial_number = %s
            """, (name, purchase_date, status, new_store_id, equipment_id, store_id, serial_number))
            
            cursor.close()
            flash('Inventory updated successfully!', 'success')
        except mysql.connector.errors.IntegrityError as e:
            flash(f'Error updating inventory: {str(e)}', 'danger')
        return redirect(url_for('national_inventory_list'))
    else:
        # Get information for the specified inventory item and related store information
        cursor.execute("""
            SELECT se.name, i.serial_number, i.purchase_date, i.status, s.store_name, se.store_id
            FROM store_equipment se
            JOIN inventory i ON se.equipment_id = i.equipment_id
            JOIN store s ON se.store_id = s.store_id
            WHERE se.store_id = %s AND se.equipment_id = %s AND i.serial_number = %s
        """, (store_id, equipment_id, serial_number))

        inventory_items = cursor.fetchone()
        cursor.fetchall()  # Fetch any remaining results
        cursor.close()

        cursor = getCursor()
        cursor.execute("SELECT store_id, store_name FROM store")
        stores = cursor.fetchall()
        cursor.close()

        return render_template('national/national_edit_inventory.html', inventory_items=inventory_items, stores=stores, current_store_id=store_id, equipment_id=equipment_id, serial_number=serial_number)


@app.route('/national/national_verify', methods=['GET', 'POST'])
def national_verify():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    connection = getCursor()

    customer_details = None
    bookings = None
    booking_details = None
    error_message = None

    if request.method == 'POST':
        booking_id = request.form.get('booking_id')

        if booking_id:
            try:
                # Fetch customer details for the provided booking ID
                booking_id_int = int(booking_id)
                connection.execute("""
                    SELECT c.last_name, c.first_name, c.date_of_birth, b.booking_id, c.image
                    FROM booking AS b
                    JOIN customer AS c ON b.customer_id = c.customer_id
                    WHERE b.booking_id = %s
                """, (booking_id_int,))
                customer_details = connection.fetchone()

                if customer_details:
                    # Fetch booking details for the provided booking ID
                    connection.execute("""
                        SELECT b.booking_id, s.store_name, b.total_amount, b.booking_date, b.status
                        FROM booking AS b
                        JOIN store AS s ON b.store_id = s.store_id
                        WHERE b.booking_id = %s
                    """, (booking_id_int,))
                    bookings = connection.fetchone()

                    # Fetch booking details for equipment associated with the booking ID
                    connection.execute("""
                        SELECT s.image, s.name, b.quantity
                        FROM booking_detail AS b
                        JOIN store_equipment AS s ON b.equipment_id = s.equipment_id
                        WHERE b.booking_id = %s
                    """, (booking_id_int,))
                    booking_details = connection.fetchall()

                    return render_template('national/national_verify_booking.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details)
                else:
                    error_message = 'No booking found with the provided booking number.'
            except ValueError:
                error_message = 'Invalid booking number. Please enter a valid number.'
        else:
            error_message = 'Please enter the booking number.'

    return render_template('national/national_verify.html', customer_details=customer_details, bookings=bookings, booking_details=booking_details, error_message=error_message)


@app.route('/national/national_check_request', methods=['GET'])
def national_check_request():
    
    # Fetch all records from the customer_request table
    connection = getCursor()
    connection.execute("select * from customer_request;")
    records = connection.fetchall()
  
    return render_template("/national/national_check_request.html", records=records)

@app.route('/national/national_check_report', methods=['GET'])
def national_check_report():
    
    # Fetch all records from the customer_report table
    connection = getCursor()
    connection.execute("select * from customer_report;")
    records = connection.fetchall()
  
    return render_template("/national/national_check_report.html", records=records)


@app.route('/national/report_analysis', methods=['GET', 'POST'])
def national_report_analysis():
    if not session.get('loggedin') or session.get('role') != 'national_manager':
        return redirect(url_for('login'))

    connection = getCursor()

    try:
        # Total Revenue
        connection.execute("""
            SELECT SUM(amount) FROM payment WHERE status = 'successful';
        """)
        total_revenue = connection.fetchone()[0]

        # Monthly Revenue
        connection.execute("""
            SELECT DATE_FORMAT(payment_date, '%Y-%m') AS Month, SUM(amount) AS Revenue
            FROM payment
            WHERE status = 'successful'
            GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
            ORDER BY DATE_FORMAT(payment_date, '%Y-%m');
        """)
        monthly_revenue = connection.fetchall()

        # Create a dictionary with all months and initialize values to 0
        all_months = ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09', '2024-10', '2024-11', '2024-12']
        monthly_revenue_dict = {month: 0 for month in all_months}
        for row in monthly_revenue:
            monthly_revenue_dict[row[0]] = row[1]

        monthly_revenue_labels = list(monthly_revenue_dict.keys())
        monthly_revenue_values = list(monthly_revenue_dict.values())

        # Payment Successful Rate
        connection.execute("""
            SELECT 
                (SELECT COUNT(*) FROM payment WHERE status = 'successful') AS successful_payments,
                (SELECT COUNT(*) FROM payment) AS total_payments;
        """)
        payment_counts = connection.fetchone()
        payment_successful_rate = (payment_counts[0] / payment_counts[1]) * 100
        payment_successful_rate = f"{payment_successful_rate:.2f}%"

        # Number of Customers
        connection.execute("""
            SELECT COUNT(DISTINCT customer_id) FROM customer;
        """)
        number_of_customers = connection.fetchone()[0]

        # Monthly Number of Clients
        connection.execute("""
            SELECT DATE_FORMAT(join_date, '%Y-%m') AS Month, COUNT(DISTINCT customer_id) AS Clients
            FROM customer
            GROUP BY DATE_FORMAT(join_date, '%Y-%m')
            ORDER BY DATE_FORMAT(join_date, '%Y-%m');
        """)
        monthly_clients = connection.fetchall()

        # Prepare complete list of months with zero values for missing months
        monthly_clients_dict = {month: 0 for month in all_months}
        for row in monthly_clients:
            monthly_clients_dict[row[0]] = row[1]

        monthly_clients_labels = list(monthly_clients_dict.keys())
        monthly_clients_values = list(monthly_clients_dict.values())

        # Top 5 Most Booked Equipment
        connection.execute("""
            SELECT e.name, COUNT(bd.equipment_id) AS bookings
            FROM booking_detail bd
            JOIN store_equipment e ON bd.equipment_id = e.equipment_id
            JOIN booking b ON bd.booking_id = b.booking_id
            JOIN payment p ON p.booking_id = b.booking_id
            WHERE p.status = 'successful'
            GROUP BY bd.equipment_id
            ORDER BY bookings DESC
            LIMIT 5;
        """)
        top_5_booked = connection.fetchall()

        # Revenue Rank by Store
        connection.execute("""
            SELECT s.store_name, SUM(p.amount) AS revenue
            FROM payment p
            JOIN booking b ON p.booking_id = b.booking_id
            JOIN store s ON b.store_id = s.store_id
            WHERE p.status = 'successful'
            GROUP BY s.store_id
            ORDER BY revenue DESC;
        """)
        revenue_rank_by_store = connection.fetchall()

        # Equipment Available Rate
        connection.execute("""
            SELECT 
                (SELECT COUNT(*) FROM inventory WHERE status = 'available') AS available_equipment,
                (SELECT COUNT(*) FROM inventory) AS total_equipment;
        """)
        equipment_counts = connection.fetchone()
        equipment_available_rate = (equipment_counts[0] / equipment_counts[1]) * 100
        equipment_available_rate = f"{equipment_available_rate:.2f}%"

    finally:
        connection.close()

    return render_template(
        "national/report_analysis.html",
        total_revenue=total_revenue,
        monthly_revenue_labels=monthly_revenue_labels,
        monthly_revenue_values=monthly_revenue_values,
        payment_successful_rate=payment_successful_rate,
        number_of_customers=number_of_customers,
        monthly_clients_labels=monthly_clients_labels,
        monthly_clients_values=monthly_clients_values,
        top_5_booked=top_5_booked,
        revenue_rank_by_store=revenue_rank_by_store,
        equipment_available_rate=equipment_available_rate
    )


@app.route('/national/create_staff', methods=['GET', 'POST'])
def create_staff():
    if not session.get('loggedin') or session.get('role') != 'national_manager':
        return redirect(url_for('login'))

    if request.method == 'POST':

        # Fetch form data
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        store_id = request.form['store']
        address = request.form['address']
        position = 'Staff'
        role = 'staff'
        image = request.files.get('UploadImage')

        # Check for existing username and email
        cursor = getCursor()
        cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
        username_exists = cursor.fetchone()
        cursor.execute('SELECT * FROM staff WHERE email = %s', (email,))
        email_exists = cursor.fetchone()

        # Validation checks for form data
        if not all([username, password, confirm_password, first_name]):
            flash('Username, password, confirmed password, first name are required.', 'error')
            return redirect('/national/create_staff')
        if '@' not in email:
            flash('Please provide a valid email.', 'error')
            return redirect('/national/create_staff')
        if username_exists:
            flash('Username already exists!', 'error')
            return redirect('/national/create_staff')
        if email_exists:
            flash('Email already exists!', 'error')
            return redirect('/national/create_staff')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect('/national/create_staff')
        if len(password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            return redirect('/national/create_staff')

        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('static/images/profile', image_filename)
            image.save(image_path)
        else:
            image_filename = 'default.png'

        hashed_password = generate_password_hash(password)

        cursor = getCursor()
        try:
            # Insert new account and staff records
            cursor.execute("""
                INSERT INTO account (username, password, role)
                VALUES (%s, %s, %s)
            """, (username, hashed_password, role))

            cursor.execute("""
                INSERT INTO staff (last_name, first_name, email, phone, address, position, image, username, store_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (last_name, first_name, email, phone, address, position, image_filename, username, store_id))

            flash('Staff profile created successfully', 'success')
            return redirect(url_for('create_staff'))

        except mysql.connector.Error as err:
            cursor.rollback()
            flash(f'Error: {err}', 'error')
        finally:
            cursor.close()

    connection = getCursor()
    connection.execute("select /*+parallel(16)*/ store_id,store_name from store;")
    stores = {k:v for k,v in connection.fetchall()} 

    return render_template("./national/create_staff.html", stores=stores)

@app.route('/national/store_staff', methods=['GET', 'POST'])
def natioanl_store_staff():
    try:
        store_id = ''   # Initialize store_id variable

        # Fetch all stores to populate the dropdown menu
        connection = getCursor()
        connection.execute("select /*+parallel(16)*/ store_id,store_name from store;")
        stores = {k:v for k,v in connection.fetchall()}

        # Check if a specific store is selected, then fetch staff for that store; otherwise, fetch all staff
        store_id = request.args.get('store')
        if store_id:
            connection.execute("select staff_id, image, concat(first_name, ' ', last_name), status as name from staff where store_id=%s;", (store_id,))
        else:
            connection.execute("select staff_id, image, concat(first_name, ' ', last_name), status as name from staff;")
        
        staff_list = connection.fetchall()
        
    except Exception as excp:
        return str(excp), 500
    
    return render_template("./national/store_staff.html", staff_list=staff_list, stores=stores, selected_store=store_id)

@app.route('/national/manage_staff', methods=['GET', 'POST'])
def manage_staff():
    staff_id = request.args.get('staff_id')
    cursor = getCursor()  

    if request.method == 'POST':

        # Fetch form data for updating the staff profile
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        position = request.form['position']
        status = request.form['status']
        image = request.files.get('UploadImage')

        # Handle image upload and update the image filename accordingly
        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            image_path = os.path.join('static/images', image_filename)
            image.save(image_path)
        else:
            image_filename = request.form['Image']

        # Update the staff profile in the database
        cursor.execute("""
            UPDATE staff 
            SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s, position=%s, status=%s, image=%s 
            WHERE staff_id=%s
        """, (first_name, last_name, email, phone, address, position, status, image_filename, staff_id))
        
        connection.commit() 

        flash('Profile updated successfully', 'success')
        return redirect(url_for('manage_staff', staff_id=staff_id))
    
    # Fetch the staff profile information from the database
    cursor.execute("SELECT first_name, last_name, email, phone, address, position, status, image FROM staff WHERE staff_id=%s;", (staff_id,))
    staff_profile = cursor.fetchone()
    
    # Check if the staff profile exists
    if not staff_profile:
        flash('Staff profile not found', 'danger')
        return redirect(url_for('staff_dashboard'))  

    # Format the staff profile data for rendering in the template
    staff_profile = {
        'first_name': staff_profile[0],
        'last_name': staff_profile[1],
        'email': staff_profile[2],
        'phone': staff_profile[3],
        'address': staff_profile[4],
        'position': staff_profile[5],
        'status': staff_profile[6],
        'image': staff_profile[7]
    }
    
    return render_template("./national/manage_staff.html", staff_profile=staff_profile)


@app.route("/national/add_news", methods=['GET', 'POST'])
def national_add_news():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':

        # Fetch form data for adding news
        title = request.form.get('title')
        content = request.form.get('content')

        connection = getCursor()

        # Insert the news into the database
        connection.execute("""Insert into news (title,content) 
                          values(%s,%s)""", (title, content))

        flash('News published successfully', 'success')

        return redirect('/national/add_news')

    return render_template('/national/add_news.html')


@app.route("/national/news", methods=['GET', 'POST'])
def national_news():

    # Fetch national news from the database
    connection = getCursor()
    connection.execute(
        """select n.title,n.content,n.create_time
        from news as n where store_id is null
        order by n.news_id desc;""")
    news = connection.fetchall()

    return render_template('/national/news.html', news=news)

