import os
import configparser

from flask import (
    Flask,
    g, # Global data context for this request
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    current_app
)
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['MONGO_URI'] = config['TEST']['DB_URI']

mongo = PyMongo(app)

db = None
capp = current_app

with app.app_context():
    db = g._database = mongo.db
    #db = LocalProxy(db)

if db is None:
    raise Exception("Unable to connect to database.")

print("Collections:")
print(db.list_collection_names())

@app.route("/")
def index():

    testcollection = db.get_collection("testcollection")
    testitem = testcollection.find_one({"profession":"walker"})
    print(testitem)

    print("Request for index page received")
    return render_template("index.html", testitem = testitem)
