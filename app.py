from pdb import post_mortem
from flask import Flask, appcontext_popped, render_template, redirect, request, flash, session
from passlib.hash import pbkdf2_sha256
from flask_pymongo import PyMongo
from datetime import datetime
from flask_moment import Moment
import os
app = Flask(__name__)
if os.environ.get("MONGO_URI") ==  None: #on local computer
    file = open("connectionstring.txt", "r")
    app.config["MONGO_URI"] = file.read().strip()
    file.close()
else: #deployed website
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
if os.environ.get("SECRET_KEY") ==  None: #on local computer
    file = open("SECRET_KEY.txt", "r")
    app.config["SECRET_KEY"] = file.read().strip()
    file.close()
else: #deployed website
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
mongo = PyMongo(app)
moment = Moment(app)
def currenttime():
    # datetime object containing current date and time
    now = datetime.now()
    # dd/mm/YY H:M:S
    dt_string = now.strftime("Posted on %B %d, %Y at %H:%M:%S")
    return dt_string


@app.route("/")
def index():
    return render_template("welcome.html")


@app.route("/home/")
def home():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    return render_template("home.html")


@app.route("/registration/", methods = ["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("registration.html")
    else:
        email = request.form["email"]
        name = request.form["firstname"]
        name+= " "
        name+= request.form["lastname"]
        password = request.form["password"]
        confirm = request.form["confirm"]
        description = request.form["description"]
        securepassword = pbkdf2_sha256.hash(password)
        user = mongo.db.social.find_one({"email":email})
        if user is not None:
            flash("Email already exists", 'danger')
            return redirect("/registration/")
        if password != confirm:
            flash("passwords do not match", 'danger')
            return redirect("/registration/")
        document = {"email": email, "password": securepassword, "name": name, "description": description}
        mongo.db.social.insert_one(document)
        session["user"] = email
        flash("Success", "success")
        return redirect("/home/")


@app.route("/login/", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        password = request.form["password"]
        user = mongo.db.social.find_one({"email":email})
        if user == None:
            flash("Invalid email", "danger")
            return redirect("/login/")
        if pbkdf2_sha256.verify(password, user["password"]) == True:
            session["user"] = email
            flash("Login succesful", "success")
            return redirect("/home/")
        else:
            flash("Invalid password", "danger")
            return redirect("/login/")


@app.route("/othersposts/", methods = ["POST", "GET"])
def othersposts():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    if request.method == "GET":
        posts = list(mongo.db.pluggedinposts.find())#{"by": {"$ne": session["user"]}}))
        return render_template("othersposts.html", posts = posts)
    else:
        post = request.form["post"]
        time = datetime.utcnow()
        document = {"by": session["user"], "time": time, "post": post}
        mongo.db.pluggedinposts.insert_one(document)
        return redirect("/othersposts/")



@app.route("/myposts/", methods = ["POST", "GET"])
def myposts():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    if request.method == "GET":
        posts = list(mongo.db.pluggedinposts.find({"by": session["user"]}))
        return render_template("myposts.html", posts = posts)
    else:
        post = request.form["post"]
        time = datetime.utcnow()
        document = {"by": session["user"], "time": time, "post": post}
        mongo.db.pluggedinposts.insert_one(document)
        return redirect("/myposts/")


@app.route("/logout/")
def logout():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    flash("You have been successfully logged out", "success")
    session.pop("user")
    return redirect("/")


@app.route("/account/")
def account():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    return render_template("account.html")


@app.route("/deleteaccount/")
def deleteaccount():
    if "user" not in session:
        flash("Please login", "danger")
        return redirect("/login/")
    mongo.db.social.remove({"email": session["user"]})
    flash("You have been successfully deleted", "success")
    session.pop("user")
    return redirect("/")


app.run(debug = True)