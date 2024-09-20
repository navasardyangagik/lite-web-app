from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Flask and SQLAlchemy setup
app = Flask(__name__)

# Update the database path accordingly
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lite-database.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/lite-web-app/instance/lite-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User and AccessToken models
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

# Function to delete a token
def delete_token(token_to_delete):
    with app.app_context():
        # Search for the token
        token = AccessToken.query.filter_by(token=token_to_delete).first()
        
        if token:
            # If token is found, delete it
            db.session.delete(token)
            db.session.commit()
            print(f"Token '{token_to_delete}' deleted successfully.")
        else:
            print(f"Token '{token_to_delete}' not found.")

# Get user input
token_to_delete = input("Enter the token to delete: ").strip()
if not token_to_delete:
    raise ValueError("Token must not be empty.")

# Delete the token
delete_token(token_to_delete)