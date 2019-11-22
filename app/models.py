import datetime
from time import time

import jwt
from flask_security import (RoleMixin, UserMixin)
from flask_security.utils import hash_password

from app import db, login_manager
from config import Config

key = Config.SECRET_KEY

class Auxiliar(db.Model):
	identifier = db.Column(db.Integer, primary_key=True, autoincrement=True)
	number_seq = db.Column(db.Integer)
	
	def __init__(self, number_seq):
		self.number_seq = number_seq

	def __repr__(self):
		return '<Stats %r>' % (self.number_seq)


class Base(db.Model):
	__abstract__ = True
	id = db.Column(db.Integer, primary_key=True)
	created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
	modified_at = db.Column(db.DateTime, default=db.func.current_timestamp(),
							onupdate=db.func.current_timestamp())

roles_users = db.Table('roles_users',
					db.Column('user_id', db.Integer(),
							db.ForeignKey('auth_user.id')),
					db.Column('role_id', db.Integer(),
							db.ForeignKey('auth_role.id')))


class Role(Base, RoleMixin):
	__tablename__ = 'auth_role'
	name = db.Column(db.String(80), nullable=False, unique=True)
	description = db.Column(db.String(255))

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Role {0}>'.format(self.name)


class User(Base, UserMixin):
	
	__tablename__ = 'auth_user'
	email = db.Column(db.String(255), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False)
    # first_name = db.Column(db.String(255))
    # last_name = db.Column(db.String(255))
	active = db.Column(db.Boolean())
    #confirmed_at = db.Column(db.DateTime())
	last_login_at = db.Column(db.DateTime())
	current_login_at = db.Column(db.DateTime())
    # Why 45 characters for IP Address ?
    # # See http://stackoverflow.com/questions/166132/maximum-length-of-the-textual-representation-of-an-ipv6-address/166157#166157
	last_login_ip = db.Column(db.String(45))
	current_login_ip = db.Column(db.String(45))
	login_count = db.Column(db.Integer)
	roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
	
	def __repr__(self):
		return '<User {}>'.format(self.email)

	
	#@staticmethod
	def encode_auth_token(self, user_id):
		"""
		Generates the Auth Token
		:return: string
		"""
		try:
			payload = {
				'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1, seconds=5),
				'iat': datetime.datetime.utcnow(),
				'sub': user_id
            }
		
			return jwt.encode(payload, key, algorithm='HS256')
        
		except Exception as e:
			return e
		
	@staticmethod
	def decode_auth_token(auth_token):
		"""
		Decodes the auth token
		:param auth_token:
		:return: integer|string
		"""
		try:
			#jwt.decode(auth_token, key)
			
			payload = jwt.decode(auth_token, key)
			is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
			if is_blacklisted_token:
				return 'Token blacklisted. Please log in again.'
			else:
				return payload['sub']

		except jwt.ExpiredSignatureError:
			return 'Signature expired. Please log in again.'

		except jwt.InvalidTokenError:
			return 'Invalid token. Please log in again.'


class BlacklistToken(db.Model):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'reddington'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False
