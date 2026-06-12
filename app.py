from flask import Flask, render_template

app= Flask(__name__)

@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register")
def home():
    return render_template("register.html")


@app.route("/login")
def home():
    return render_template("login.html")


@app.route("/dashboard")
def home():
    return render_template("dashboard.html")


@app.route("/save_password")
def home():
    return render_template("save_password.html")


@app.route("/edit-password")
def home():
    return render_template("edit_password.html")


@app.route("/logout")
def home():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug = True)

