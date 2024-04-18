import os
import configparser
from pprint import pprint
import random

from flask import (
    Flask,
    g,  # Global data context for this request
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    current_app,
)
from flask_pymongo import PyMongo
from werkzeug.local import LocalProxy

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(".ini")))

app = Flask(__name__)

app.config["DEBUG"] = True
app.config["MONGO_URI"] = config["TEST"]["DB_URI"]

mongo = PyMongo(app)

db = None
capp = current_app

with app.app_context():
    db = g._database = mongo.db
    # db = LocalProxy(db) # Seem in other examples of code but unsure to purpose

if db is None:
    raise Exception("Unable to connect to database.")

print("Collections:")
print(db.list_collection_names())


@app.route("/favicon.ico")
def favicon():
    return send_from_directory( os.path.join(app.root_path, "static", "media"), "icon.ico" ) #TODO: Ensure that favicon is appropriate size


@app.route("/")
def index():
    print("\nNew Request:")
    testcollection = db.get_collection("testcollection")
    filter = {"profession":"walker"}
    itemcount = testcollection.count_documents(filter)
    testitems = testcollection.find(filter)
    print(f"Number of items in '{testcollection.name}' using filter {filter}: {itemcount}")
    randitem = testitems[random.randint(0, itemcount-1)]
    print()
    print("Selected random item:")
    pprint(randitem)
    print()

    print("Request for index page received")
    return render_template("index.html", testitem=randitem)

# TODO: Create route for "/API"