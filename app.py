import os
import configparser
from pprint import pprint
import random
import textwrap
from typing import Union

from flask import (
    Flask,
    abort,
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
    return send_from_directory(
        os.path.join(app.root_path, "static", "media"), "icon.ico"
    )  # TODO: Ensure that favicon is appropriate size


# TODO: Create route for "/API"
@app.route("/api", methods=['GET', 'POST'])
def readAPI():
    username = request.args.get("username")
    password = request.args.get("password")
    if not (username == "mike" and password == "bogus"):
        abort(403)
    return_string = "<h1>API PAGE REACHED</h1>\n" f"Welcome {username}!\n"
    pprint(
        request.args.to_dict()
    )  # TODO: Consider passing this directly into the filter for <collection>.find()
    testcollection = db.get_collection("testcollection")
    filter = request.args.to_dict()
    filter.pop("username")
    filter.pop("password")
    itemcount = testcollection.count_documents(filter)
    testitems = testcollection.find(filter)
    return_string += f"Items with filter '{filter}': {itemcount}"

    return return_string


@app.route("/")
def index():
    print("\nNew Request:")
    testcollection = db.get_collection("testcollection")
    filter = {"profession": "walker"}
    itemcount = testcollection.count_documents(filter)
    testitems = testcollection.find(filter)
    print(
        f"Number of items in '{testcollection.name}' using filter {filter}: {itemcount}"
    )
    randitem = testitems[random.randint(0, itemcount - 1)]
    print()
    print("Selected random item:")
    pprint(randitem)
    print()

    print("Request for index page received")
    return render_template("index.html", testitem=randitem)


@app.errorhandler(404)
def handle_fourohfour(ex):
    return "404 - Page Not Found"
