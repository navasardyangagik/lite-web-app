from .Lite import *
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from functools import wraps
from flask import session
from .models import User
from . import db, limiter
from threading import Thread, Lock
import time

views = Blueprint('views', __name__)


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
                
                # Process orders synchronously without threading
                log_messages = []
                for BEARER_TOKEN in BEARER_TOKENS:
                    accts = accByPlanHandler(BEARER_TOKEN, litekey)
                    log_message = threadHandler(BEARER_TOKEN, ticker, amount, side, litekey, accts)
                    log_messages.append(log_message)

                order_log = "\n".join(log_messages)
                print(order_log)
                session['order_log'] = order_log  # Save log to session

                return redirect(url_for('views.view_orderlog'))
        else:
            session.clear()
            flash('Your Lite Key is no longer valid. Please log in again.', category='error')
            return redirect(url_for('auth.login'))

    if user:
        return render_template('lite.html')
    else:
        session.clear()
        flash('Your Lite Key is no longer valid. Please log in again.', category='error')
        return redirect(url_for('auth.login'))


@views.route('/orderlog')
@login_required
def view_orderlog():
    order_log = session.get('order_log', "No log available.")
    session.pop('order_log', None)  # Clear the log after viewing
    return render_template('orderlog.html', order_log=order_log)