import time
import os
import json
from app import app

from flask import render_template, redirect, make_response

import mysql.connector
import connect
from flask import request
from flask import Flask, request, flash, session, redirect, url_for, render_template
from datetime import datetime, timedelta
import re
import mysql.connector
import connect
import os

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

def store():
    connection = getCursor()
    connection.execute(
            "select store_id,store_name from store;")
    stores = connection.fetchall()  
    return stores


def category():
    connection = getCursor()
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()  
    return categorys


@app.route("/")
def main():

    connection = getCursor()
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()

    return render_template('./basic/home.html',categorys=categorys)



@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))



@app.route("/upload", methods=['GET', 'POST'])
def upload():

    # Handle file upload request
    for _, storage in request.files.items():
        file_data = storage.read()
        file_path = str(int(time.time())) + storage.filename
        save_path = os.path.join(os.path.abspath('static'), 'images','profile', file_path)
        with open(save_path, 'wb') as w:
            w.write(file_data)

        return make_response((
            json.dumps({"status": 10000, "file_path": file_path}),
            200,
            {'Content-Type': 'application/json; charset=utf-8'}
        ))

@app.route("/upload_product", methods=['GET', 'POST'])
def upload_product():
    # Handle file upload request
    for _, storage in request.files.items():
        file_data = storage.read()
        file_path = str(int(time.time())) + storage.filename
        save_path = os.path.join(os.path.abspath('static'), 'images','products', file_path)
        with open(save_path, 'wb') as w:
            w.write(file_data)

        return make_response((
            json.dumps({"status": 10000, "file_path": file_path}),
            200,
            {'Content-Type': 'application/json; charset=utf-8'}
        ))


@app.route("/product", methods=['GET', 'POST'])
def prodcut():

    # Establish a database connection and get a cursor
    connection = getCursor()

    # Execute a query to fetch all categories
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()

    stores = store()

    category_id = request.args.get('category')

    # Execute a query to fetch products based on the category_id
    connection = getCursor()
    connection.execute(
            "select equipment_id,name,image,store_id,hire_cost from store_equipment where category_id =%s;",(category_id,))
    products= connection.fetchall()

    connection.execute(
            "select category_name from category where category_id =%s;",(category_id,))
    category_name= connection.fetchone()[0]

    return render_template('/basic/product.html',products=products,category_name=category_name,categorys=categorys,stores=stores)


@app.route("/product/details", methods=['GET', 'POST'])
def prodcut_details():

    connection = getCursor()
    # Execute a query to fetch all categories
    connection.execute(
            "select * from category;")
    categorys = connection.fetchall()

    # Get the 'id' and 'equipment_id' parameters from the request arguments
    id = request.args.get('id')
    equipment_id =request.args.get('equipment_id')
 
    # Define the SQL query to fetch detailed information about the product
    sql = """SELECT name,specifications,e.image,hire_cost,min_hire_period,max_hire_period,s.stock,c.category_id,c.category_name FROM store_equipment as e 
             left join (SELECT store_id,equipment_id,ifnull(count(serial_number),0) as stock FROM inventory where status ='available'
             group by store_id, equipment_id) as s on e.store_id= s.store_id and e.equipment_id = s.equipment_id
             inner join category as c on e.category_id = c.category_id where e.store_id =%s and e.equipment_id =%s;"""

    connection.execute(sql,(id,equipment_id))
    details = connection.fetchone()

    return render_template('/basic/product_details.html',details=details,categorys=categorys)


@app.route("/promotion", methods=['GET', 'POST'])
def promotion():

    connection = getCursor()

    # Execute a query to fetch all promotions with their details and associated stores
    connection.execute(
            """select p.promotion_id, p.promotion_name,p.description,p.start_day,p.end_day,p.discount_rate,p.store_id
            from promotion as p join store as s on p.store_id = s.store_id;""")
    promotions = connection.fetchall()

    stores= store()
    categorys=category()
    return render_template('/basic/promotion.html',promotions=promotions,stores=stores,categorys=categorys)


@app.route("/store_location", methods=['GET', 'POST'])
def store_location():
    connection = getCursor()

    # Execute a query to fetch store information including store name, address, phone, and city
    connection.execute("SELECT store_name, address, phone, city FROM store;")
    stores = connection.fetchall()

    # Transform the fetched data into a list of dictionaries for easier processing in the template
    stores = [{'store_name': store[0], 'address': store[1], 'phone': store[2], 'city': store[3]} for store in stores]

    categorys= category()

    return render_template('/basic/store_location.html', stores=stores,categorys=categorys)


@app.route("/store_contact", methods=['GET', 'POST'])
def store_contact():
    
    # Get the city from the form data
    city = request.form.get('city')

    # Initialize an empty dictionary to store store details
    store_details = {}
    connection = getCursor()
    
    # Execute a query to fetch store details based on the specified city
    connection.execute("SELECT store_name, address, phone FROM store WHERE city = %s;", (city,))
    store = connection.fetchall()
    
    categorys= category()

    # Check if a store was found for the specified city
    if store:
        store = store[0]
        store_details = {'store_name': store[0], 'address': store[1], 'phone': store[2], 'city': city}
    
    return render_template('/basic/store_contact.html', store=store_details,categorys=categorys)


@app.route("/news", methods=['GET', 'POST'])
def news():

    connection = getCursor()

    # Execute a query to fetch news articles along with their associated store names
    connection.execute(
            """select n.title,n.content,n.create_time,s.store_name 
            from news as n join store as s on n.store_id = s.store_id
            order by n.news_id desc;""")
    news = connection.fetchall()

    categorys=category()
    return render_template('/basic/news.html',news=news,categorys=categorys)


@app.route("/about_us", methods=['GET', 'POST'])
def about_us():

    categorys=category()
    
    return render_template('/basic/about.html',categorys=categorys)
