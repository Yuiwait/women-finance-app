from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Updated MySQL credentials
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://bhumika:sanjay@localhost/financial_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed Password
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # Foreign Key
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship("User", backref=db.backref("expenses", lazy=True))

# Create Tables
with app.app_context():
    db.create_all()
    print("✅ Tables created successfully!")
