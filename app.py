import os
import random
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity
)
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# JWT Configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your_secret_key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 900  # 15 min
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 86400  # 24 hours
jwt = JWTManager(app)

# Email Configuration
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

mail = Mail(app)


# Database Connection
def create_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
    except Error as e:
        print("Error connecting to MySQL:", e)
        return None


# Serve Frontend Pages
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")  # ✅ Ensure Flask serves the login page


@app.route("/register")
def register_page():
    return render_template("register.html")


# API Endpoints
@app.route("/api/register", methods=["POST"])
def register():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    required_fields = ["name", "email", "password", "role"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    name, email, password, role = data["name"], data["email"], data["password"], data["role"]
    hashed_password = generate_password_hash(password)
    otp = str(random.randint(100000, 999999))  # Generate 6-digit OTP

    db = create_db_connection()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already registered"}), 400

        query = "INSERT INTO users (name, email, password_hash, role, otp, is_verified) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (name, email, hashed_password, role, otp, False))
        db.commit()

        send_otp(email, otp)  # Send OTP via email

        return jsonify(
            {"message": "User registered successfully! Please verify your email using the OTP sent to you."}), 201
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = create_db_connection()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor()
    try:
        cursor.execute("SELECT id, name, password_hash, role, is_verified FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        if not check_password_hash(user[2], password):
            return jsonify({"error": "Invalid credentials"}), 401
        if not user[4]:  # Email not verified
            return jsonify({"error": "Email not verified. Please verify first."}), 403

        access_token = create_access_token(identity={"id": str(user[0]), "name": user[1], "role": user[3]})
        refresh_token = create_refresh_token(identity=str(user[0]))

        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
    finally:
        cursor.close()
        db.close()


# Fetch Expenses for Logged-in User
@app.route("/api/expenses", methods=["GET"])
@jwt_required()
def get_expenses():
    user_id = get_jwt_identity()["id"]
    db = create_db_connection()
    if not db:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT category, amount FROM expenses WHERE user_id=%s", (user_id,))
        expenses = cursor.fetchall()
        return jsonify(expenses), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
