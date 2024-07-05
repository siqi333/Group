
from flask import Flask

app = Flask(__name__,template_folder='../templates',static_folder='../static')



from app import home
from app import authentication
from app import local_view
from app import staff_view
from app import customer_view
from app import national_view
from app import admin_view

