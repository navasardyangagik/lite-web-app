from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter  # Add this import
from flask_limiter.util import get_remote_address  # Add this import
from os import path

db = SQLAlchemy()
DB_NAME = 'lite-database.db'

# Initialize Flask-Limiter globally
limiter = Limiter(
    key_func=get_remote_address,  # Rate limit based on IP address
    default_limits=["200 per day", "50 per hour"]  # Global rate limits
)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'J9iFXhOjHO^$nck10dJ6EW$NNqU%4QZM'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    # Attach the limiter to the app
    limiter.init_app(app)
    
    # Error 404 Page handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error404.html"), 404

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    with app.app_context():
        create_database()

    return app

def create_database():
    if not path.exists('website/' + DB_NAME):
        db.create_all()
        print('Created Database!')
