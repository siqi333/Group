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
from datetime import date, timedelta,datetime
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


def category():
    connection = getCursor()
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()  
    return categorys

def store():
    connection = getCursor()
    connection.execute(
            "select store_id,store_name from store;")
    stores = connection.fetchall()  
    return stores


def time_change(date):
    date = date.strftime("%d/%m/%Y")
    return date


@app.route('/customer_dashboard')
def customer_dashboard():

    # Get the username from the session
    username = session.get('username')

    # Establish a database connection and get a cursor
    connection = getCursor()

    # Execute a query to fetch customer details based on the username
    connection.execute(
            "select first_name,last_name,customer_id from customer where username=%s;", (username,))
    name = connection.fetchone()  # Fetch the customer's name and ID
    customer_id = name[2]  # Extract the customer ID from the fetched data
    
    categorys=category()
    

    connection = getCursor()
    # Execute queries to fetch pickup and return information for the customer
    connection.execute("""select start_date,count(quantity) from booking_detail as d join booking as b 
                       on d.booking_id =b.booking_id where b.customer_id = %s
                       group by start_date""",(customer_id,))
    pickups = connection.fetchall()

    connection.execute("""select end_date,count(quantity) from booking_detail as d join booking as b 
                       on d.booking_id =b.booking_id where b.customer_id = %s
                       group by end_date""",(customer_id,))
    returns = connection.fetchall()

    today = datetime.now().date()

    # Execute a query to fetch the latest news
    connection.execute("""select title,create_time,store_name from news as n join store as s on n.store_id = s.store_id 
                        order by news_id desc limit 1 """)
    news = connection.fetchone()

    # Ensure the user is logged in and has the correct role
    if not session.get('loggedin') or session.get('role') != 'customer':
        return redirect(url_for('login'))
    
    return render_template('./customer/customer_dashboard.html',name=name,categorys=categorys,returns=returns,pickups=pickups,today=today,news=news)


@app.route('/customer/personal', methods=['GET', 'POST'])
def customer_personal():
    # Get the username from the session
    username= session.get('username')

    categorys=category()

    if request.method == "GET":

        # Initialize a dictionary with default values for the customer's record
        record = {
            "last_name": "",
            "first_name": "",
            "email": "",
            "phone": "",
            "address": "",
            "date_of_Birth": "",
            "Image": "",
        }

        # Fetch the customer's information from the database
        connection = getCursor()
        connection.execute(
            "select * from customer where username=%s;", (username,))
        result = connection.fetchone()

        # Update the record dictionary if the customer information is found
        if result:
            record['last_name'] = result[1]
            record['first_name'] = result[2]
            record['email'] = result[3]
            record['phone'] = result[4]
            record['address'] = result[5]
            record['date_of_Birth'] = result[6]
            record['Image'] = result[7]
        return render_template("./customer/profile.html", record=record,username=username,categorys=categorys)
    
    else:

        # Extract form data from the POST request
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        # date_of_Birth = request.form.get('date_of_Birth')
        # Image = request.form.get('Image')

        # Fetch the customer's information from the database
        connection = getCursor()
        connection.execute(
            "select * from customer where username=%s;", (username,))
        result = connection.fetchone()

        # Update the customer's information in the database
        sql = "update  customer set last_name=%s,first_name=%s,email=%s,phone=%s,address=%s where username=%s"
        connection.execute(sql, (last_name, first_name, email, phone, address, result[-1]))
        flash("Update Successful")

        return redirect("/customer/personal")
      

@app.route('/customer/password', methods=['GET', 'POST'])
def customer_password():

    username = session.get('username')

    categorys=category()

    if request.method == 'POST':

        # Get form data from the POST request
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Check if all required fields are provided
        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template("./customer/password.html")

        # Check if the new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template("./customer/password.html")

        # Check if the new password meets the criteria (at least 8 characters with letters and numbers)
        if len(new_password) < 8 or not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', new_password):
            flash('Password must be at least 8 characters long and contain a mix of letters and numbers.', 'error')
            return render_template("./customer/password.html")

        # Fetch the hashed password from the database based on the username
        cursor = getCursor()
        cursor.execute('SELECT password FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()

        # Check if the account exists and if the old password is correct
        if account:
            if check_password_hash(account[0], old_password):
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE account SET password = %s WHERE username = %s', (hashed_password, username))
                flash('Password is changed successfully.', 'success')
            else:
                flash('Old password is incorrect.', 'error')
        else:
            flash('Account not found.', 'error')

    return render_template("./customer/password.html",categorys=categorys)


@app.route('/customer/product', methods=['GET', 'POST'])
def customer_product():

    categorys=category()

    # Get the category_id from the request arguments
    category_id = request.args.get('category')

    connection = getCursor()

    # Fetch products based on the specified category_id
    connection.execute(
            """select equipment_id,name,image,store_id,hire_cost from store_equipment where category_id =%s;""",(category_id,))
    products= connection.fetchall()

    # Fetch the category name based on the category_id
    connection.execute(
            "select category_name from category where category_id =%s;",(category_id,))
    category_name= connection.fetchone()[0]

    stores = store()

    return render_template('/customer/product.html',stores=stores,products=products,category_name=category_name,categorys=categorys)


@app.route('/customer/product_details', methods=['GET', 'POST'])
def customer_product_details():

    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route
    
    username=session.get('username')

    # Fetch the customer_id based on the username
    connection = getCursor()
    connection.execute('select customer_id from customer where username = %s',(username,))
    customer_id = connection.fetchone()[0]

    categorys=category()

    # Get store_id and equipment_id from the request arguments
    store_id = request.args.get('store_id')
    equipment_id = request.args.get('equipment_id')

    # SQL query to fetch detailed product information including availability and stock
    sql = """SELECT name,specifications,e.image,hire_cost,min_hire_period,max_hire_period,s.stock,c.category_id,c.category_name FROM store_equipment as e 
             left join (SELECT store_id,equipment_id,ifnull(count(serial_number),0) as stock FROM inventory where status ='available'
             group by store_id, equipment_id) as s on e.store_id= s.store_id and e.equipment_id = s.equipment_id
             inner join category as c on e.category_id = c.category_id where e.store_id =%s and e.equipment_id =%s;"""

    connection = getCursor()
    connection.execute(sql,(store_id,equipment_id))
    details = connection.fetchone()

    # Check if the product exists in the shopping cart
    connection.execute("""select * from shoppingcart where equipment_id =%s and customer_id =%s""",(equipment_id,customer_id))
    detail_exist = connection.fetchone()

    # Set a flag to determine if the product can be added to the cart (1 for yes, 0 for no)
    no_process = 1
    if detail_exist:
        no_process=0
    
    # Fetch booked dates for the product that are still valid (end_date > current date and status = 'paid')
    connection.execute("""select equipment_id,start_date,end_date,quantity from booking_detail as d 
                       join booking as b on d.booking_id = b.booking_id
                       where equipment_id =%s and end_date > curdate() and b.status ='paid'""",(equipment_id,))
    booked_dates = connection.fetchall()

    return render_template('/customer/product_details.html',details = details,equipment_id=equipment_id,store_id=store_id,categorys=categorys,no_process = no_process,booked_dates=booked_dates)


@app.route('/customer/shopping_cart', methods=['GET', 'POST'])
def customer_shopping_cart():

    username = session.get('username')

    categorys=category()

    if not username:
        return redirect('/login/')
    
    connection = getCursor()
    # Fetch the customer_id based on the username
    connection.execute('select customer_id from customer where username=%s',(username,))
    customer_id = connection.fetchone()[0]

    if request.method =='GET':
        # Fetch shopping cart details for the customer
        connection = getCursor()
        connection.execute("""select s.*,e.name,e.image,e.store_id, st.store_name,st.store_id from shoppingcart as s join store_equipment as e on s.equipment_id = e.equipment_id
                            JOIN store AS st ON e.store_id = st.store_id 
                            where customer_id =%s""",(customer_id,))
        cart_details = connection.fetchall()

        store_id =[]

        shoppingcart = []
        total_cost = 0

        # Iterate through cart_details to calculate total cost and transform date formats
        for each in cart_details:
            cart = list(each)
            date_str1 = cart[3]
            date_str2 = cart[4]
            store_id.append(each[-1])

            transform_start = time_change(cart[3])
            transform_end = time_change(cart[4])

            days_difference = (date_str2 - date_str1).days
            total_amount = cart[2] * cart[5] * days_difference
            cart.append(total_amount)
            cart.append(transform_start)
            cart.append(transform_end)
            total_cost += total_amount
            shoppingcart.append(cart)

        print(shoppingcart)
        store_id = set(store_id)

        ready = 1
        if len(store_id) >1 :
            ready= 0

        return render_template('/customer/shopping_cart.html', cart_details=shoppingcart, total_cost=total_cost,ready=ready,categorys=categorys)

    elif request.method=='POST':

        # Get form data from the POST request
        equipment_id = request.form.get('equipment_id')
        store_id = request.form.get('store_id')
        name = request.form.get('equipment_name')
        price = request.form.get('price')
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        quantity = request.form.get('quantity')

        # Convert start_date and end_date to datetime objects
        start_date= datetime.strptime(start_date,"%d-%m-%Y")
        end_date= datetime.strptime(end_date,"%d-%m-%Y")

        # Insert the item into the shopping cart
        sql = """Insert into shoppingcart(customer_id,equipment_id,hire_cost,start_date,end_date,quantity)
                  values (%s,%s,%s,%s,%s,%s)"""
        connection = getCursor()
        connection.execute(sql,(customer_id,equipment_id,price,start_date,end_date,quantity))

        return redirect('/customer/shopping_cart')

@app.route('/customer/shopping_cart_delete', methods=['GET', 'POST'])
def shopping_cart_delete():

    username = session.get('username')

    if not username:
        return redirect('/login/')
    
    # Fetch the customer_id based on the username
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s',(username,))
    
    customer_id = connection.fetchone()[0]
    # Get the equipment_id from the request arguments
    equipment_id = request.args.get('equipment_id')


    # Delete the item from the shopping cart
    connection = getCursor()
    connection.execute(
        """Delete from shoppingcart where customer_id=%s and equipment_id = %s""",
        (customer_id,equipment_id,))
    
    return redirect('/customer/shopping_cart')


@app.route('/customer/payment', methods=['POST'])
def customer_payment():

    categorys=category()

    # Get form data from the POST request
    customer_id = request.form.get('customer_id')
    total_cost = request.form.get('total_cost')
    store_id = request.form.get('store_id')

    equipment_id = request.form.getlist('equipment_id')
    price = request.form.getlist('price')
    start_date = request.form.getlist('start_date')
    end_date = request.form.getlist('end_date')
    quantity = request.form.getlist('quantity')
    total = request.form.getlist('total')

    booking_date = datetime.now().date()

    # Combine the data into a list of tuples
    combined_data = list(zip(equipment_id, start_date, end_date, total,quantity))
  
    connection = getCursor()

    # Delete items from the shopping cart for the customer
    connection.execute(
        """Delete from shoppingcart where customer_id=%s""",
        (customer_id,))
    
    # Insert a new booking entry into the database
    connection.execute(
        """insert into booking (customer_id, store_id, total_amount, booking_date) VALUES (%s, %s, %s, %s)""",
        (customer_id, store_id, total_cost, booking_date,))

    # Fetch the last inserted booking_id
    connection.execute("SELECT LAST_INSERT_ID();")
    booking_id = connection.fetchone()[0] 

    # Insert booking details and in_out_record for each item in combined_data
    for data in combined_data:
        connection.execute(
        """insert into booking_detail (booking_id, equipment_id, start_date, end_date,total,quantity) VALUES (%s, %s, %s, %s,%s,%s)""",
        (booking_id, *data))
           
        last_detail_id = connection.lastrowid
    
        connection.execute("""Insert Into in_out_record(detail_id,pickup_time,return_time) 
                    values(%s,%s,%s)""",(last_detail_id,None,None))

    connection.close()

    return render_template('/customer/payment.html',total_cost=total_cost,booking_id=booking_id,categorys=categorys)


@app.route('/customer/payment_successful', methods=['POST'])
def customer_payment_successful():

    categorys=category()

    # Get form data from the POST request
    booking_id = request.form.get('booking_id')
    total_amount = request.form.get('total_cost')
    booking_date = datetime.now().date()

    # Insert payment information into the database
    connection = getCursor()
    connection.execute(
        """insert into payment (booking_id, amount, payment_date, status) VALUES (%s, %s, %s, %s)""",
        (booking_id, total_amount, booking_date, 'successful',))

    # Update booking status to 'paid' in the database
    order_number = int(booking_id)
    connection.execute("""UPDATE booking set status = %s where booking_id = %s""",('paid',booking_id,))
    
    return render_template("/customer/payment_successful.html",order_number=order_number,categorys=categorys)


@app.route('/customer/booking')
def customer_booking():

    username = session.get('username')
    categorys=category()

    if not username:
        return redirect('/login/')

    # Fetch the customer_id based on the username
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s',(username,))
    customer_id = connection.fetchone()[0]

    # Query to fetch booking information for the customer
    connection.execute("""
                       With right_id as (select booking_id, count(booking_id) as num, sum(end_date >= curdate()) as end_num 
                       ,sum(start_date<=curdate()) as no_cancell
                       from booking_detail group by booking_id having end_num >0)
                
                       select b.booking_id,s.store_name,b.total_amount,b.booking_date,b.status,r.no_cancell from booking as b
                       join store as s on b.store_id = s.store_id 
                       join right_id as r on b.booking_id = r.booking_id
                       where b.customer_id = %s """,(customer_id,))
    bookingold = connection.fetchall()

    # Process the fetched booking data
    bookings = []
    for each in bookingold:
        each = list(each)
        each[3] = time_change(each[3])
        bookings.append(each)

    return render_template('/customer/booking_current.html',bookings=bookings,categorys=categorys)


@app.route('/customer/prior_records')
def customer_prior_records():

    username = session.get('username')
    categorys=category()

    if not username:
        return redirect('/login/')

    # Fetch the customer_id based on the username
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s',(username,))
    customer_id = connection.fetchone()[0]

    # Query to fetch past booking records for the customer
    connection.execute("""
                       With right_id as (select booking_id, count(booking_id) as num, sum(end_date<curdate()) as end_num 
                       from booking_detail group by booking_id having num = end_num)
                
                       select b.booking_id,s.store_name,b.total_amount,b.booking_date,b.status from booking as b
                       join store as s on b.store_id = s.store_id
                       where b.customer_id = %s and b.booking_id in (select booking_id from right_id) """,(customer_id,))
    
    bookingold = connection.fetchall()

    # Process the fetched booking data
    bookings = []
    for each in bookingold:
        each = list(each)
        each[3] = time_change(each[3])
        bookings.append(each)

    return render_template('/customer/booking_prior.html',bookings=bookings,categorys=categorys)


@app.route('/customer/booking_details')
def customer_booking_details():

    booking_id = request.args.get('id')
    condition = request.args.get('condition')
    categorys=category()

    # Query to fetch booking details based on booking_id
    connection = getCursor()
    connection.execute("""select s.name,s.image,b.start_date,b.end_date,b.total,b.quantity,b.equipment_id from booking_detail as b
                       join store_equipment as s on b.equipment_id = s.equipment_id where b.booking_id = %s """,(booking_id,))
    booking_detail = connection.fetchall()

    today = datetime.now().date()

    return render_template('/customer/booking_details.html',booking_details=booking_detail,categorys=categorys,today=today)



@app.route('/customer/booking_cancel')
def customer_booking_cancel():

    booking_id = request.args.get('booking_id')

    cancel_date = datetime.now().date()

    # Update the booking status to 'cancelled' in the database
    connection = getCursor()
    connection.execute("""Update booking set status = 'cancelled' where booking_id = %s""",(booking_id,))

    # Fetch the total amount of the booking
    connection.execute("""select total_amount from booking where booking_id =%s""",(booking_id,))
    amount = connection.fetchone()[0]

    # Insert a payment record for the cancellation (refund)
    connection.execute("""Insert into payment (booking_id,amount,payment_date,status) values (%s,%s,%s,%s)""",
                       (booking_id,amount,cancel_date,'refund'))

    return redirect('/customer/booking')


@app.route('/customer/booking_extend',methods=['POST'])
def customer_booking_extend():

    username = session.get('username')
    categorys=category()

    # Fetch the customer_id based on the username
    connection = getCursor()
    connection.execute('select customer_id from customer where username =%s',(username,))
    customer_id = connection.fetchone()[0]

    # Retrieve form data for equipment_id, quantity, and end_date
    equipment_id = request.form.get("equipment_id")
    quantity = request.form.get("quantity")
    end_date = request.form.get("end_date")
    quantity = int(quantity)

    # Query to fetch equipment details and store details for extension
    connection.execute("""select name,image,hire_cost,min_hire_period,max_hire_period,s.store_id,s.store_name 
                       from store_equipment as e join store as s on e.store_id = s.store_id where equipment_id = %s""",(equipment_id,))
    extend = connection.fetchone()

    # Add quantity, end_date, and equipment_id to the extend list
    extend = list(extend)
    extend.append(quantity)
    extend.append(end_date)
    extend.append(equipment_id)

    # Query to fetch booked dates for the equipment
    connection.execute("""select equipment_id,start_date,end_date,quantity from booking_detail as d 
                       join booking as b on d.booking_id = b.booking_id
                       where equipment_id =%s and end_date > curdate() and b.status ='paid'""",(equipment_id,))
    booked_dates = connection.fetchall()

    return render_template('/customer/booking_extend.html',categorys=categorys,extend=extend,customer_id=customer_id,booked_dates=booked_dates)


@app.route('/customer/hiring_record', methods=['GET', 'POST'])
def customer_hiring_record():
    username = session.get('username')

    if not username:
        return redirect('/login/')
    
    search_query = request.args.get('search', '')

    connection = getCursor()
    try:

        # Retrieve customer_id based on the username       
        connection.execute('SELECT customer_id FROM customer WHERE username=%s', (username,))
        customer_id_result = connection.fetchone()
        
        if not customer_id_result:
            return redirect('/login/')
        
        customer_id = customer_id_result[0]
        # Define the SQL query to fetch hiring records
        query = """
            SELECT e.name, e.image, b.quantity, b.start_date, b.end_date, 
            DATEDIFF(b.end_date,b.start_date) AS days
            FROM booking_detail b 
            JOIN payment p ON b.booking_id = p.booking_id
            JOIN store_equipment e ON b.equipment_id = e.equipment_id
            JOIN booking k ON b.booking_id = k.booking_id 
            WHERE p.status = 'successful' 
            AND k.customer_id = %s 
            AND e.name LIKE %s 
  
            ORDER BY b.start_date ASC
        """

        # Execute the query with customer_id and search_pattern
        search_pattern = f"%{search_query}%"
        connection.execute(query, (customer_id, search_pattern))
        hiring_record = connection.fetchall()

    except Exception as e:
        print(f"Error occurred: {e}")
        hiring_record = []
    finally:
        connection.close()

    categorys=category()

    return render_template('/customer/hiring_record.html', hiring_record=hiring_record,categorys=categorys)


@app.route('/customer/notification', methods=['GET', 'POST'])
def customer_notification():
    username = session.get('username')

    categorys=category()

    if not username:
        return redirect('/login/')
    
    connection = getCursor()
    try:

        # Retrieve customer_id based on the username
        connection.execute('SELECT customer_id FROM customer WHERE username=%s', (username,))
        customer_id = connection.fetchone()[0]

        # Define SQL query to fetch notification data for pick-up and return events
        connection.execute("""SELECT method, store, equipment,quantity,date From(
                              SELECT 'pick up' as method, s.store_name as store, e.name as equipment, b.quantity, b.start_date as date
                              FROM booking_detail b JOIN payment p ON b.booking_id=p.booking_id
                              JOIN store_equipment e ON b.equipment_id=e.equipment_id
                              JOIN booking k ON b.booking_id=k.booking_id
                              JOIN store s ON k.store_id=s.store_id
                              WHERE p.status='successful' AND k.customer_id= %s
                              UNION ALL
                              SELECT 'return' as method, s.store_name as store, e.name as equipment, b.quantity, b.end_date as date
                              FROM booking_detail b JOIN payment p ON b.booking_id=p.booking_id
                              JOIN store_equipment e ON b.equipment_id=e.equipment_id
                              JOIN booking k ON b.booking_id=k.booking_id
                              JOIN store s ON k.store_id=s.store_id
                              WHERE p.status='successful' AND k.customer_id= %s)CTE ORDER BY date desc, method""", (customer_id, customer_id))
        
        # Fetch all notifications 
        notification = connection.fetchall()
        
    finally:
        connection.close()

    return render_template('./customer/notification.html', notification=notification,categorys=categorys)


@app.route('/customer/receipt', methods=['GET', 'POST'])
def customer_receipt():
    username = session.get('username')
    categorys=category()

    if not username:
       return redirect('/login/')
    
    connection = getCursor()
    try:

        # Retrieve customer_id based on the username
        connection.execute('SELECT customer_id FROM customer WHERE username=%s', (username,))
        customer_id = connection.fetchone()[0]

        # Define SQL query to fetch receipt information for successful payments
        connection.execute("""SELECT p.booking_id as order_number, p.payment_date, p.amount 
                            FROM payment p 
                            JOIN booking b ON p.booking_id=b.booking_id
                            WHERE p.status='successful' AND b.customer_id=%s
                            ORDER BY order_number ASC;""", (customer_id,))
        
        # Fetch all payment receipts
        receipt = connection.fetchall()
    finally:
        connection.close()

    return render_template('/customer/receipt.html', receipt=receipt,categorys=categorys)


@app.route('/customer/receipt/details', methods=['GET', 'POST'])
def customer_receipt_details():
    username = session.get('username')
    categorys=category()

    if not username:
       return redirect('/login/')
    
    booking_id = request.args.get('booking_id')

    connection = getCursor()
    try:

        # Retrieve customer_id based on the username
        connection.execute('SELECT customer_id FROM customer WHERE username=%s', (username,))
        customer_id = connection.fetchone()[0]

        # Fetch detailed receipt information for the specified booking_id
        connection.execute("""SELECT b.booking_id as order_number, payment_date, e.name as equipment, b.quantity, b.total as amount
                              FROM booking_detail b 
                              JOIN payment p ON b.booking_id=p.booking_id
                              JOIN store_equipment e ON b.equipment_id=e.equipment_id
                              JOIN booking k ON b.booking_id=k.booking_id
                              WHERE p.status='successful'
                              AND k.customer_id=%s AND b.booking_id=%s 
                              ORDER BY order_number ASC;""", (customer_id, booking_id))
        receipt_details = connection.fetchall()

        # Fetch the total amount for the specified booking_id from the payment table
        connection.execute('SELECT amount FROM payment WHERE booking_id=%s;', (booking_id,))
        total_amount = connection.fetchone()
        
    finally:
        connection.close()

    return render_template('/customer/receipt_details.html', receipt_details=receipt_details, total_amount=total_amount,categorys=categorys)


@app.route("/customer/promotion", methods=['GET', 'POST'])
def customer_promotion():

    # Execute a SQL query to fetch promotions along with their details
    connection = getCursor()
    connection.execute(
            """select p.promotion_id, p.promotion_name,p.description,p.start_day,p.end_day,p.discount_rate,p.store_id
            from promotion as p join store as s on p.store_id = s.store_id;""")
    promotions = connection.fetchall()

    stores= store()
    categorys=category()
    return render_template('/customer/promotion.html',promotions=promotions,stores=stores,categorys=categorys)


@app.route("/customer/promotion_product", methods=['GET', 'POST'])
def customer_promotion_product():

    store_id = request.args.get('store_id')
    promotion_id = request.args.get('promotion_id')

    categorys=category()

    # Fetch products from the store with the specified store ID
    connection = getCursor()
    connection.execute(
            """select equipment_id,name,image,store_id,hire_cost,category_id from store_equipment where store_id =%s;""",(store_id,))
    products= connection.fetchall()

    # Fetch the discount rate for the specified promotion ID
    connection.execute(
            "select discount_rate from promotion where promotion_id =%s;",(promotion_id,))
    discount= connection.fetchone()[0]

    # Calculate discounted prices for each product
    products_discount = []
    for each in products:
        each = list(each)
        discount_price= int(each[4] * ((100-discount) /100))
        each.append(discount_price)
        products_discount.append(each) 
    
    # Fetch the store name for displaying on the webpage
    connection.execute(
            """select store_name from store where store_id =%s;""",(store_id,))
    store_name= connection.fetchone()[0]

    return render_template('/customer/promotion_product.html',products=products_discount,categorys=categorys,store_name=store_name,promotion_id=promotion_id)

@app.route('/customer/promotion_details', methods=['GET', 'POST'])
def customer_promotion_details():

    categorys=category()

    # Extract store ID, equipment ID, and promotion ID from the request parameters
    store_id = request.args.get('store_id')
    equipment_id = request.args.get('equipment_id')
    promotion_id = request.args.get('promotion_id')

    # SQL query to fetch details of the product including stock, hire cost, etc.
    sql = """SELECT name,specifications,e.image,hire_cost,min_hire_period,max_hire_period,s.stock,c.category_id,c.category_name FROM store_equipment as e 
             left join (SELECT store_id,equipment_id,ifnull(count(serial_number),0) as stock FROM inventory where status ='available'
             group by store_id, equipment_id) as s on e.store_id= s.store_id and e.equipment_id = s.equipment_id
             inner join category as c on e.category_id = c.category_id where e.store_id =%s and e.equipment_id =%s;"""

    connection = getCursor()
    connection.execute(sql,(store_id,equipment_id))
    details = connection.fetchone()
    
    # Fetch the discount rate for the specified promotion ID
    connection.execute("""select discount_rate from promotion where promotion_id =%s""",(promotion_id,))
    discount = connection.fetchone()[0]

    # Apply the discount to the hire cost of the product
    details = list(details)
    details[3] = int(details[3] * ((100-discount) /100))

    # Fetch booked dates for the product to display on the webpage
    connection.execute("""select equipment_id,start_date,end_date,quantity from booking_detail where equipment_id =%s and end_date > curdate()""",(equipment_id,))
    booked_dates = connection.fetchall()

    return render_template('/customer/product_details.html',details = details,equipment_id=equipment_id,store_id=store_id,categorys=categorys,booked_dates=booked_dates)


@app.route("/customer/news", methods=['GET', 'POST'])
def customer_news():

    # Establish a database connection and execute SQL query to fetch news data
    connection = getCursor()
    connection.execute(
            """select n.title,n.content,n.create_time,s.store_name 
            from news as n join store as s on n.store_id = s.store_id
            order by n.news_id desc;""")
    news = connection.fetchall()
    categorys=category()
    return render_template('/customer/news.html',news=news,categorys=categorys)


UPLOAD_FOLDER = os.path.join('static', 'identifications')

@app.route('/customer/identification', methods=['GET', 'POST'])
def customer_identification():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    cursor = getCursor()

    if request.method == 'POST':

        # Handle POST request to update identification image
        image = request.files.get('image')
        if image and image.filename != '':
            image_filename = secure_filename(image.filename)
            # Ensure the directory exists
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            image.save(image_path)
        else:
            image_filename = request.form.get('current_image', '')

        # Update the customer's image in the database
        cursor.execute('UPDATE customer SET image = %s WHERE username = %s', (image_filename, username))
        flash('Identification image updated successfully.', 'success')

    # Fetch customer's first name, last name, and image from the database
    cursor.execute('SELECT first_name, last_name, image FROM customer WHERE username = %s', (username,))
    customer = cursor.fetchone()

    # Check if customer data is found
    if customer:
        name = (customer[0], customer[1])
        image = customer[2]
    else:
        name = ("", "")
        image = ""

    categorys=category()
    return render_template("/customer/identification.html", name=name, customer_image=image,categorys=categorys)


@app.route('/customer/contact', methods=['GET', 'POST'])
def customer_contact():
    username = session.get('username')
    categorys=category()
    if not username:
        return redirect('/login/')

    # Get a cursor to interact with the database
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s', (username,))
    customer_id = connection.fetchone()[0]
    if request.method == "GET":

        # Fetch store list for display in the form
        connection.execute('select store_id,store_name from store')
        store_list = connection.fetchall()
        return render_template('/customer/contact.html', store_list=store_list,categorys=categorys)
    
    else:
        # Handle POST request to submit contact form       
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        msg_subject = request.form['msg_subject']
        message = request.form['message']
        store_id = request.form['store_id']
        create_time = datetime.now()

        # Insert feedback data into the feedback table
        connection.execute(
            "insert into feedback (name,email,phone,subject,create_time,customer_id,store_id) values (%s,%s,%s,%s,%s,%s,%s)",
            (name, email, phone_number, msg_subject, create_time, customer_id, store_id)
        )
        new_id = connection.lastrowid

        # Insert message into feedback_exchange table
        connection.execute(
            "insert into feedback_exchange (sender_id,create_time,feedback_id,content) values (%s,%s,%s,%s)",
            (customer_id, create_time, new_id, message)
        )
        return redirect("/customer/feedback")


@app.route('/customer/feedback', methods=['GET', 'POST'])
def customer_feedback():
    username = session.get('username')
    categorys=category()
    if not username:
        return redirect('/login/')

    # Get a cursor to interact with the database
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s', (username,))
    customer_id = connection.fetchone()[0]

    # Fetch feedback data for the current customer
    connection.execute(
        "select feedback_id,name,email,feedback.phone,subject,create_time,store_name from feedback left join store on store.store_id=feedback.store_id where customer_id=%s order by create_time desc",
        (customer_id,))
    feedbacks = connection.fetchall()

    # Process and format the feedback data for display
    feedbacks_result = []
    for feedback in feedbacks:
        feedback = list(feedback)
        feedback[5] = feedback[5].strftime('%d-%m-%Y %H:%M:%S')
        feedbacks_result.append(feedback)

    return render_template('/customer/feedback.html', feedbacks=feedbacks_result,categorys=categorys)


@app.route('/customer/feedback_detail', methods=['GET', 'POST'])
def feedback_detail():
    username = session.get('username')
    categorys=category()
    if not username:
        return redirect('/login/')

    # Get a cursor to interact with the database
    connection = getCursor()
    connection.execute('select customer_id from customer where username=%s', (username,))
    customer_id = connection.fetchone()[0]
    
    if request.method == "GET":
        reply = 0
        feedback_id = request.args.get('id')

        # Fetch the feedback details
        connection.execute(
            "select name,email,feedback.phone,subject,create_time,store_name from feedback left join store on store.store_id=feedback.store_id  where feedback_id=%s order by create_time desc",
            (feedback_id,))
        feedback = connection.fetchone()

        # Fetch the chat records related to this feedback
        connection.execute("select * from feedback_exchange where feedback_id=%s order by create_time asc",
                           (feedback_id,))
        chat_records = connection.fetchall()

        # Process and format the chat records
        chat_result = []
        for chat_record in chat_records:
            chat_type = "staff"
            username = "Me"
            usertype = ""
            if chat_record[1] == customer_id:
                chat_type = "customer"
            else:
                connection.execute(
                    "select last_name,first_name from staff where username=(select username from account where account_id=%s)",
                    (chat_record[1],))
                username = " ".join(connection.fetchone())
                usertype = "Staff"
            create_time = chat_record[2]
            content = chat_record[3]
            if chat_type == "staff":
                reply += 1
            chat_result.append({
                "chat_type": chat_type,
                "username": username,
                "usertype": usertype,
                "create_time": create_time.strftime('%d-%m-%Y %H:%M:%S'),
                "content": content
            })
        feedback = list(feedback)
        feedback[4] = feedback[4].strftime('%d-%m-%Y %H:%M:%S')
        return render_template('/customer/feedback_detail.html', feedback=feedback, chat_result=chat_result,
                               reply=reply, feedback_id=feedback_id,categorys=categorys)
    else:
        feedback_id = request.form.get('feedback_id')
        content = request.form.get('content', '')

        # Insert the new message into the database
        connection.execute(
            "insert into feedback_exchange (sender_id,create_time,feedback_id,content) values (%s,%s,%s,%s)",
            (customer_id, datetime.now(), feedback_id, content)
        )
        flash("Message send successful")
        return redirect(url_for('feedback_detail', id=feedback_id))


app.config['UPLOAD_FOLDER']='uploads'
@app.route('/customer/report_equipment', methods=['GET','POST'])
def report():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    cursor = getCursor()

    # Fetch store information
    cursor.execute('select /*+parallel(16)*/ store_id,store_name from store;')
    store_info=cursor.fetchall()
    stores = [store[1] for store in store_info]
    
    if request.method == 'POST':

        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        equipment = request.form.get('equipment')
        description = request.form.get('description')
        photo = request.files.get('photo')
        store = request.form.get('store')

        # Save the photo if uploaded
        if photo and photo.filename != '':
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))

        # Insert the report into the database
        cursor.execute('insert into customer_report values (%s,%s,%s,%s,%s);', (name, email, equipment, description, photo.filename))
        flash('report committed successfully.', 'success')
        return redirect(url_for('report'))

    return render_template('customer/report_equipment.html', stores=stores)
	

@app.route('/customer/request_equipment', methods=['GET','POST'])
def request_equipment():
    if 'username' not in session:
        flash('You need to login first', 'danger')
        return redirect(url_for('login'))  # Ensure you have a login route

    username = session.get('username')
    cursor = getCursor()
    
    # Fetch store information
    cursor.execute('select /*+parallel(16)*/ store_id,store_name from store;')
    store_info=cursor.fetchall()
    stores = [store[1] for store in store_info]

    if request.method == 'POST':

        # Get form data
        equipment_id = request.form.get("equipment_id")
        name = request.form.get('name')
        email = request.form.get('email')
        equipment = request.form.get('equipment')
        reason = request.form.get('reason')
        store = request.form.get('store')

        # Insert the request into the database
        cursor.execute('insert into customer_request values (%s,%s,%s,%s,%s,%s);', (equipment_id, name, email, equipment, reason, store))
        flash('request committed successfully.', 'success')
        return redirect(url_for('request_equipment'))

    return render_template('customer/request_equipment.html', stores=stores)
