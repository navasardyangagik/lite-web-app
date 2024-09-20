from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/gagik/Desktop/flask-backend/instance/lite-database.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/lite-web-app/instance/lite-database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"User: {user.username}, Subscription: {user.subscription_type}")
        for token in user.access_tokens:
            print(f"  Access Token: {token.token}")