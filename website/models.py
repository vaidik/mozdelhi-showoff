from app import app
from hashlib import sha256
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

generate_slug = lambda name: '-'.join(name.lower().split(' '))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(10), unique=True)
    first_name = db.Column(db.String(20))
    last_name = db.Column(db.String(20))
    irc_nick = db.Column(db.String(20))
    website = db.Column(db.String(100))
    github = db.Column(db.String(30))
    about = db.Column(db.Text)

    def __init__(self, email, username, first_name, last_name, about,
                 irc_nick=None, website=None, github=None):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.about = about
        self.irc_nick = irc_nick
        self.website = website
        self.github = github

    def __repr__(self):
        return '<User %r>' % self.email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    slug = db.Column(db.String(128), unique=True)
    description = db.Column(db.String(128))
    version = db.Column(db.String(50))
    criteria = db.Column(db.String(200))

    # PNG Image only
    image = db.Column(db.String(200), unique=True)

    issuer_origin = db.Column(db.String(200))
    issuer_name = db.Column(db.String(50))
    issuer_org = db.Column(db.String(50))
    issuer_contact = db.Column(db.String(50))

    def __init__(self, name, description, image, version,
                 issuer_origin, issuer_name, issuer_org=None,
                 issuer_contact=None, slug=None):
        self.name = name
        self.description = description
        self.version = version

	# TO DO
	# Add support for custom origins
        self.issuer_origin = 'http://%s' % app.config['PERSONA_AUDIENCE']
        self.issuer_name = issuer_name
        self.issuer_org = issuer_org
        self.issuer_contact = issuer_contact

        # use the mentioned slug or generate new slug if not given
        self.slug = slug if self.slug else generate_slug(name)

        self.criteria = '/badges/%s' % self.slug
        self.image = '/static/img/badges/%s' % self.slug


class EarnedBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(128), unique=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('user',
                                   lazy='dynamic'))

    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'))
    badge = db.relationship('Badge', backref=db.backref('badge',
                                     lazy='dynamic'))

    salt = db.Column(db.String(10))
    recipient = db.Column(db.String(100))
    evidence = db.Column(db.String(200))
    issued_on = db.Column(db.DateTime)
    expires = db.Column(db.DateTime)

    # if the badge has been issued or not
    status = db.Column(db.Boolean)

    def __init__(self, user, badge, salt, slug=None,
                 evidence=None, issued_on=None, expires=None):
        self.user = user
        self.badge = badge
        self.salt = salt
        self.recipient = 'sha256$%s' % sha256('%s%s' % (user.email,
                                                        salt)).hexdigest()
        self.evidence = evidence
        self.issued_on = issued_on
        self.expires = expires
        self.status = False

        # slug should be username-badge_slug
        self.slug = '%s-%s' % (user.username, badge.slug)

    def create_assertion(self):
        assertion = {}
        assertion.update(recipient=self.recipient, salt=self.salt)

        if self.issued_on:
            assertion.update(issued_on=self.issued_on)

        if self.expires:
            assertion.update(expires=self.expires)

        if self.evidence:
            assertion.update(evidence=self.evidence)

        badge = {}
        b = self.badge
        badge.update(name=b.name, description=b.description, version=b.version,
                     image=b.image, criteria=b.criteria,
                     issuer=dict(origin=b.issuer_origin, name=b.issuer_name))
        if b.issuer_org:
            badge['issuer'].update(org=b.issuer_org)
        if b.issuer_contact:
            badge['issuer'].update(contact=b.issuer_contact)
        assertion.update(badge=badge)

        return assertion

'''
class Testing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean)

    def __init__(self):
        self.status = False
'''

