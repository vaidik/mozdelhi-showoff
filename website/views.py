from app import app

from flask import g
from flask import redirect
from flask import request
from flask import render_template
from flask import session
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import LoginManager

from models import *

import requests
import json

login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = 'login'

@app.before_request
def before_request():
    g.user = current_user

@login_manager.user_loader
def load_user(email):
    return User.query.get(email)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))

    #if 'assertion' not in request.form:
    #    return redirect()

    assertion = request.form['assertion']
    audience = app.config['PERSONA_AUDIENCE']

    req = requests.post('https://browserid.org/verify',
                        params={'assertion': assertion, 'audience': audience})
    body = json.loads(req.text)
    if body['status'] == 'okay':
        user = User.query.filter_by(email=body['email']).first()
        if user is not None:
            login_user(user)
        else:
            session['register'] = True
            return render_template('register.html', email=body['email'])
    else:
        return 'some error occurred'

    return redirect('/')

@app.route('/register', methods=['POST'])
def register():
    if session.get('register', None) is not True:
        return redirect(url_for('login'))

    name = request.form['name']
    email = request.form['email']

    new_user = User(email, name)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    del session['register']

    return redirect('/')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/badges')
def badges(status=True):
    earned_badges = EarnedBadge.query.filter_by(user=g.user, status=status)
    return render_template('badges.html', badges=earned_badges, status=status)

@app.route('/badges/pending')
def badges_pending():
    return badges(status=False)

@app.route('/profile')
def profile_me():
    return profile('asd')

@app.route('/profile/<username>')
def profile(username):
    return 'profile of %s' % username

@app.route('/people_search')
def people_search(term):
    return 'something'
