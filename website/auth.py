from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, AccessToken
from flask import session
from . import  db, limiter

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("8 per minute")
def login():
    if request.method == 'POST':
        data = request.form
        key = data['key']
        user = User.query.filter_by(key=key).first()
        
        if len(key) != 16:
            flash('Key is too long/short! Try again!', category='error')
            return redirect(url_for('auth.login'))

        if user and user.key == key:
            # Store user_id and Lite Key in session
            session['user_id'] = user.id
            session['username'] = user.username
            session['key'] = key  # Store the Lite Key for later verification
            
            flash(f'Logged in. Welcome, {user.username}! Membership: {user.subscription_type}', category='success')
            return redirect(url_for('views.lite'))  # Redirect to the protected page
        else:
            flash('404 License key not found!', category='error')

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()  # Clear the session to log out
    flash('Logged out successfully!', category='success')
    return redirect(url_for('views.home'))