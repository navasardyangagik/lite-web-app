import secrets
import string
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask and SQLAlchemy setup
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/gagik/Desktop/flask-backend/instance/lite-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User and AccessToken models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(16), unique=True, nullable=False)  # Add this column for storing the unique key
    access_tokens = db.relationship('AccessToken', backref='user', lazy=True)


class AccessToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Function to generate a random key
def generate_key():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

# Create tables if they don't exist
with app.app_context():
    db.create_all()  # Ensure tables are created before working with them

# Get user input
full_name = input("User full name: ").strip()
if not full_name:
    raise ValueError("User name must not be empty.")

subscription_type = input("Subscription type: ").strip()
validsubs = ['Speed', 'Silver', 'Gold', 'Platinum']
if subscription_type not in validsubs:
    raise ValueError("Invalid subscription type.")

# Number of identities (access tokens)
try:
    identitiesquestion = int(input("Identities number: "))
    if identitiesquestion <= 0:
        raise ValueError("Number of identities must be greater than 0.")
except ValueError:
    raise ValueError("Please enter a valid number for identities.")

# Collect access tokens
access_token_chars = []
for i in range(identitiesquestion):
    token = input(f"Enter 10 characters for identity {i + 1}: ").strip()
    if len(token) != 10:
        raise ValueError("Each token must be exactly 10 characters.")
    access_token_chars.append(token)

# Generate a random key
key = generate_key()

# Save to the database
with app.app_context():
    # Create a new user with the generated key
    new_user = User(username=full_name, subscription_type=subscription_type, key=key)
    db.session.add(new_user)
    db.session.commit()  # Commit so that user is saved, and we can reference its ID

    # Add access tokens for this user
    for token in access_token_chars:
        new_token = AccessToken(token=token, user_id=new_user.id)
        db.session.add(new_token)

    db.session.commit()  # Commit the access tokens

print(f"Generated and saved key: {key} with tokens: {access_token_chars}")