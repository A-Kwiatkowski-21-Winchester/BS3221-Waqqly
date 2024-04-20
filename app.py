import base64
from datetime import datetime
import json
import os
import configparser
from pprint import pprint
import random
import secrets
import urllib
import urllib.parse
import requests

import bson
import bson.json_util
from flask import (
    Flask,
    abort,
    g,
    jsonify,
    redirect,  # Global data context for this request
    render_template,
    request,
    send_from_directory,
    current_app,
)
from flask_pymongo import PyMongo
from jinja2 import TemplateNotFound

with open('app.log', 'w') as f:
    f.write("") # Clear file

def printlog(obj=None, pretty=False):
    if(obj is None):
        obj = ""
    with open('app.log', 'a') as f:
        if(pretty):
            pprint(obj)
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: "), file=f)
            pprint(obj, stream=f)
        print(obj)
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S: "), file=f, end="")
        print(obj, file=f)

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

printlog("Collections:")
printlog(db.list_collection_names())

un_pw_pair = "apidemo:test"  # b64: YXBpZGVtbzp0ZXN0
correct_b64_auth = base64.b64encode(un_pw_pair.encode("utf-8"))


def checkAuthorization(abortOnFail: bool = True):
    printlog(list(request.headers), pretty=True)
    auth_header = request.headers.get("Authorization")
    # If no authorization header in request, or is not of type "basic", abort with 400.
    if (auth_header is None) or (auth_header.split(" ")[0].casefold() != "basic"):
        g.abort_reason = (
            "Authorization header not present or not of correct type 'Basic'"
        )
        if abortOnFail:
            abort(400)
        return False

    request_b64_auth = auth_header.split(" ")[1].encode("utf-8")

    # Using secrets.compare_digest() helps prevent against timing attacks
    if not (secrets.compare_digest(request_b64_auth, correct_b64_auth)):
        g.abort_reason = "Invalid authorization"
        if abortOnFail:
            abort(401)
        return False


def getMaxID():
    # Queries the collection with no filter, reverse sorting by ID, and returning only the ID field
    maxIdItem = (
        db.testcollection.find(projection=["id"]).sort({"id": -1}).limit(1)
    )  # for MAX
    return maxIdItem[0].get("id")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static", "media"), "icon.ico"
    )  # TODO: Ensure that favicon is appropriate size


@app.route("/api/get", methods=["GET"])
def getAPI():
    checkAuthorization()
    accept_headers = request.headers.getlist("Accept")
    printlog(request.method)

    if "application/json" in (ah.casefold() for ah in accept_headers):
        g.acceptJSON = True

    return_string = "<h1>API PAGE REACHED</h1> <p>Welcome user!</p> "
    testcollection = db.get_collection("testcollection")
    filter = request.args.to_dict()
    itemcount = testcollection.count_documents(filter)
    testitems = testcollection.find(filter)  # TODO: Add special query params like LIMIT
    bsonitems = bson.json_util.dumps(testitems, indent=2)
    jsonitems = json.dumps(json.loads(bsonitems), skipkeys=True)
    return_string += f"Items with filter '{filter}': {itemcount}"

    if ("acceptJSON" in g) and (g.acceptJSON is True):
        return jsonify(json.loads(jsonitems))

    return return_string


@app.route("/api/post", methods=["POST"])
def postAPI():
    checkAuthorization()
    printlog("POST REQUEST RECEIVED")

    post_details = request.args.to_dict()
    printlog(post_details)
    user_dict = {"id": ""}

    def transplant(keyString, type):
        if not isinstance(post_details[keyString], type):
            raise TypeError(keyString)
        user_dict[keyString] = post_details.pop(keyString)

    try:
        transplant("type", str)
        transplant("first_name", str)
        transplant("last_name", str)
        transplant("email", str)
        transplant("phone", str)
        transplant("addr_line1", str)
        transplant("addr_city", str)
        transplant("addr_country", str)
        transplant("addr_postal", str)
    except TypeError as ex:
        g.abort_reason = f"Provided field '{ex.args[0]}' is malformed"
        abort(400)
    except KeyError as ex:
        g.abort_reason = f"Required field '{ex.args[0]}' has not been provided"
        abort(400)

    user_dict["notes"] = post_details.pop("notes", "")  # Optional, with blank default

    if len(post_details) > 0:
        remaining_keys = list(post_details.keys())
        g.abort_reason = f"Provided field '{remaining_keys[0]}' is not supported"
        abort(400)

    user_dict["id"] = getMaxID() + 1
    printlog(user_dict, pretty=True)
    # printlog(urllib.parse.urlencode(user_dict)) # Convert into query

    db.testcollection.insert_one(user_dict)

    return "Successful", 201


@app.route("/register")
def register():
    reg_details = request.args.to_dict()
    if not reg_details:
        return render_template("/register/register.html")

    printlog("\nNew Registration:")
    printlog(reg_details, pretty=True)

    querystring = urllib.parse.urlencode(reg_details)
    postURL = f"http://{request.host}/api/post?{querystring}" 
    printlog(f"Attempting to connect to {postURL}")
    response = requests.post(
        postURL,
        headers={
            "Accept": "application/json",
            "Authorization": "Basic " + correct_b64_auth.decode("utf-8"),
        },
        timeout=15,
    )
    printlog(f"Responded with {response.status_code}: {response._content}")
    if response.status_code != 201:
        g.abort_reason = f"Something went wrong during registration. Server said: '{response._content}'"
        abort(400)

    return redirect(f"/register/complete?first_name={reg_details.get('first_name')}")


@app.route("/register/complete")
def register_complete():
    printlog(request.args.to_dict(), pretty=True)
    fname = request.args.get("first_name") or "kind stranger"
    return render_template("register/complete.html", name=fname)


@app.route("/")
def index():
    printlog("\nNew Request:")
    testcollection = db.get_collection("testcollection")
    filter = {"type": {"$regex": "walk.*"}}
    itemcount = testcollection.count_documents(filter)
    printlog(
        f"Number of items in '{testcollection.name}' using filter {filter}: {itemcount}"
    )

    # Method 1 for getting random item:
    testitems = testcollection.find(filter)
    randitem = testitems[random.randint(0, itemcount - 1)]
    printlog()
    printlog("Selected random item (m1):")
    printlog(randitem, pretty=True)
    printlog()

    printlog("Request for index page received")
    return render_template("index.html", testitem=randitem)


@app.route("/<variable>")
def allpages(variable):
    try:
        return render_template(f"{variable}.html")
    except TemplateNotFound:
        abort(404)


@app.errorhandler(400)
def handle_400(ex):
    error_string = "400 - Bad Request"
    if "abort_reason" in g:
        error_string += f" :: {g.abort_reason}"
    printlog(error_string)
    return error_string, 400


@app.errorhandler(401)
def handle_401(ex):
    error_string = "401 - Unauthorized"
    if "abort_reason" in g:
        error_string += f" :: {g.abort_reason}"
    else:
        error_string += " :: The server could not verify that you are authorized to access the URL requested."

    printlog(error_string)
    return error_string, 401


@app.errorhandler(404)
def handle_404(ex):
    error_string = "404 - Page Not Found"
    if "abort_reason" in g:
        error_string += f" :: {g.abort_reason}"

    printlog(error_string)
    return error_string, 404
