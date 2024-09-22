from .Lite import *
from flask import Blueprint, render_template, request, flash, redirect, url_for
from functools import wraps
from flask import session
from .models import User
from . import  db, limiter
import asyncio
from threading import Thread

views = Blueprint('views', __name__)
order_logs = {}  # Global dictionary to store logs


def background_orderhandler(user_id, BEARER_TOKENS, ticker, amount, side, key):
    log_messages = []
    for BEARER_TOKEN in BEARER_TOKENS:
        if BEARER_TOKEN != '':
            log_message = threadHandler(BEARER_TOKEN, ticker, amount, side, key)
            log_messages.append(log_message)
    order_logs[user_id] = "\n".join(log_messages)


@views.app_errorhandler(404)  # This applies to the entire app (for 404 errors)
def not_found(e):
    return render_template("error404.html"), 404

@views.app_errorhandler(429)  # This applies to the entire app (for 429 errors)
def ratelimit_handler(e):
    return render_template('error429.html'), 429

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:  # If user is not logged in
            flash('You need to log in to access this page.', category='error')
            return redirect(url_for('auth.login'))  # Redirect to login page
        return f(*args, **kwargs)  # Proceed to the view if logged in
    return decorated_function

@views.route('/')
def home():
    return render_template('home.html')


@views.route('/lite', methods=['GET', 'POST'])
@login_required
@limiter.limit("8 per minute")
def lite():
    user_id = session.get('user_id')
    litekey = session.get('key')
    user = User.query.filter_by(id=user_id, key=litekey).first()

    if request.method == "POST":
        if user:
            data = request.form
            BEARER_TOKENS = data['api-keys'].splitlines()
            ticker = data['ticker']
            amount = data['amount']
            side = data['side']
            
            for i in BEARER_TOKENS:
                if len(i) < 28:
                    flash('One or more of your API keys was too short! Please enter the correct API key(s)!', category='error')
                    return redirect(url_for('views.lite'))
            
            if len(ticker) > 5:
                flash('The ticker is too long! Please enter the correct ticker!', category='error')
                return redirect(url_for('views.lite'))
            
            if not accesstokenchecker(BEARER_TOKENS, litekey):
                flash('Access token mismatch! Please enter only your access tokens.', category='error')
                return redirect(url_for('views.lite'))
            else:
                flash('Orders placed! Please check your Tradier accounts.', category='success')
                # Start the background order handler with user_id
                thread = Thread(target=background_orderhandler, args=(user.id, BEARER_TOKENS, ticker, amount, side, litekey))
                thread.start()
                
            return redirect(url_for('views.view_orderlog'))  # Redirect to the updated order log page
        else:
            session.clear()
            flash('Your Lite Key is no longer valid. Please log in again.', category='error')
            return redirect(url_for('auth.login'))
    else:
        return render_template('lite.html')  # Make sure to render the correct template here


@views.route('/orderlog')
@login_required
def view_orderlog():
    user_id = session.get('user_id')
    order_log = order_logs.get(user_id, "No log available yet.")  # Retrieve log for user
    return render_template('orderlog.html', order_log=order_log)