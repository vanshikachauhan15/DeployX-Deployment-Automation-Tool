from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from core.models import User, db

auth = Blueprint("auth", __name__)

# ---------------- SIGNUP ----------------
@auth.route("/signup", methods=["GET", "POST"])
def signup():

    # ✅ Already logged in → dashboard
    if "user_id" in session:
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return render_template("signup.html")

    data = request.form
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return render_template("signup.html", error="Email and password required")

    if User.query.filter_by(email=email).first():
        return render_template("signup.html", error="User already exists")

    user = User(
        email=email,
        password=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("auth.login"))

# ---------------- LOGIN ----------------
@auth.route("/login", methods=["GET", "POST"])
def login():

    # Agar already logged in hai aur login page open kare
    if "user_id" in session:
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return render_template("login.html", error="Invalid email or password")

    session["user_id"] = user.id
    session["email"] = user.email

    # ✅ LOGIN KE BAAD HOME
    return redirect(url_for("main.index"))


# ---------------- LOGOUT ----------------
@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
