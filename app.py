import os

from flask import ( # type: ignore
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

app = Flask(__name__)


@app.route("/")
def index():
    print("Request for index page received")
    return render_template("index.html")
