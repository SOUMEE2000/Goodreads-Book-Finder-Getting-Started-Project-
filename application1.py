import requests
import json

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("URL for database")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
  if request.method=="POST":
    fname= request.form.get("fname")
    lname= request.form.get("lname")
    email= request.form.get("email")
    password= request.form.get("password")
    username= request.form.get("username")

    if db.execute("SELECT username, password, email FROM users WHERE username= :username AND password= :password AND email =:email ",
                 {"username":username, "password":password, "email":email}).rowcount!= 0:
                  return render_template("register.html", message= "The email/ password /username is already registered under an user")

    db.execute("INSERT INTO users(username, first_name, last_name, email, password) VALUES(:username,:fname, :lname, :email, :password)",
                   {"username":username, "fname":fname, "lname":lname, "email":email, "password":password})
    db.commit()
    return render_template("login.html")

  else:
    return render_template("login.html")

@app.route("/home", methods=["POST","GET"])
def home():

  if request.method=="POST":
    username= request.form.get("username")
    session["username"]= username
    session["logged_in"]=True
    password= request.form.get("password")

    if db.execute("SELECT username, password FROM users WHERE username= :username AND password= :password ",
                  {"username":username, "password":password}).rowcount== 0:
         return render_template("login.html", message="Invalid username or password")

    return render_template("search.html",  username= session["username"])

  else:
       return render_template("search.html", username=session["username"])

@app.route("/home/results", methods=["POST"])
def results():
    isbn= request.form.get("isbn")
    author= request.form.get("author")
    title= request.form.get("title")
    sq11= "SELECT * FROM books"
    sq12= ""

    if isbn!="":
        sq12=sq12 + " WHERE isbn LIKE '%" + isbn + "%'"

    if author!="" and sq12=="" :
        sq12=sq12 + " WHERE author LIKE '%" + author + "%'"

    if author!="" and sq12!="" :
        sq12=sq12 + " AND author LIKE '%" + author + "%'"

    if title!="" and sq12=="" :
        sq12=sq12 + " WHERE title LIKE  '%" + title + "%'"

    if title!="" and sq12!="" :
        sq12=sq12 + " AND title LIKE '%" + title + "%'"
    sq11=sq11+sq12

    if sq12 != "" and db.execute(sq11).rowcount!=0:
        book_s= db.execute(sq11).fetchall()
        return render_template("results.html", books=book_s, username=session["username"])

    else:
      return render_template("search.html",message="No results to match your search...", username= session["username"])

@app.route("/home/results/<string:title>", methods=["GET","POST"])
def details(title):
    book_id= db.execute("SELECT book_id FROM books WHERE title= :title",{"title":title}).fetchone()
    book_s= db.execute("SELECT * FROM books WHERE title= :title",{"title":title}).fetchone()
    revs=db.execute("SELECT review, username, ratings FROM reviews WHERE book_id= :book_id ",{"book_id":book_id[0]}).fetchall()
    return render_template("review.html", books=book_s, revs=revs, username= session["username"])

@app.route("/<string:title>", methods=["GET","POST"])
def reviews(title):
    my_rev= request.form.get("myrev")
    print(my_rev)
    if my_rev is not None:
        book_id= db.execute("SELECT book_id FROM books WHERE title= :title",{"title":title}).fetchone()
        db.execute("INSERT INTO reviews(review, username, book_id) VALUES :my_rev, :username, :book_id",{"my_rev":my_rev, "username":session["username"],"book_id":book_id})
        db.commit()
    return redirect(url_for('details', title=title))

#@app.route("/my_profile")
#def profile():


@app.route("/api/<string:isbn>")
def user_search(isbn):
    book= db.execute("SELECT * FROM books WHERE isbn= :isbn", {"isbn" :isbn}).fetchall()
    title= book[0][2]
    author= (book[0][3])
    year= (book[0][4])
    res= requests.get("https://www.goodreads.com/book/review_counts.json ", params={"key":"KEY", "isbns":isbn})
    message= json.dumps({"TITLE":title, "AUTHOR":author,"ISBN":isbn,"YEAR OF PUBLICATION":year})
    return render_template("isbn.html", message=message)

@app.route("/goback")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/ret_home")
def rethome():
    return redirect(url_for('home'))
