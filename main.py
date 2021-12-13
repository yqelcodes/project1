import os
import re
import requests
from flask import Flask, session, render_template, request, abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

error = {}


def sanitize(input):
    result = input.replace("'", "")
    result = result.replace('"', '')
    result = re.sub(" +", " ", result)
    return result.strip()


@app.route("/")
def index():
    if session.get("userid") is None:
        session["userid"] = 0
        return render_template("login.html", session=session)
    elif session["userid"] == 0:
        return render_template("login.html", session=session)
    else:
        return render_template("store.html", session=session)


@app.route("/newuser", methods=["POST", "GET"])
def newuser():
    if request.method == "GET":
        return render_template("newuser.html")
    if request.method == "POST":
        username = sanitize(request.form.get("username"))
        password = sanitize(request.form.get("password"))
        if username == "" or password == "":
            error["header"] = "Empty field"
            error["message"] = "Both username and password should be meaningful"
            return render_template("error.html", error=error)
        if db.execute("select id from users where name = :username", {"username": username}).rowcount > 0:
            error["header"] = "User already exist"
            error["message"] = "Pick another name, because the one you have choosen is already taken"
            return render_template("error.html", error=error)
        else:
            db.execute("insert into users (name, password) values (:username, crypt(:password, gen_salt('bf')))",
                       {"username": username, "password": password})
            db.commit()
            return render_template("login.html")


@app.route("/logout", methods=["GET"])
def logout():
    if session["userid"] != 0:
        session["userid"] = 0
    return render_template("login.html", session=session)


