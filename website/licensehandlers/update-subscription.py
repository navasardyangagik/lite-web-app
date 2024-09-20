from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Set the correct database URI depending on your environment
# Uncomment the one you need

# For local testing
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lite-database.db'

# For production server
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/lite-web-app/instance/lite-database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model definition
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(16), unique=True, nullable=False)

# Function to update user's subscription type
def update_subscription(identifier, subscription_type):
    with app.app_context():
        # Try to find the user by key or username
        user = User.query.filter((User.username == identifier) | (User.key == identifier)).first()
        
        if user:
            user.subscription_type = subscription_type
            db.session.commit()
            print(f"User {user.username}'s subscription updated to {subscription_type}.")
        else:
            print(f"User with name/key '{identifier}' not found.")

# Get user input
identifier = input("Enter the user's name or key: ").strip()
if not identifier:
    raise ValueError("Name or key must not be empty.")

subscription_type = input("Enter new subscription type: ").strip()
validsubs = ['Speed', 'Silver', 'Gold', 'Platinum']
if subscription_type not in validsubs:
    raise ValueError("Invalid subscription type.")

# Update the subscription
update_subscription(identifier, subscription_type)