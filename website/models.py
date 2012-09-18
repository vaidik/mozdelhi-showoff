from app import app
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    name = db.Column(db.String(120))

    def __init__(self, email, name):
        self.email = email
        self.name = name

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
    description = db.Column(db.String(128))
    version = db.Column(db.String(50))
    criteria = db.Column(db.String(200))
    #evidence = db.Column(db.String(200))

    # PNG Image only
    image = db.Column(db.String(200), unique=True)

    issuer_origin = db.Column(db.String(200))
    issuer_name = db.Column(db.String(50))
    issuer_org = db.Column(db.String(50))
    issuer_contact = db.Column(db.String(50))

    def __init__(self, name, description, image, version, criteria,
                 issuer_origin, issuer_name, issuer_org=None,
                 issuer_contact=None):
        self.name = name
        self.description = description
        self.image = image
        self.version = version
        self.criteria = criteria
        self.issuer_origin = issuer_origin
        self.issuer_name = issuer_name
        self.issuer_org = issuer_org
        self.issuer_contact = issuer_contact


class EarnedBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)

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
    
    def __init__(self, user, badge, salt,
                 evidence=None, issued_on=None, expires=None):
        self.user = user
        self.badge = badge
        self.salt = salt
        self.recipient = ''
        self.evidence = evidence
        self.issued_on = issued_on
        self.expires = expires
        self.status = False

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

