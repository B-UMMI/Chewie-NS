import datetime
from time import time

from flask_security import (RoleMixin, UserMixin)
from flask_security.utils import hash_password

from app import db, login_manager
from config import Config

key = Config.SECRET_KEY

class Auxiliar(db.Model):
	"""
	Definition of the Auxiliar model for the database
	"""
	identifier = db.Column(db.Integer, primary_key=True, autoincrement=True)
	number_seq = db.Column(db.Integer)
	
	def __init__(self, number_seq):
		self.number_seq = number_seq

	def __repr__(self):
		return '<Stats %r>' % (self.number_seq)


class Base(db.Model):
	"""
	Definition of the Base model for the database
	"""
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
	"""
	Definition of the Role model for the database
	"""
	__tablename__ = 'auth_role'
	name = db.Column(db.String(80), nullable=False, unique=True)
	description = db.Column(db.String(255))

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return '<Role {0}>'.format(self.name)


class User(Base, UserMixin):
	"""
	Definition of the User model for the database
	"""
	
	__tablename__ = 'auth_user'
	email = db.Column(db.String(255), nullable=False, unique=True)
	password = db.Column(db.String(255), nullable=False)
	name = db.Column(db.String(255), nullable=False)
	username = db.Column(db.String(255), nullable=False)
	organization = db.Column(db.String(255), nullable=False)
	active = db.Column(db.Boolean())
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

