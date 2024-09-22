import secrets
import string
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Set the correct database URI depending on your environment
# Uncomment the one you need

# For local testing
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/gagik/Desktop/flask-backend/instance/lite-database.db'

# For production server
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/lite-web-app/instance/lite-database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User and AccessToken models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(16), unique=True, nullable=False)
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
search_criteria = input("Search by (name/key): ").strip().lower()
if search_criteria not in ['name', 'key']:
    raise ValueError("Invalid search criteria. Choose 'name' or 'key'.")

search_value = input(f"Enter user {search_criteria}: ").strip()
if not search_value:
    raise ValueError("Search value must not be empty.")

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

# Update existing users with new tokens
with app.app_context():
    if search_criteria == 'name':
        user = User.query.filter_by(username=search_value).first()
    else:
        user = User.query.filter_by(key=search_value).first()

    if user:
        # User exists, add new tokens
        for token in access_token_chars:
            existing_token = AccessToken.query.filter_by(token=token).first()
            if existing_token:
                print(f"Token {token} already exists and will not be added.")
            else:
                new_token = AccessToken(token=token, user_id=user.id)
                db.session.add(new_token)
        db.session.commit()  # Commit the access tokens
        print(f"Updated user: {user.username} with key: {user.key} with new tokens.")
    else:
        print("No user found with the provided criteria. No changes were made.")
