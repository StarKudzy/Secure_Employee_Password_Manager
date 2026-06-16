from flask import Flask, render_template, request, redirect, session
import sqlite3 #connect to SQLite Database
import os #file handling- encryption key storage
import secrets
import string
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

#create the flas app
app= Flask(__name__)
app.secret_key = "change_this_to_a_random_key" # create flask key

#database connection
def get_db_connection():
    connection = sqlite3.connect("password_manager.db")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON") # PRAGMA statement enforce relations between tables
    return connection

key_file = "secret.key"
#fn  create encryption key
def create_key():
    key = Fernet.generate_key()
    with open(key_file, "wb") as file:
        file.write(key)
    
   #load encryption key from secret key 
def load_key():
    with open(key_file, "rb") as file:
        return file.read()
    
    
def get_cipher():
    # creates secret key if it does not exist
    if not os.path.exists(key_file):
        create_key()
        
    key = load_key()
    return Fernet(key)
    

cipher = get_cipher()

def encrypt_password(password):
    #encrypt plain-text password before saving it to the database
    encrypted_password = cipher.encrypt(password.encode())
    return encrypted_password.decode()

# decrypt password when the user wants to view or edit
def decrypt_password(encrypted_password):
    decrypted_password = cipher.decrypt(encrypted_password.encode())
    return decrypted_password.decode()
           
    
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


@app.route("/login", methods=["GET", "POST"])
def login():
    #if user submits the login form
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
    #search for a user using email
        connection = get_db_connection()
        user = connection.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        connection.close()    
    
    #check if the user exists and the entered password is correct
        if user and check_password_hash(user["password_hash"], password):
          session["user_id"] = user["id"] #store user info in the session and keeps user logged in
          session["full_name"] = user["full_name"]
        
          return redirect("/dashboard")
    #if the email or password is wrong
        return("Invalid email or password")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    #only logged-in users can access the dashboard
    
    if "user_id" not in session:
        return redirect("/login")
    
    connection = get_db_connection()
    
    #get passwords of logged in user
    passwords = connection.execute(
        """
        SELECT * FROM saved_passwords
        WHERE user_id = ? 
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()
    
    connection.close()
    return render_template("dashboard.html", passwords=passwords)


@app.route("/save-password", methods = ["GET", "POST"])
def save_password():
    #Only logged-in users can save passwords
    
    if "user_id" not in session:
        return redirect("/login")
    
    #if user submits the save password form
    if request.method == "POST":
        service_name = request.form["service_name"]
        username = request.form["username"]
        password = request.form["password"]
        notes = request.form["notes"]
        
        encrypted_password = encrypt_password(password) #encrypt the password before storing it
        
        connection = get_db_connection()
        connection.execute(
            """
            INSERT INTO saved_passwords
            (user_id, service_name, username, encrypted_password, notes)
            VALUES(?,?,?,?,?)
            """,
            (
                session["user_id"],
                service_name,
                username,
                encrypted_password,
                notes
            )
        )
        
        
        connection.commit()
        connection.close()
        
        return redirect("/dashboard")
    return render_template("save_password.html")


@app.route("/edit_password")
def edit_password(password_id):
      #Only logged-in users can edit passwords
    
    if "user_id" not in session:
        return redirect("/login")
    
    
    connection = get_db_connection()
    
   
       
    saved_password = connection.execute(
            """
            SELECT * FROM saved_passwords
            WHERE id = ? AND user_id = ?
            
            """,
            (password_id, session["user_id"])).fetchone()
    
    if save_password is None:
        connection.close()
        return "Password not found"
    
    if request.method == "POST":
        service_name = request.form["service_name"]
        username = request.form["username"]
        password = request.form["password"]
        notes = request.form["notes"]
        
        encrypted_password = encrypt_password(password) #encrypt the password before storing it
        
       
        connection.execute(
            """
            UPDATE saved_passwords
            SET service_name = ?,username = ?, password = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                
                service_name,
                username,
                encrypted_password,
                notes,
                session["user_id"],
            )
        )
        
    
        
        
        connection.commit()
        connection.close()
        
        return redirect("/dashboard")
    
    return render_template("edit_password.html")

@app.route("/view-password/<int:password_id>")
def view_password(password_id):
    if "user_id" not in session:
        return redirect("/login")
    
    connection = get_db_connection

    saved_password = connection.execute(
        """
        SELECT * FROM saved_passwords
        WHERE id = ? AND user_id = ?
        """,
        (password_id, session["user_id"])
    ).fetchone()
    
    
    
    if save_password is None:
        return "Password not found"
    
    
    
    #decrypt password before showing it
    real_password = decrypt_password(saved_password["encrypt_password"])
    
    return f"""
              <h2>Saved Password</h2>
        <p><strong>Service:</strong> {saved_password["service_name"]}</p>
        <p><strong>Username:</strong> {saved_password["username"]}</p>
        <p><strong>Password:</strong> {real_password}</p>
        <p><strong>Notes:</strong> {saved_password["notes"]}</p>
        <a href="/dashboard">Back to Dashboard</a>

           """
           
    connection.close()       
   


@app.route("/logout")
def logout():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug = True)

