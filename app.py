import base64
import json
import os
import configparser
from pprint import pprint
import random
import secrets

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


# @app.route("/api", methods=['GET', 'POST'])
@app.route("/api") # TODO: SEPARATE INTO *GET* AND *POST*
def readAPI():
    accept_headers = request.headers.getlist("Accept")
    auth_header = request.headers.get("Authorization")

    pprint(accept_headers)

    if "application/json" in (ah.casefold() for ah in accept_headers):
        g.acceptJSON = True

    # If no authorization header in request, or is not of type "basic", abort with 400.
    if (auth_header is None) or (auth_header.split(" ")[0].casefold() != "basic"):
        g.abort_reason = (
            "Authorization header not present or not of correct type 'Basic'"
        )
        abort(400)

    un_pw_pair = "apidemo:test"  # b64: YXBpZGVtbzp0ZXN0
    correct_b64_auth = base64.b64encode(un_pw_pair.encode("utf-8"))
    request_b64_auth = auth_header.split(" ")[1].encode("utf-8")

    # Using secrets.compare_digest() helps prevent against timing attacks
    if not (secrets.compare_digest(request_b64_auth, correct_b64_auth)):
        g.abort_reason = "Invalid authorization"
        abort(401)

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



@app.route("/register")
def register():
    reg_details = request.args.to_dict()
    if not reg_details:
        return render_template("/register/register.html")
    
    print("\nNew Registration:")
    pprint(reg_details)

    return redirect(f"/register/complete?first_name={reg_details['first_name']}")


@app.route("/register/complete")
def register_complete():
    pprint(request.args.to_dict())
    fname = request.args.get("first_name") or "kind stranger"
    return render_template("register/complete.html", name=fname)


@app.route("/")
def index():
    print("\nNew Request:")
    testcollection = db.get_collection("testcollection")
    filter = {"type": {"$regex": "walk.*"}}
    itemcount = testcollection.count_documents(filter)
    print(
        f"Number of items in '{testcollection.name}' using filter {filter}: {itemcount}"
    )

    # Method 1 for getting random item:
    testitems = testcollection.find(filter)
    randitem = testitems[random.randint(0, itemcount - 1)]
    print()
    print("Selected random item (m1):")
    pprint(randitem)
    print()

    print("Request for index page received")
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
    return error_string, 400


@app.errorhandler(401)
def handle_401(ex):
    error_string = "401 - Unauthorized"
    if "abort_reason" in g:
        error_string += f" :: {g.abort_reason}"
    else:
        error_string += " :: The server could not verify that you are authorized to access the URL requested."

    return error_string, 401


@app.errorhandler(404)
def handle_404(ex):
    error_string = "404 - Page Not Found"
    if "abort_reason" in g:
        error_string += f" :: {g.abort_reason}"
    return error_string, 404
