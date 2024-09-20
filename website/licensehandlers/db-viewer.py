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
    key = db.Column(db.String(16), unique=True)
    username = db.Column(db.String(150))
    subscription_type = db.Column(db.String(150))

class AccessToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='access_tokens')

# Function to view all users and their access tokens
def view_users():
    with app.app_context():
        users = User.query.all()
        if not users:
            print("No users found in the database.")
            return
        for user in users:
            print(f"User: {user.username}, Subscription: {user.subscription_type}, Key: {user.key}")
            if user.access_tokens:
                for token in user.access_tokens:
                    print(f"  Access Token: {token.token}")
            else:
                print("  No access tokens found.")

# Run the function to display users and tokens
if __name__ == "__main__":
    view_users()