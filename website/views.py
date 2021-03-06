from app import app

from flask import abort
from flask import g
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask.ext.login import current_user
from flask.ext.login import login_required
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import LoginManager

from models import *

import sqlalchemy

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
    if not current_user.is_authenticated():
        return redirect(url_for('login'))

    return redirect(url_for('people'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

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
            session['waitlist_email'] = body['email']
            return redirect('/waitlist')
            #session['register'] = True
            #session['email'] = body['email']
            #return redirect('/register')
    else:
        return 'some error occurred'

    return redirect('/')

@app.route('/waitlist', methods=['GET', 'POST'])
def waitlist():
    if request.method == 'GET':
        return render_template('register.html', email=session['waitlist_email'])

    if not session.get('waitlist_email', None):
        return redirect('/login')

    done = False
    try:
        w = WaitList(session['waitlist_email'])
        db.session.add(w)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        done = True

    del session['waitlist_email']
    return render_template('register_thanks.html', done=done)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('register', None):
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('edit_profile.html', email=session['email'])

    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    irc_nick = request.form['irc_nick']
    website = request.form['website']
    github = request.form['github']
    email = request.form['email']
    about = request.form['about']

    new_user = User(email, username, first_name, last_name, about, irc_nick,
                    website, github)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    del session['register']
    del session['email']

    return redirect('/')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/people')
def people():
    users = User.query.all()
    return render_template('people.html', people=users)

@app.route('/profile/earned-badges')
def earned_badges(user=None, status=True):
    if user is None:
        user = g.user
    earned_badges = EarnedBadge.query.filter_by(user=user, status=status,
                                                declined=False)
    return render_template('earned_badges.html', badges=earned_badges, status=status)

@app.route('/profile/<username>/earned-badges')
def user_earned_badges(username):
    user = User.query.filter_by(username=username).first()
    return earned_badges(user=user)

@app.route('/profile/earned-badges/pending')
def earned_badges_pending():
    return earned_badges(status=False)

@app.route('/profile/earned-badges/pending/accept', methods=['POST'])
def earned_badges_pending_accept():
    resp = {'status': 'OK'}
    if 'slug' not in request.form:
        resp['status'] = '400'

    eb = EarnedBadge.query.filter_by(slug=request.form['slug']).first()
    eb.status = True
    db.session.commit()
    return json.dumps(resp)

@app.route('/profile/earned-badges/pending/decline', methods=['POST'])
def earned_badges_pending_decline():
    resp = {'status': 'OK'}
    if 'slug' not in request.form:
        resp['status'] = '400'

    eb = EarnedBadge.query.filter_by(slug=request.form['slug']).first()
    eb.declined = True
    db.session.commit()
    return json.dumps(resp)

@app.route('/profile/<username>/earned-badges/pending')
@login_required
def user_earned_badges_pending(username):
    if username != g.user.username:
        abort(400)

    user = User.query.filter_by(username=username, status=False).first()
    return earned_badges(user=user, status=False)

@app.route('/profile')
def profile_me():
    return profile(current_user.username)

@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    if request.method == 'GET':
        return render_template('edit_profile.html', email=g.user.email)

    g.user.username = request.form['username']
    g.user.first_name = request.form['first_name']
    g.user.last_name = request.form['last_name']
    g.user.about = request.form['about']
    g.user.website = request.form['website']
    g.user.github = request.form['github']
    g.user.irc_nick = request.form['irc_nick']
    db.session.commit()
    return redirect('/profile')

@app.route('/profile/<username>')
def profile(username):
    u = User.query.filter_by(username=username).first()
    eb = EarnedBadge.query.filter_by(user=u, status=True).all()
    return render_template('view_profile.html', user=u, badges=eb)

@app.route('/people_search')
def people_search(term):
    return 'something'

@app.route('/assertion/<slug>')
def assertion(slug):
    eb = EarnedBadge.query.filter_by(slug=slug).first()
    resp = make_response(json.dumps(eb.create_assertion()))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/badges/<slug>')
def badge(slug):
    b = Badge.query.filter_by(slug=slug).first()
    eb = EarnedBadge.query.filter_by(badge=b, status=True).all()
    people = []
    for e in eb:
        people.append(e.user)
    return render_template('badge.html', b=b, people=people)

@app.route('/badges')
def badges():
    b = Badge.query.all()
    return render_template('badges.html', badges=b)
