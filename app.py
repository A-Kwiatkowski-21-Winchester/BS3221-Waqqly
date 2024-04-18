import base64
import os
import configparser
from pprint import pprint
import random
import secrets
import textwrap
from typing import Union

from flask import (
    Flask,
    Response,
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
# @app.route("/api", methods=['GET', 'POST'])
@app.route("/api")
def readAPI():
    accept_headers = request.headers.getlist("ACCEPT")
    auth_header=request.headers.get("Authorization")

    # If no authorization header in request, or is not of type "basic", abort with 400.
    if ((auth_header is None) or (auth_header.split(" ")[0].casefold() != "basic")):
        abort(400)

    un_pw_pair = "apidemo:test" #b64: YXBpZGVtbzp0ZXN0
    correct_b64_auth = base64.b64encode(un_pw_pair.encode("utf-8")) 
    request_b64_auth = auth_header.split(" ")[1].encode("utf-8")
    if not (secrets.compare_digest(request_b64_auth, correct_b64_auth)):
        abort(401)

    return_string = "<h1>API PAGE REACHED</h1> <p>Welcome user!</p> "
    pprint(request.args.to_dict())
    testcollection = db.get_collection("testcollection")
    filter = request.args.to_dict()
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


@app.errorhandler(400)
def handle_400(ex):
    return "400 - Bad Request. Are your headers correct?", 400

@app.errorhandler(404)
def handle_404(ex):
    return "404 - Page Not Found", 404
