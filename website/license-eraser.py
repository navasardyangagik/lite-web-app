from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask and SQLAlchemy setup
app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/gagik/Desktop/flask-backend/instance/lite-database.db'
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

# Create tables if they don't exist
with app.app_context():
    db.create_all()  # Ensure the database tables exist

# Function to delete user by key or name
def delete_user_by_key_or_name():
    # Ask the user whether they want to search by key or name
    search_by = input("Would you like to delete by (1) Key or (2) Name? ")

    if search_by == '1':
        # Delete by key
        key = input("Enter the key to delete: ").strip()
        with app.app_context():
            user = User.query.filter_by(key=key).first()
            if user:
                # Delete user and associated access tokens
                db.session.delete(user)
                db.session.commit()
                print(f"User with key {key} deleted successfully.")
            else:
                print(f"No user found with key {key}.")
    elif search_by == '2':
        # Delete by username
        username = input("Enter the user's name: ").strip()
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                # Delete user and associated access tokens
                db.session.delete(user)
                db.session.commit()
                print(f"User with name {username} deleted successfully.")
            else:
                print(f"No user found with name {username}.")
    else:
        print("Invalid choice. Please select either 1 or 2.")

# Call the function to delete a user
delete_user_by_key_or_name()