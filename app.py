from flask import Flask, render_template, request, redirect
import sqlite3
from werkzeug.security import generate_password_hash

app= Flask(__name__)

def get_db_connection():
    connection = sqlite3.connect("password_manager.db")
    connection.row_factory = sqlite3.Row
    return connection

@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method== "POST":
        full_name = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        if password != confirm_password:
            return "Passwords do not match"
        
        password_hash = generate_password_hash(password)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email, password_hash)
            )
            connection.commit()
            connection.close()
            return redirect("/login")
        
        except sqlite3.IntegrityError:
            connection.close()
            return "Email already registred."
        
    return render_template("register.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/save_password")
def save_password():
    return render_template("save_password.html")


@app.route("/edit_password")
def edit_password():
    return render_template("edit_password.html")


@app.route("/logout")
def logout():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug = True)

