#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Pedro Cerqueira
    github: @pedrorvc

    Rafael Mamede
    github: @rfm-targa

DESCRIPTION

"""

import os
import jwt
import sys
import time
import pickle
import hashlib
import itertools
import statistics
import datetime as dt
import requests, json
from collections import Counter

# Flask imports
from flask_login import login_required
from flask_restplus import Resource, fields, marshal_with
from flask_security.utils import verify_password, hash_password
from flask_security import (login_user, logout_user, 
                            current_user, user_registered)

from flask_jwt_extended import (
    jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies,
    get_csrf_token, decode_token, jwt_optional
)

from flask import (current_app, render_template, flash, redirect, url_for, request, make_response, 
                   Response, stream_with_context, send_from_directory, jsonify)

from werkzeug.utils import secure_filename

# App imports
from app.models import User, Role
from app.utils import wrappers as w
from app.utils import sparql_queries
from app.utils import auxiliary_functions as aux
from app import (db, celery, login_manager,
                 datastore_cheat, security, jwt as jwtm)

from app.api import api, blueprint

# Helper imports
# from app.utils.blacklist_service import save_token

from SPARQLWrapper import SPARQLWrapper

# Get the error handlers to work with restplus
jwtm._set_error_handler_callbacks(api)

# queue to add locus do schema
@celery.task(time_limit=20)
def add_locus_schema(new_schema_url, new_locus_url):

    # count number of loci on schema and build the uri based on that number+1
    loci_count = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.COUNT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'],
                                                                      new_schema_url))

    # 0 if schema has no loci
    number_schema_parts = int(loci_count['results']['bindings'][0]['count']['value'])

    # create URI for new schema part
    new_schema_part_url = '{0}/loci/{1}'.format(new_schema_url, str(number_schema_parts+1))

    # link locus to schema (previous operations determined that schema exists)
    link_query = (sparql_queries.INSERT_SCHEMA_LOCUS.format(current_app.config['DEFAULTHGRAPH'],
                                                            new_schema_part_url,
                                                            str(number_schema_parts+1),
                                                            new_locus_url,
                                                            new_schema_url,
                                                            new_schema_part_url))

    link_locus = aux.send_data(link_query,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

    if link_locus.status_code in [200, 201]:
        return {'message': 'Locus successfully added to schema.'}, 201
    else:
        return {'message': 'Could not add locus to schema.'}, link_locus.status_code


# queue to add alleles
@celery.task(time_limit=20)
def add_allele(new_locus_url, spec_name, loci_id, new_user_url,
               new_seq_url, isNewSeq, sequence, allele_uri):

    max_tries = 3
    new_allele_url = allele_uri

    # add allele to virtuoso
    if isNewSeq:

        query2send = (sparql_queries.INSERT_ALLELE_NEW_SEQUENCE.format(current_app.config['DEFAULTHGRAPH'],
                                                                       new_seq_url,
                                                                       sequence,
                                                                       new_allele_url,
                                                                       spec_name,
                                                                       new_user_url,
                                                                       new_locus_url,
                                                                       str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                       new_allele_url.split('/')[-1]
                                                                       ))
        operation = ['ADD', 'add', 'added']
    else:

        query2send = (sparql_queries.INSERT_ALLELE_LINK_SEQUENCE.format(current_app.config['DEFAULTHGRAPH'],
                                                                        new_allele_url,
                                                                        spec_name,
                                                                        new_user_url,
                                                                        new_locus_url,
                                                                        str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                        new_allele_url.split('/')[-1],
                                                                        new_seq_url
                                                                        ))
        operation = ['LINK', 'link', 'linked']

    tries = 0
    insert = False
    while insert is False:

        # if len(sequence) < 2000:
        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])
#            else:
#                result = aux.send_big_query(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
#                                            query2send,
#                                            current_app.config['VIRTUOSO_USER'],
#                                            current_app.config['VIRTUOSO_PASS'])

        tries += 1

        if result.status_code in [200, 201]:
            insert = True
        elif tries == max_tries:
            insert = True

    if result.status_code > 201:
        return {'FAIL': 'Could not {0} new allele.'.format(operation[1])}, result.status_code
    else:
        return {operation[0]: 'A new allele has been {0} to {1}'.format(operation[2], new_allele_url)}, result.status_code


def enforce_locking(user_role, user_uri, locking_value):
    """
    """

    allow = [True, user_role]
    if user_role not in ['Admin', 'Contributor']:
        allow = [False, {'Not authorized': 'must have Admin or Contributor permissions.'}]

    # if user is a Contributor, check if it is the one that locked the schema
    if user_role == 'Contributor' and user_uri != locking_value:
        allow = [False, {'Not authorized': 'must have Admin permissions or be the Contributor that is altering the schema.'}]

    return allow


def generate(header, iterable):
    """
    """

    # first '{' has to be escaped
    yield '{{ "{0}": ['.format(header)
    if len(iterable) > 0:
        yield json.dumps(iterable[0])
        for item in iterable[1:]:
            yield ',{0}'.format(json.dumps(item))

    yield '] }'


# queue to add profile
@celery.task(time_limit=20)
def add_profile(rdf_2_ins):

    result = aux.send_data(rdf_2_ins,
                           current_app.config['LOCAL_SPARQL'],
                           current_app.config['VIRTUOSO_USER'],
                           current_app.config['VIRTUOSO_PASS'])

    # try to send it a few times if error
    try:
        if result.status_code > 201:
            time.sleep(2)
            result = aux.send_data(rdf_2_ins,
                                   current_app.config['LOCAL_SPARQL'],
                                   current_app.config['VIRTUOSO_USER'],
                                   current_app.config['VIRTUOSO_PASS'])

            if result.status_code not in [200, 201]:
                return {"message": "Sum Thing Wong creating profile"}, result.status_code
            else:
                return True, result.status_code

        else:
            return True, result.status_code

    except Exception as e:
        try:
            if result.status_code > 201:
                time.sleep(2)
                result = aux.send_data(rdf_2_ins,
                                       current_app.config['LOCAL_SPARQL'],
                                       current_app.config['VIRTUOSO_USER'],
                                       current_app.config['VIRTUOSO_PASS'])

                if result.status_code not in [200, 201]:
                    return {"message": "Sum Thing Wong creating profile"}, result.status_code
                else:
                    return True, result.status_code

            else:
                return True, result.status_code
        except Exception as e:

            return e, 400
        return e, 400


user_datastore = datastore_cheat

# Create a default admin user on Postgres and Virtuoso
# This runs every time this file reloads
@blueprint.before_app_first_request
def create_role():

    # check if Admin was previously created
    try:
        default = user_datastore.get_user(1)
    # will raise exception if database does not exist
    # this will happen at first execution when we
    # build the compose for the first time and there is no
    # Postgres database. After that, the Postgres database
    # should persist even if we remove all images
    except Exception:
        default = None

    # if the database or the Admin user do not exist
    # create the database
    if default is None:
        # this will drop db and delete all users
        # will not delete users from Virtuoso
        # rollback or the process will hang
        db.session.rollback()
        db.drop_all()
        db.create_all()

        print('Creating Admin account...', flush=True)
        # add possible roles to database
        user_datastore.create_role(name='Admin')
        user_datastore.create_role(name='Contributor')
        user_datastore.create_role(name='User')
        # create Admin user
        u = user_datastore.create_user(email="test@refns.com",
                                       password=hash_password("mega_secret"),
                                       username="chewie",
                                       organization="UMMI")
        user_datastore.add_role_to_user(u, "Admin")

        # check if Admin was successfully created in Postgres db
        postgres_admin = user_datastore.get_user(1)
        postgres_account = False if postgres_admin is None else True

        db.session.commit()

        # Create Admin in Virtuoso
        new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'],
                                             str(u.id))
        newUserRole = 'Admin'
        sparql_query = (sparql_queries.INSERT_USER.format(current_app.config['DEFAULTHGRAPH'],
                                                          new_user_url,
                                                          newUserRole))

        result = aux.send_data(sparql_query,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        # check if Admin was successfully inserted into Virtuoso graph
        virtuoso_admin = result.status_code
        virtuoso_account = True if virtuoso_admin in [200, 201] else False

        print('Created Postgres Admin: {0}\n'
              'Created Virtuoso Admin: {1}'.format(postgres_account, virtuoso_account), flush=True)

    # after the first execution we already have Admin
    else:
        print('Admin account already exists.', flush=True)


# API Routes

# Login/logout Routes

# Namespace for Login
auth_conf = api.namespace('auth', description='authentication operations')

# Login model
auth_model = api.model('LoginModel',
                       {'email': fields.String(required=True,
                                               description='User email address.',
                                               example='test@refns.com'),
                        'password': fields.String(required=True,
                                                  description='User password.',
                                                  example='mega_secret')
                       })

# refresh_model = api.model("RefreshModel", {
#     'refresh_token': fields.String(required=True,
#                                    description="refresh token")
# })


@auth_conf.route("/login")
class UserLoginAPI(Resource):
    """User login resource """

    @api.doc(responses={200: "Success"})
    @api.expect(auth_model, validate=True)
    @login_manager.request_loader
    def post(self):
        """
        Log users in and generate token
        """

        # get the post data
        post_data = request.get_json()

        try:
            # fetch the user data
            user = User.query.filter_by(email=post_data.get('email')).first()

            if user and verify_password(post_data.get('password'), user.password):
                # Log user in
                login_user(user)

                # Commit changes because SECURITY_TRACKABLE is True
                # db.session.commit()
                security.datastore.commit()

                # Generate token
                auth_token = create_access_token(identity=user)
                auth_refresh_token = create_refresh_token(identity=user)
                if auth_token and auth_refresh_token:
                    response_object = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'access_token': auth_token,
                        'refresh_token': auth_refresh_token
                    }
                    # Front-end communicating with back-end?
                    # set_access_cookies(jsonify(response_object), auth_token)
                    # set_refresh_cookies(jsonify(response_object), auth_refresh_token)
                    return response_object, 200
            else:
                response_object = {
                    'status': 'fail',
                    'message': 'email or password does not match.'
                }
                return response_object, 401

        except Exception as e:
            print(e)
            response_object = {
                'status': 'fail',
                'message': 'Try again'
            }
            return response_object, 500


@auth_conf.route("/refresh")
class RefreshToken(Resource):
    """Refresh token resource """

    @api.doc(responses={200: "Success"},
             security=["refresh_token"])
    @jwt_refresh_token_required
    def post(self, **kwargs):
        """ Generates a new access token with a provided and valid refresh token.
        """

        # Create the new access token
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)

        # Set the access JWT and CSRF double submit protection cookies
        # in this response
        resp = {'access_token': access_token}

        #resp = {'refresh': True}
        #set_access_cookies(resp, access_token)

        return resp, 200


@auth_conf.route("/logout")
class LogoutAPI(Resource):
    """ Logout resource """

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated'},
             security=['access_token'])
    @jwt_required
    def post(self):
        """Log out a user"""

        # get the post data
        auth_header = request.headers.get('Authorization')

        if auth_header:
            auth_token = auth_header
        else:
            auth_token = ''

        if auth_token:
            logout_user()

            response_object = {
                'status': 'Success',
                'message': 'Succesfully logged out'
            }
            return response_object

        else:
            response_object = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return response_object, 403


# Users Routes

# Namespace for User operations
user_conf = api.namespace('user', description='user related operations')

# User models
# models ensure that the specified output fields are displayed
# as long as data provided to model has the right structure and type
user_model = api.model('UserModel',
                       {'id': fields.Integer(required=True,
                                             description='User unique integer identifier.'),
                        'email': fields.String(required=True,
                                               description='User email address.'),
                        'username': fields.String(required=True, description='Username.'),
                        'organization': fields.String(required=True, description='Organization that the user belongs to.'),
                        'last_login_at': fields.DateTime(required=True,
                                                         description='User last login date.'),
                        'roles': fields.String(required=True,
                                               description='Role/Permission type of the user.'),
                        'validated': fields.Boolean(required=True,
                                                    description='User is valid if it was '
                                                                'successfully added to Postgres and to Virtuoso.')
                        })

current_user_model = api.model('CurrentUserModel',
                               {'id': fields.Integer(required=True,
                                                     description='User unique integer identifier.'),
                                'email': fields.String(required=True,
                                                       description='User email address.'),
                                'username': fields.String(required=True, description='Username.'),
                                'organization': fields.String(required=True, description='Organization that the user belongs to.'),
                                'last_login_at': fields.DateTime(required=True,
                                                                 description='User last login date.'),
                                'roles': fields.String(required=True,
                                                       description='Role/Permission type of the user.'),
                                'validated': fields.Boolean(required=True,
                                                            description='User is valid if it was '
                                                                        'successfully added to Postgres and to Virtuoso.')
                                })

register_user_model = api.model('RegisterUserModel',
                                {'email': fields.String(required=True,
                                                        description='User email address.'),
                                 'password': fields.String(required=True,
                                                           description='User NS account password.',
                                                           min_length=8),
                                 'username': fields.String(required=True, description='Username.'),
                                 'organization': fields.String(required=True, description='Organization that the user belongs to.')
                                 })

create_user_model = api.model('CreateUserModel',
                              {'email': fields.String(required=True,
                                                      description='User email address.'),
                               'password': fields.String(required=True,
                                                         description='User NS account password.',
                                                         min_length=8),
                               'username': fields.String(required=True, description='Username.'),
                               'organization': fields.String(required=True, description='Organization that the user belongs to.'),
                               'role': fields.String(required=False,
                                                     default='User',
                                                     description='Role/Permissions for the new user (User or Contributor).')
                               })


# User routes
@user_conf.route("/users")
class AllUsers(Resource):
    """ Returns a list of users """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated'},
             security=['access_token'])
    @api.marshal_with(user_model)
    @w.admin_required
    def get(self):
        """Returns the full list of users."""

        # returning list of users from Postgres
        ns_users = db.session.query(User).all()

        users_info = []
        # get info for each user and append to list
        for user in ns_users:

            current_user_dict = {}

            # check if user exists in Virtuoso
            user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], user.id)
            user_exists_query = sparql_queries.ASK_USER.format(user_uri)
            ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
            user_exists = ask_result['boolean']

            current_user_dict = {}
            current_user_dict['id'] = user.id
            current_user_dict['email'] = user.email
            current_user_dict['username'] = user.username
            current_user_dict['organization'] = user.organization
            # this value will be None/null if user never logged in
            current_user_dict['last_login_at'] = user.last_login_at
            current_user_dict['roles'] = str(user.roles[0])
            current_user_dict['validated'] = user_exists

            users_info.append(current_user_dict)

        # model definition will process list and output correct format
        return users_info, 200

    # hide class method (hide decorator has to be at start)
    @api.hide
    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated'},
             security=['access_token'])
    @api.expect(create_user_model, validate=True)
    @w.admin_required
    def post(self):
        """Creates a user (Admin only)."""

        postgres_account = False
        virtuoso_account = False

        # get post data
        data = request.get_json()

        email = data['email']
        password = data['password']
        username = data['username']
        organization = data['organization']
        # new users are created with User permissions
        new_user_role = data['role']

        # check if user already exists in Postgres
        postgres_user = user_datastore.get_user(email)
        if postgres_user is not None:
            postgres_account = True
            postgres_message = ('User with provided email already '
                                'exists in Postgres DB.')
            new_user_id = postgres_user.id
        else:
            # add new user to memory, without synchronising with DB and making it persistent
            new_user = user_datastore.create_user(email=email, 
                                                  password=hash_password(password),
                                                  username=username,
                                                  organization=organization)
            default_role = user_datastore.find_role(new_user_role)
            user_datastore.add_role_to_user(new_user, default_role)
            # we can get the new user identifier because session has autoflush
            new_user_id = new_user.id

            # try to commit and make changes persistent
            try:
                db.session.commit()
                postgres_account = True
                postgres_message = ('Successfully added new user with '
                                    'ID={0} to Postgres.'.format(new_user_id))
            except Exception as e:
                # could not commit changes
                # rollback session transactions
                db.session.rollback()
                # Postgres auto increment function will increment
                # user identifiers even if the changes cannot be committed
                postgres_message = 'Failed to commit changes. Discarded changes.'

        print(postgres_message, flush=True)

        # add user to Virtuoso only if it could be added to Postgres
        # auto increment function of Postgres should guarantee that we will not
        # add a user that already exists in Virtuoso
        if postgres_account is True:

            # create user URI
            new_user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'],
                                                 new_user_id)

            # check if user already exists in Virtuoso
            user_exists_query = sparql_queries.ASK_USER.format(new_user_uri)
            ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
            user_exists = ask_result['boolean']

            if user_exists is True:
                virtuoso_account = True
                virtuoso_message = 'User with provided ID={0} already exists in Virtuoso'.format(new_user_id)
            elif user_exists is False:
                # add user to Virtuoso
                new_user_query = (sparql_queries.INSERT_USER.format(current_app.config['DEFAULTHGRAPH'],
                                                                    new_user_uri,
                                                                    new_user_role))

                insert_result = aux.send_data(new_user_query,
                                              current_app.config['LOCAL_SPARQL'],
                                              current_app.config['VIRTUOSO_USER'],
                                              current_app.config['VIRTUOSO_PASS'])

                query_status = insert_result.status_code
                if query_status in [200, 201]:
                    virtuoso_account = True
                    virtuoso_message = ('{0}: Successfully added new user with '
                                        'ID={1} to Virtuoso.'.format(query_status, new_user_id))
                else:
                    virtuoso_message = '{0}: Could not add new user to Virtuoso.'.format(query_status)

        elif postgres_account is False:
            virtuoso_message = ('Cannot add new user to Virtuoso because '
                                'it could not be added to Postgres DB.')

        print(virtuoso_message, flush=True)

        return {'Postgres': '{0} ({1})'.format(postgres_account, postgres_message),
                'Virtuoso': '{0} ({1})'.format(virtuoso_account, virtuoso_message)}


@user_conf.route("/register_user")
class RegisterUser(Resource):
    """ Registers a user """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated'},
             security=[])
    @api.expect(register_user_model, validate=True)
    def post(self):
        """ Registers a user """

        postgres_account = False
        virtuoso_account = False

        # get post data
        data = request.get_json()

        email = data['email']
        password = data['password']
        username = data['username']
        organization = data['organization']
        # new users are created with User permissions
        new_user_role = 'User'

        # check if user already exists in Postgres
        postgres_user = user_datastore.get_user(email)
        if postgres_user is not None:
            postgres_account = True
            postgres_message = ('User with provided email already '
                                'exists in Postgres DB.')
            new_user_id = postgres_user.id
        else:
            # add new user to memory, without synchronising with DB and making it persistent
            new_user = user_datastore.create_user(email=email, 
                                                  password=hash_password(password),
                                                  username=username,
                                                  organization=organization)
            default_role = user_datastore.find_role(new_user_role)
            user_datastore.add_role_to_user(new_user, default_role)
            # we can get the new user identifier because session has autoflush
            new_user_id = new_user.id

            # try to commit and make changes persistent
            try:
                db.session.commit()
                postgres_account = True
                postgres_message = ('Successfully added new user with '
                                    'ID={0} to Postgres.'.format(new_user_id))
            except Exception as e:
                # could not commit changes
                # rollback session transactions
                db.session.rollback()
                # Postgres auto increment function will increment
                # user identifiers even if the changes cannot be committed
                postgres_message = 'Failed to commit changes. Discarded changes.'

        print(postgres_message, flush=True)

        # add user to Virtuoso only if it could be added to Postgres
        # auto increment function of Postgres should guarantee that we will not
        # add a user that already exists in Virtuoso
        if postgres_account is True:

            # create user URI
            new_user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'],
                                                 new_user_id)

            # check if user already exists in Virtuoso
            user_exists_query = sparql_queries.ASK_USER.format(new_user_uri)
            ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
            user_exists = ask_result['boolean']

            if user_exists is True:
                virtuoso_account = True
                virtuoso_message = 'User with provided ID={0} already exists in Virtuoso'.format(new_user_id)
            elif user_exists is False:
                # add user to Virtuoso
                new_user_query = (sparql_queries.INSERT_USER.format(current_app.config['DEFAULTHGRAPH'],
                                                                    new_user_uri,
                                                                    new_user_role))

                insert_result = aux.send_data(new_user_query,
                                              current_app.config['LOCAL_SPARQL'],
                                              current_app.config['VIRTUOSO_USER'],
                                              current_app.config['VIRTUOSO_PASS'])

                query_status = insert_result.status_code
                if query_status in [200, 201]:
                    virtuoso_account = True
                    virtuoso_message = ('{0}: Successfully added new user with '
                                        'ID={1} to Virtuoso.'.format(query_status, new_user_id))
                else:
                    virtuoso_message = '{0}: Could not add new user to Virtuoso.'.format(query_status)

        elif postgres_account is False:
            virtuoso_message = ('Cannot add new user to Virtuoso because '
                                'it could not be added to Postgres DB.')

        print(virtuoso_message, flush=True)

        return {'Postgres': '{0} ({1})'.format(postgres_account, postgres_message),
                'Virtuoso': '{0} ({1})'.format(virtuoso_account, virtuoso_message)}


@user_conf.route("/current_user")
class CurrentUser(Resource):
    """
    Class with methods related with the user that is currently logged in.
    """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated'},
             security=['access_token'])
    @api.marshal_with(current_user_model)
    @jwt_required
    def get(self):
        """Returns information about the current user."""

        # get user from Postgres DB
        current_user = get_jwt_identity()
        user = User.query.get_or_404(current_user)

        # check if user exists in Virtuoso
        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], current_user)
        user_exists_query = sparql_queries.ASK_USER.format(user_uri)
        ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
        user_exists = ask_result['boolean']

        current_user_dict = {}
        current_user_dict['id'] = user.id
        current_user_dict['email'] = user.email
        current_user_dict['username'] = user.username
        current_user_dict['organization'] = user.organization
        current_user_dict['last_login_at'] = user.last_login_at
        current_user_dict['roles'] = str(user.roles[0])
        current_user_dict['validated'] = user_exists

        return current_user_dict, 200


@user_conf.route("/<int:id>")
class Users(Resource):
    """
    Class with methods to obtain information about or modify users accounts.
    """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             params={'id': 'Specify the ID associated with the user'},
             security=['access_token'])
    @api.marshal_with(user_model)
    @w.admin_required
    def get(self, id):
        """Returns information about the user with the provided id."""

        # Gets users from Postgres DB
        try:
            user = User.query.get_or_404(id)
        except Exception:
            print('There is no user with provided ID.', flush=True)
            # return empty dict to get every value as 'null'
            return {}, 404

        # check if user exists in Virtuoso
        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], user.id)
        user_exists_query = sparql_queries.ASK_USER.format(user_uri)
        ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
        user_exists = ask_result['boolean']

        current_user_dict = {}
        current_user_dict['id'] = user.id
        current_user_dict['email'] = user.email
        current_user_dict['username'] = user.username
        current_user_dict['organization'] = user.organization
        # this value will be None/null if user never logged in
        current_user_dict['last_login_at'] = user.last_login_at
        current_user_dict['roles'] = str(user.roles[0])
        current_user_dict['validated'] = user_exists
        # add other relevant info to recover
        # can we recover number of schemas inserted by user and etc?

        return current_user_dict, 200


    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             params={'id': 'ID of the user to promote' },
             security=['access_token'])
    @w.admin_required
    def put(self, id):
        """Promote from User to Contributor"""

        # Get user data
        try:
            user = User.query.get_or_404(id)
        except Exception:
            return {'message': 'There is no user with provided ID.'}

        remove_this_role = user.roles[0]

        promote_to_this_role = user_datastore.find_role('Contributor')

        postgres_change = False
        if remove_this_role == promote_to_this_role:
            postgres_message = 'User with provided ID is already a Contributor in Postgres DB.'
            print(postgres_message, flush=True)
        elif remove_this_role == 'User':
            print('Promoting user to Contributor in Postgres DB...', end='', flush=True)
            # Remove User's current role
            user_datastore.remove_role_from_user(user, remove_this_role)
            # Add new role to the User (Promotion)
            user_datastore.add_role_to_user(user, promote_to_this_role)
            # Commit changes to the database
            db.session.commit()
            print('done.', flush=True)
            postgres_change = True
            postgres_message = 'Promoted user to Contributor in Postgres DB.'
        elif remove_this_role == 'Admin':
            postgres_message = 'Cannot change role of Admin in Postgres DB.'
            print(postgres_message, flush=True)

        # promote user in Virtuoso
        # delete current role
        # select info from single user
        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], id)

        role_query = (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              role_query)

        user_role = result['results']['bindings'][0]['role']['value']

        # delete User role and insert Contributor role
        virtuoso_change = False
        if user_role == 'User':
            # delete role
            print('Promoting user to Contributor in Virtuoso graph...', end='', flush=True)
            delete_role_query = (sparql_queries.DELETE_ROLE.format(current_app.config['DEFAULTHGRAPH'], user_uri))
            delrole_result = aux.send_data(delete_role_query,
                                           current_app.config['LOCAL_SPARQL'],
                                           current_app.config['VIRTUOSO_USER'],
                                           current_app.config['VIRTUOSO_PASS'])
            # insert role
            insert_role_query = (sparql_queries.INSERT_ROLE.format(current_app.config['DEFAULTHGRAPH'], user_uri))
            insrole_result = aux.send_data(insert_role_query,
                                           current_app.config['LOCAL_SPARQL'],
                                           current_app.config['VIRTUOSO_USER'],
                                           current_app.config['VIRTUOSO_PASS'])
            print('done.', flush=True)
            virtuoso_change = True
            virtuoso_message = 'Promoted user to Contributor in Virtuoso graph.'
        elif user_role == 'Contributor':
            virtuoso_message = 'User with provided ID is already a Contributor in Virtuoso graph.'
            print(virtuoso_message, flush=True)
        elif user_role == 'Admin':
            virtuoso_message = 'Cannot change role of Admin in Virtuoso graph.'
            print(virtuoso_message, flush=True)

        return {'Postgres': '{0} ({1})'.format(postgres_change, postgres_message),
                'Virtuoso': '{0} ({1})'.format(virtuoso_change, virtuoso_message)}, 200

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             params={'id': 'ID of the user to delete'},
             security=['access_token'])
    @w.admin_required
    def delete(self, id):
        """Delete user."""

        # try to get user data
        try:
            user = User.query.get_or_404(id)
        # if there is no user with provided identifier
        except Exception:
            not_found = 'Cannot delete unexistent user with provided ID={0}.'.format(id)
            return {'message': not_found}, 404

        user_id = user.id
        user_role = user.roles
        # ensure that Admins cannot be deleted
        if user_id == 1 or 'Admin' in str(user_role):
            return {'message': 'Insufficient permissions to delete specified user.'}

        # delete user from Postgres
        user_datastore.delete_user(user)
        # commit changes to the database
        db.session.commit()

        # delete user from Virtuoso
        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], user_id)
        user_exists_query = sparql_queries.ASK_USER.format(user_uri)
        ask_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), user_exists_query)
        user_exists = ask_result['boolean']

        if user_exists is True:
            user_delete_query = (sparql_queries.DELETE_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri))
            delete_result = aux.send_data(user_delete_query,
                                          current_app.config['LOCAL_SPARQL'],
                                          current_app.config['VIRTUOSO_USER'],
                                          current_app.config['VIRTUOSO_PASS'])

        return {'message': 'The user {0} has been deleted'.format(str(user.email))}, 200


# NS statistics Routes
# Namespace for NS statistics operations
stats_conf = api.namespace('stats', description='statistics of the database.')


@stats_conf.route("/summary")
class StatsSummary(Resource):
    """ Summary of the data. """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    def get(self):
        """ Count the number of items in Typon """

        # get simple counts for data in the NS
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             (sparql_queries.NS_STATS.format(current_app.config['DEFAULTHGRAPH'])))

        stats = result['results']['bindings']
        if stats != []:
            return stats, 200
        else:
            return {'NOT FOUND': 'Could not retrieve summary info from NS.'}, 404


@stats_conf.route("/species")
class StatsSpecies(Resource):
    """ Summary of all species data. """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    def get(self):
        """ Get species properties values and total number of schemas per species. """

        # count number of schemas per species
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.COUNT_SPECIES_SCHEMAS.format(current_app.config['DEFAULTHGRAPH'])))

        species_schemas_count = result['results']['bindings']
        if len(species_schemas_count) > 0:
            return {'message': species_schemas_count}, 200
        else:
            return {'NOT FOUND': 'NS has no species or species have no schemas.'}, 404


@stats_conf.route("/species/<int:species_id>/totals")
class StatsSpeciesId(Resource):
    """ Summary of one species' data. """

    parser = api.parser()

    parser.add_argument('schema_id',
                        type=str,
                        default=None,
                        help='')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    @w.use_kwargs(api, parser)
    def get(self, species_id, schema_id):
        """ Get schema properties values, total number of loci and total number of alleles for all schemas of a species. """

        precomputed_data_file = os.path.join(os.getcwd(), 'pre-computed-data/totals_{0}.json'.format(str(species_id)))

        with open(precomputed_data_file, 'r') as json_file:
            json_data = json.load(json_file)

        if schema_id is None:
            return json_data
        elif schema_id is not None:
            schema_data = [s for s in json_data['message'] if s['schema']['value'].split('/')[-1] == schema_id]
            return schema_data


@stats_conf.route("/species/<int:species_id>/schema/loci/nr_alleles")
class StatsSpeciesSchemas(Resource):
    """ Summary of one species' data. """

    parser = api.parser()

    parser.add_argument('schema_id',
                        type=str,
                        default=None,
                        help='')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    @w.use_kwargs(api, parser)
    def get(self, species_id, schema_id):
        """ Get the loci and count the alleles for each schema of a particular species. """

        precomputed_data_file = os.path.join(os.getcwd(), 'pre-computed-data/loci_{0}.json'.format(str(species_id)))

        with open(precomputed_data_file, 'r') as json_file:
            json_data = json.load(json_file)

        if schema_id is None:
            return json_data
        elif schema_id is not None:
            schema_data = [s for s in json_data['message'] if s['schema']['value'].split('/')[-1] == schema_id]
            return schema_data


@stats_conf.route("/species/<int:species_id>/schema/<int:schema_id>/modes")
class StatsSpeciesSchemasMode(Resource):
    """ Returns the allele mode sizes per gene. """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    def get(self, species_id, schema_id):
        """ Get the all the loci and calculate the allele mode for a particular schema of a particular species. """

        #
        precomputed_data_file = os.path.join(os.getcwd(), 'pre-computed-data/mode_{0}_{1}.json'.format(species_id, schema_id))

        with open(precomputed_data_file, 'r') as json_file:
            json_data = json.load(json_file)

        return json_data


@stats_conf.route("/species/<int:species_id>/schema/<int:schema_id>/annotations")
class StatsAnnotations(Resource):
    """ Summary of all annotations in NS. """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[])
    def get(self, species_id, schema_id):
        """ Get all the annotations in NS. """

        #
        precomputed_data_file = os.path.join(os.getcwd(), 'pre-computed-data/annotations_{0}_{1}.json'.format(species_id, schema_id))

        with open(precomputed_data_file, 'r') as json_file:
            json_data = json.load(json_file)

        return {"message": json_data}, 200


# Loci Routes

# Namespace for Loci operations
loci_conf = api.namespace('loci', description='loci related operations')

new_loci_model = api.model('NewLociModel',
                           {'prefix': fields.String(required=True,
                                                    description="Alias for the loci"),
                            'locus_ori_name': fields.String(description="Original name of the locus")
                            })

allele_list_model = api.model('AlleleListModel',
                              {'sequence': fields.String(required=False,
                                                         description="Allele DNA sequence"),
                               'species_name': fields.String(required=True,
                                                             description="Name of the species (assumes it exists already)"),
                               'uniprot_url': fields.String(required=False,
                                                            default=False,
                                                            description="Url to the Uniprot result of the allele"),
                               'uniprot_label': fields.String(required=False,
                                                              default=False,
                                                              description="Uniprot label of the allele"),
                               'uniprot_sname': fields.String(required=False,
                                                              default=False,
                                                              description="Uniprot sname of the allele"),
                               'sequence_uri': fields.String(required=False,
                                                             default=False,
                                                             description="URI of an existing sequence"),
                               'enforceCDS': fields.Boolean(required=False,
                                                            default=False,
                                                            description="Enforce CDS"),
                               'input': fields.String(required=False,
                                                      enum=["manual, auto"],
                                                      description="Type of input. Options are manual, auto, link."
                                                                  "Manual presumes that only one allele will be inserted."
                                                                  "Auto presumes that a whole schema is being loaded."
                                                                  "Link is useful to add an existing sequence to a new allele and locus.")
                              })


@loci_conf.route("/list")
class LociList(Resource):
    """ List all loci present on NS """

    parser = api.parser()
    parser.add_argument('prefix',
                        type=str,
                        help="Alias for the loci")

    parser.add_argument('sequence',
                        type=str,
                        location='args',
                        help="Loci sequence")

    parser.add_argument('locus_ori_name',
                        type=str,
                        help="Original locus name")

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @w.admin_contributor_required
    def get(self, **kwargs):
        """ Get a list of all loci on NS """

        prefix = kwargs['prefix']
        sequence = kwargs['sequence']
        locus_ori_name = kwargs['locus_ori_name']
        # Get list of loci that contain the provided DNA sequence
        if sequence is not None:

            # Get sequence from request
            sequence = sequence.upper()

            # Generate hash
            sequence_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            # Query virtuoso
            sequence_uri = '{0}sequences/{1}'.format(current_app.config['BASE_URL'], str(sequence_hash))

            # get all loci that have the provided sequence
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SEQUENCE_LOCI.format(current_app.config['DEFAULTHGRAPH'], sequence_uri)))

            res_loci = result['results']['bindings']

        else:
            # get list of loci, ascending order of locus identifier
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  sparql_queries.SELECT_ALL_LOCI.format(current_app.config['DEFAULTHGRAPH']))

            res_loci = result['results']['bindings']

        if prefix is not None:
            res_loci = [res for res in res_loci if prefix in res['name']['value']]

        if locus_ori_name is not None:
            res_loci = [res for res in res_loci if locus_ori_name in res['original_name']['value']]

        # if result is not empty, stream with context
        if len(res_loci) > 0:
            return Response(stream_with_context(generate('Loci', res_loci)), content_type='application/json', mimetype='application/json')
        # if there are loci with the sequence, filter based on other arguments
        else:
            return {'message': 'None of the loci in the NS meet the filtering criteria.'}, 404


    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Conflict'},
            security=["access_token"])
    @api.expect(new_loci_model)
    @w.admin_contributor_required
    def post(self):
        """Add a new locus."""

        # get user ID
        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()
        prefix = post_data['prefix']
        # check if prefix is not invalid
        if aux.check_prefix(prefix) is False:
            return {'message': 'Please provide a valid prefix.'}, 400

        # count total number of loci in the NS
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.COUNT_TOTAL_LOCI.format(current_app.config['DEFAULTHGRAPH'])))

        number_loci_spec = int(result["results"]["bindings"][0]['count']['value'])

        newLocusId = number_loci_spec + 1

        # name will be something like prefix-000001
        aliases = '{0}-{1}'.format(prefix, '%06d' % (newLocusId,))

        # check if already exists locus with that aliases
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_LOCUS_PREFIX.format(aliases)))

        if result['boolean']:
            return {'message': 'Locus with that prefix already exists.'}, 409

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(newLocusId))

        # try to get locus original FASTA file name
        locus_ori_name = post_data.get('locus_ori_name', False)

        uniprot_name = post_data['UniprotName']
        uniprot_label = post_data['UniprotLabel']
        uniprot_uri = post_data['UniprotURI']
        ns_locus_ori_name = '; typon:originalName "{0}"^^xsd:string.'.format(locus_ori_name) if locus_ori_name not in ['', 'string', False] else ' .'

        # if locus_ori_name then also save the original fasta name
        query2send = (sparql_queries.INSERT_LOCUS.format(current_app.config['DEFAULTHGRAPH'],
                                                         new_locus_url,
                                                         aliases,
                                                         uniprot_name,
                                                         uniprot_label,
                                                         uniprot_uri,
                                                         ns_locus_ori_name))

        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {'message': 'New locus added at {0} with the alias {1}'.format(new_locus_url, aliases),
                    'uri': new_locus_url,
                    'id': str(newLocusId)}, 201
        else:
            return {'message': 'Could not create locus.'}, result.status_code


@loci_conf.route("/<int:loci_id>")
class LociNS(Resource):
    """ Gets a particular locus ID """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
            security=["access_token"])
    @jwt_required
    def get(self, loci_id, **kwargs):
        """Get a particular locus."""

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_LOCUS.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        locus = result['results']['bindings']

        if locus == []:
            return {'message': 'There is no locus with the provided ID.'}, 404
        else:
            return locus


# This endpoint is not using token authentication and the c_user is None
# that means that if the schema is locked no one can access the sequences,
# even the Admin. This has no token because the frontend is working with
# unlocked endpoints.

@loci_conf.route('/<int:loci_id>/fasta')
class LociNSFastaAPItypon(Resource):
    """Loci NS Fasta Resource."""

    # Define extra arguments for requests
    parser = api.parser()

    parser.add_argument('date',
                        type=str,
                        help='provide a date in the format YYYY-MM-DDTHH:MM:SS '
                             'to get the alleles that were uploaded up to the '
                             'provided date.')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
            security=[])
    @w.use_kwargs(api, parser)
    def get(self, loci_id, **kwargs):
        """Gets the FASTA sequence of the alleles from a particular loci from a particular species."""

        c_user = get_jwt_identity()

        locus_uri = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        # check if locus exists
        locus_exists = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                    sparql_queries.ASK_LOCUS.format(locus_uri))
        locus_exists = locus_exists['boolean']
        if locus_exists is False:
            return {'message': 'There is no locus with provided ID.'}

        # get schema that the locus is associated with
        locus_schema_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                          (sparql_queries.SELECT_LOCUS_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], locus_uri)))

        # get schema URI from response
        has_schema = False if locus_schema_query['results']['bindings'] == [] else True
        if has_schema is False:
            return {'message': 'Locus is not associated with any schema.'}

        locus_schema = locus_schema_query['results']['bindings'][0]['schema']['value']

        # determine if schema is locked
        # locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                                     (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], locus_schema)))
        # locking_status = locking_status_query['results']['bindings'][0]['Schema_lock']['value']

        # if schema is locked, enforce condition that only the Admin
        # or the Contributor that administers the schema may get the FASTA sequences
        # if locking_status != 'Unlocked':
        #    if c_user is None:
        #        return {'Not authorized': 'Schema is locked. Cannot download sequences '
        #                                  'that belong to a locus in a locked schema.'}, 403
        #    else:
                # check the role of the user that is trying to access
        #        new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

        #        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
        #                              (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'],
        #                                                                 new_user_url)))

        #        user_role = result['results']['bindings'][0]['role']['value']

        #        allow = enforce_locking(user_role, new_user_url, locus_schema)
        #        if allow[0] == False:
        #            return allow[1], 403

        # get request data
        request_data = request.args
        if 'date' in request_data:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_LOCUS_FASTA_BY_DATE.format(current_app.config['DEFAULTHGRAPH'], locus_uri, request_data['date'])))
        else:
            # find all alleles from the locus and return the sequence and id sorted by id
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_LOCUS_FASTA.format(current_app.config['DEFAULTHGRAPH'], locus_uri)))

        # virtuoso returned an error because request length exceeded maximum value
        # get each allele separately
        if 'Max row length is exceeded when trying to store a string of' in str(result):
            # get locus sequences hashes
            if 'date' in request_data:
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                      (sparql_queries.SELECT_LOCUS_SEQS_BY_DATE.format(current_app.config['DEFAULTHGRAPH'], locus_uri, request_data['date'])))
            else:
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                      (sparql_queries.SELECT_LOCUS_SEQS.format(current_app.config['DEFAULTHGRAPH'], locus_uri)))

            seqs_hashes = result['results']['bindings']
            for s in range(len(seqs_hashes)):
                # get the sequence corresponding to the hash
                result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                       (sparql_queries.SELECT_SEQ_FASTA.format(current_app.config['DEFAULTHGRAPH'], seqs_hashes[s]['sequence']['value'])))

                seqs_hashes[s]['nucSeq'] = result2['results']['bindings'][0]['nucSeq']
        else:
            seqs_hashes = result['results']['bindings']

        return Response(stream_with_context(generate('Fasta', seqs_hashes)), content_type='application/json')


@loci_conf.route('/<int:loci_id>/uniprot')
class LociNSUniprotAPItypon(Resource):
    """Loci Uniprot Resource."""

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
        security=[])
    def get(self, loci_id):
        """Gets Uniprot annotations for a particular loci from a particular species."""

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        # get all uniprot labels and URI from all alleles of the selected locus
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_LOCUS_UNIPROT.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        annotations = result['results']['bindings']

        if annotations == []:
            return {'message': 'No Uniprot annotations found for the provided loci ID.'}, 404

        return Response(stream_with_context(generate('UniprotInfo', annotations)), content_type='application/json')


@loci_conf.route("/<int:loci_id>/alleles")
class LociNSAlleles(Resource):
    """ Gets all alleles from a particular locus ID """

    parser = api.parser()
    parser.add_argument('species_name',
                        type=str,
                        help="Species name")

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
            security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, loci_id, **kwargs):
        """Gets all alleles from a particular locus ID."""

        c_user = get_jwt_identity()

        # Get request data
        request_data = request.args

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        # check if provided loci id exists
        result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   (sparql_queries.ASK_LOCUS.format(new_locus_url)))

        if not result_loci['boolean']:
            return {'message': 'Could not find a locus with provided ID.'}, 404

        # get schema that the locus is associated with
        locus_schema_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                          (sparql_queries.SELECT_LOCUS_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        # get schema URI from response
        locus_schema = locus_schema_query['results']['bindings'][0]['schema']['value']

        # determine if schema is locked
        locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], locus_schema)))
        locking_status = locking_status_query['results']['bindings'][0]['Schema_lock']['value']

        # if schema is locked, enforce condition that only the Admin
        # or the Contributor that locked the schema may get the FASTA sequences
        if locking_status != 'Unlocked':
            # check the role of the user that is trying to access
            new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'],
                                                                     new_user_url)))

            user_role = result['results']['bindings'][0]['role']['value']

            allow = enforce_locking(user_role, new_user_url, locking_status)
            if allow[0] is False:
                return allow[1], 403

        # if user provided a species name, filter the query to contain only that species
        if 'species_name' in request_data:

            species = request_data['species_name']

            # get the taxon id from uniprot, if not found return 404
            uniprot_query = (sparql_queries.SELECT_UNIPROT_TAXON.format(species))

            print('Searching on uniprot...')

            # Check if species exists on uniprot
            result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), uniprot_query)

            uniprot_taxid = result2['results']['bindings']
            if uniprot_taxid != []:
                taxon_uri = uniprot_taxid[0]['taxon']['value']
            else:
                return {'message': 'Species name not found on uniprot, search on http://www.uniprot.org/taxonomy/'}, 404

            # check if species already exists locally (typon)
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.ASK_SPECIES_UNIPROT.format(taxon_uri)))

            if not result['boolean']:
                return {'message': 'Species does not exists in NS.'}, 409

            # determine if locus with provided identifier is associated to provided species
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_LOCUS_SPECIES_ALLELES.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, species)))

        # simply get all alleles for provided locus
        else:
            # get list of alleles from that locus
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_LOCUS_ALLELES.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        locus_info = result['results']['bindings']
        if locus_info == []:
            return {'message': 'Locus with provided ID is not associated to the provided species name.'}, 404
        else:
            return locus_info, 200


    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Conflict'},
            security=["access_token"])
    @api.expect(allele_list_model)
    @w.admin_contributor_required
    def post(self, loci_id):
        """Add alleles to a locus of a species."""

        # get user data
        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()

        # get the species name
        species_name = post_data['species_name']

        # get the DNA sequence
        sequence = (str(post_data['sequence'])).upper()

        new_locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(loci_id))

        # check if locus exists, must exist to be able to add alleles
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_LOCUS.format(new_locus_url)))

        # stop execution if locus does not exist
        if not result['boolean']:
            return {'UNEXISTENT LOCUS': 'Specified locus does not exist.'}, 404

        # get schema that the locus is associated with
        locus_schema_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                          (sparql_queries.SELECT_LOCUS_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        # get schema URI from response
        locus_schema = locus_schema_query['results']['bindings']
        if locus_schema != []:
            locus_schema = locus_schema[0]['schema']['value']
        else:
            return {'message': 'Locus with provided ID is not associated to any schema.'}

        # determine if schema is locked
        locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], locus_schema)))
        locking_status = locking_status_query['results']['bindings'][0]['Schema_lock']['value']

        # if schema is locked, enforce condition that only the Admin
        # or the Contributor that locked the schema may get the FASTA sequences
        if locking_status != 'Unlocked':
            # check the role of the user that is trying to access
            new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], new_user_url)))

            user_role = result['results']['bindings'][0]['role']['value']

            allow = enforce_locking(user_role, new_user_url, locking_status)
            if allow[0] is False:
                return allow[1], 403

        # if the input mode is 'manual' we need to check that the species exists
        if post_data['input'] == 'manual':

            # this is the user URI
            user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

            # check sequence length
            if not aux.check_len(sequence):
                return {'INVALID LENGTH': 'Sequence has invalid length value.'}, 400

            query = (sparql_queries.SELECT_UNIPROT_TAXON.format(species_name))

            # Check if species exists on uniprot
            result_species = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
            try:
                url = result_species['results']['bindings'][0]['taxon']['value']
            except:
                return {'INVALID SPECIES': 'Species name not found on UniProt. Please '
                        'provide a valid species name or search for one on '
                        'http://www.uniprot.org/taxonomy/'}, 404

            # after determining that the species exists, check if the sequence is a valid CDS
            translation_result = aux.translate_dna(sequence, 11, 0)
            if isinstance(translation_result, list):
                protein_sequence = str(translation_result[0][0])
            else:
                return {'INVALID CDS': 'Sequence is not a valid CDS.'}, 418

            # check if sequence already belongs to the locus
            query = (sparql_queries.SELECT_LOCUS_ALLELE.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, sequence))

            # queries with big sequences need different approach
            if len(sequence) > 9000:
                result = aux.send_big_query(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)
            else:
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)

            # if sequence already exists on locus return the allele uri, if not create new sequence
            try:
                new_allele_url = result["results"]["bindings"][0]['alleles']['value']
                return {'REPEATED ALLELE': 'Allele already exists at {0}'.format(new_allele_url)}, 409
            except Exception:
                pass

            # check if sequence exists in uniprot only if the sequence was translatable
            # query the uniprot sparql endpoint and build the RDF with the info on uniprot
            # should not be necessary if properly translated

            # in manual, the allele URI is not provided
            # construct allele URI by counting the total number of alleles in locus
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.COUNT_LOCUS_ALLELES.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

            number_alleles_loci = int(result["results"]["bindings"][0]['count']['value'])

            allele_uri = '{0}/alleles/{1}'.format(new_locus_url, number_alleles_loci+1)

        # Get the uniprot info if it's provided
        elif post_data["input"] == "auto":

            # in auto mode the permissions were previously
            # validated in the load_schema process
            # get token and construct user URI
            user_id = request.headers.get('user_id')
            user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], user_id)

            # in 'auto' mode, alleles URIs are provided by the load schema process
            allele_uri = post_data['sequence_uri']

        # build the id of the sequence by hashing it
        seq_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

        # build the endpoint URI for the sequence
        new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(seq_hash))

        # check if there is a sequence with the same hash
        hash_presence = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                     (sparql_queries.ASK_SEQUENCE_HASH.format(new_seq_url)))

        # check if the sequence that has the same hash is the same or a different DNA sequence
        # only enter here if hash is attributed to a sequence that is in the NS
        if hash_presence['boolean'] is True:

            hashed_sequence = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                           (sparql_queries.ASK_SEQUENCE_HASH_SEQ.format(new_seq_url, sequence)))

            # WARNING: there was a hash collision, two different sequences have the same hash
            if hashed_sequence['boolean'] is False:
                return {'HASH COLLISION': ('Found hash collision. New sequence has same hash as sequence at URI {0}.\n{1}'.format(new_seq_url, sequence))}, 409

        # if the sequence already exists in the NS
        if hash_presence['boolean']:
            # celery task
            task = add_allele.apply(args=[new_locus_url, species_name, loci_id, user_url, new_seq_url, False, sequence, allele_uri])

        # if there is no sequence with that hash
        else:
            # celery task
            task = add_allele.apply(args=[new_locus_url, species_name, loci_id, user_url, new_seq_url, True, sequence, allele_uri])

        # get POST message
        process_result = task.result

        return process_result


@loci_conf.route("/<int:loci_id>/alleles/<int:allele_id>")
class AlleleNSAPItypon(Resource):
    """ Allele List Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
            security=["access_token"])
    @jwt_required
    def get(self, loci_id, allele_id):
        """ Gets a particular allele from a particular loci """

        new_allele_url = '{0}loci/{1}/alleles/{2}'.format(current_app.config['BASE_URL'], str(loci_id), str(allele_id))

        # check if provided loci id exists
        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))
        result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   sparql_queries.ASK_LOCUS.format(new_locus_url))

        if not result_loci['boolean']:
            return {'UNEXISTENT LOCUS': 'Specified locus does not exist.'}, 404

        # get information on allele, sequence, submission date, id and number of isolates with this allele
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_ALLELE_INFO.format(current_app.config['DEFAULTHGRAPH'], new_allele_url)))

        allele_info = result['results']['bindings']
        if allele_info == []:
            return {'message': 'No allele found with the provided id.'}, 404
        else:
            return allele_info


# Schema Routes

# Namespace
species_conf = api.namespace('species', description='Species related operations.')

species_model = api.model('SpeciesModel',
                          {'name': fields.String(required=True,
                                                 description='Name of the species to add.')
                          })

schema_model = api.model('SchemaModel',
                         {'name': fields.String(required=True,
                                                description="Name of the schema to add."),
                          'bsr': fields.String(required=True,
                                               description="Blast Score Ratio used to create the schema."),
                          'prodigal_training_file': fields.String(required=True,
                                                                  description="Link to the Prodigal training file used to create the schema"),
                          'translation_table': fields.String(required=True,
                                                             description="Translation table used to create the schema."),
                          'minimum_locus_length': fields.String(required=True,
                                                                description="Minimum locus length used to create the schema."),
                          'size_threshold': fields.String(required=True,
                                                          description="Size variation threshold value."),
                          'chewBBACA_version': fields.String(required=True,
                                                             description="Version of chewBBACA used to create the schema."),
                          'word_size': fields.String(required=True,
                                                     description='Word size used for the clustering process.'),
                          'cluster_sim': fields.String(required=True,
                                                       description='Percentage of shared k-mers considered to decide if a sequence should be added to a cluster.'),
                          'representative_filter': fields.String(required=True,
                                                                 description='Percentage of k-mers shared with the cluster '
                                                                              'representative considered to exclude sequences '
                                                                              'that are very similar to the representative.'),
                          'intraCluster_filter': fields.String(required=True,
                                                               description='Percentage of k-mers shared between non-representative sequences in a cluster that'
                                                                           ' will be considered to exclude sequences that are very similar with other '
                                                                           'non-representative sequences in the cluster.')
                         })

schema_lock_model = api.model('SchemaLockModel',
                              {'action': fields.String(required=True,
                                                       description='Action to perform (lock or unlock).'),
                               })

schema_modification_model = api.model('SchemaModModel',
                                      {'date': fields.String(required=True,
                                                             description='Last modification date for the schema.'),
                                       })

schema_loci_model = api.model('SchemaLociModel',
                              {'loci_id': fields.String(required=True,
                                                        description="Id of the loci")
                               })

loci_list_model = api.model('LociListModel',
                            {'locus_id': fields.String(required=True,
                                                       description="ID of the locus")
                             })

isolate_model = api.model("IsolateModel", {
    'ST': fields.String(required=False, description="ST for traditional 7 genes MLST"),
    'accession': fields.String(required=False, description="Accession URL to reads"),
    'country': fields.String(required=False, description="Country where the isolate was collected."),
    'strainId': fields.String(required=False, description="Strain identifier"),
    'collection_date': fields.String(required=False, description="The date on which the sample was collected"),
    'host': fields.String(required=False, description='The natural (as opposed to laboratory) host to the organism from which the sample was obtained.\
                                                       Use the full taxonomic name, eg, "Homo sapiens".'),
    'host_disease': fields.String(required=False, description="DOID ID , e.g. salmonellosis has ID 0060859. \
                                                               Controlled vocabulary, http://www.disease-ontology.org/"),
    'lat': fields.String(required=False, description="Latitude information in the WGS84 geodetic reference datum, e.g 30.0000"),
    'long': fields.String(required=False, description="Longitude information in the WGS84 geodetic reference datum, e.g 30.0000"),
    'isol_source': fields.String(required=False, description="Describes the physical, environmental and/or local geographical source \
                                                                 of the biological sample from which the sample was derived.")
})

allele_model = api.model('AlleleModel',
                         {'locus_id': fields.String(required=True,
                                                    description="ID of the locus"),
                          'allele_id': fields.String(required=True,
                                                     description="The ID of the allele in NS")
                          })

profile_model = api.model('ProfileModel',
                          {'profile': fields.Raw(required=True,
                                                 description="AlleleCall profile"),
                           'headers': fields.Raw(required=True,
                                                 description="Headers of the profile file")
                           })


@species_conf.route('/list')
class SpeciesListAPItypon(Resource):
    """ Species List Resource"""

    # Define extra arguments for requests
    parser = api.parser()

    parser.add_argument('species_name',
                        type=str,
                        help='Name of the species')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    # @jwt_required
    def get(self, **kwargs):
        """ Get a list of all species on Typon """

        # check if user provided a species name
        species_name = kwargs['species_name']

        # get single species or full species list
        # returns empty results if species does not exist in the NS
        query_end = ' typon:name "{0}"^^xsd:string. '.format(species_name) if species_name is not None else ' typon:name ?name. '
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SPECIES.format(current_app.config['DEFAULTHGRAPH'],
                                                                    query_end)))

        species_list = result['results']['bindings']
        if species_list == []:
            return {'NOT FOUND': 'Species does not exists in the NS.'}, 404
        else:
            return (result['results']['bindings'])

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        409: 'Species already exists',
                        404: 'Species name not found on uniprot'},
             security=["access_token"])
    @api.expect(species_model, validate=True)
    @w.admin_required
    def post(self):
        """Add a new species to Typon."""

        # get user data
        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()

        # get taxon name from the post data
        taxon_name = str(post_data['name'])
        # get total number of taxa already on the graph
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.COUNT_TAXON.format(current_app.config['DEFAULTHGRAPH'])))

        number_taxa = int(result["results"]["bindings"][0]['count']['value'])

        # get the taxon id from uniprot, if not found return 404
        uniprot_query = sparql_queries.SELECT_UNIPROT_TAXON.format(taxon_name)

        print('Searching on uniprot..', flush=True)

        # check if species exists on uniprot
        result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), uniprot_query)
        try:
            uniprot_url = result2["results"]["bindings"][0]['taxon']['value']
        except:
            return {'message': 'Species name not found on uniprot. Please provide a valid species name or search at http://www.uniprot.org/taxonomy/'}, 404

        # check if species already exists locally (typon)
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SPECIES_UNIPROT.format(uniprot_url)))

        if result['boolean']:
            return {'message': 'Species already added to the NS.'}, 409

        # species exists on uniprot, everything ok to create new species
        new_spec_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(number_taxa+1))

        data2send = (sparql_queries.INSERT_SPECIES.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, uniprot_url, taxon_name))

        result = aux.send_data(data2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {'message': '{0} added to the NS.'.format(taxon_name)}, 201
        else:
            return {'message': 'Could not add new taxon to the NS.',
                    'error': result.text}, result.status_code


@species_conf.route('/<int:species_id>')
class SpeciesAPItypon(Resource):
    """ Species Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id):
        """ Returns the species corresponding to the given id """

        url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        # get species name and its schemas
        # returns empty list if there is no species with provided identifier
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SPECIES_AND_SCHEMAS.format(current_app.config['DEFAULTHGRAPH'], url)))

        species_info = result['results']['bindings']
        if species_info == []:
            return {'NOT FOUND': 'No species found with the provided ID.'}, 404
        else:
            return species_info


@species_conf.route('/<int:species_id>/profiles')
class SpeciesProfiles(Resource):
    """ AlleleCall Profiles Resources
    """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    @api.expect(profile_model)
    @jwt_required
    def post(self, species_id):
        """ Add an allele call profile"""

        # get user data
        c_user = get_jwt_identity()

        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))

            if not result['boolean']:
                return {"message": "Not authorized, admin only"}, 403

        except:
            return {"message": "Not authorized, admin only"}, 403

        # get post data
        post_data = request.get_json()

        if not post_data:
            return {"message": "No profile provided"}, 400

        profile_dict = post_data["profile"]
        headers = post_data["headers"]

        species_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))

        dict_genes = {}

        # get all locus from the species and their respective name, to compare to the name of the locus from the profile the user sent
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('select (str(?originalName) as ?originalName) ?locus '
                               'from <{0}> '
                               'where '
                               '{{?locus a typon:Locus; typon:isOfTaxon <{1}>; typon:originalName ?originalName. }}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                                                                            species_url)))

        for gene in result["results"]["bindings"]:
            dict_genes[str(gene['originalName']['value'])] = str(gene['locus']['value'])

        genome_name = next(iter(profile_dict))

        # create the new isolate id for the uri
        nameWdata2hash = genome_name + str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
        new_isolate_id = hashlib.sha256(nameWdata2hash.encode('utf-8')).hexdigest()

        rdf_2_ins = ('PREFIX typon: <http://purl.phyloviz.net/ontology/typon#> \nINSERT DATA IN GRAPH <{0}> {{\n'.format(current_app.config['DEFAULTHGRAPH']))

        isolateUri = "{0}/isolates/{1}".format(species_url, str(new_isolate_id))

        # Check if isolate already exists
        check_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                    ('ASK where {{ <{0}> a typon:Isolate }}'.format(isolateUri)))

        if not check_result['boolean']:
            return {"message": "Isolate already exists"}, 409

        rdf_2_ins += ('<{0}> a typon:Isolate;\ntypon:name "{1}"^^xsd:string; typon:sentBy <{2}>;'
                      ' typon:dateEntered "{3}"^^xsd:dateTime; typon:isFromTaxon <{4}>;'.format(isolateUri,
                                                                                                genome_name,
                                                                                                new_user_url,
                                                                                                str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                                                species_url))
        i = 0
        hasAlleles = 0

        # build the rdf with all alleles
        while i < len(profile_dict[genome_name]):
            gene = headers[i+1]

            # get the allele id
            try:
                allele = int(profile_dict[genome_name][i])

            except:
                i += 1
                continue

            # get the locus uri
            try:
                loci_uri = dict_genes[headers[i+1]]
            except:
                return {"message": ("{0} locus was not found, profile not uploaded".format(str(headers[i+1])))}, 404

            # check if allele exists
            allele_uri = "{0}/alleles/{1}".format(loci_uri, str(allele))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('ASK where {{ <{0}> a typon:Locus; typon:hasDefinedAllele <{1}> }}'.format(loci_uri, allele_uri)))
            if result['boolean']:

                rdf_2_ins += '\ntypon:hasAllele <{0}>;'.format(allele_uri)
                hasAlleles += 1

            i += 1

        # if the genome has alleles, send the rdf
        if hasAlleles > 0:

            # remove last semicolon from rdf and close the brackets
            rdf_2_ins = rdf_2_ins[:-1]

            rdf_2_ins += ".}"                

            # add to the queue to send the profile
            task = add_profile.apply(args=[rdf_2_ins])

            process_result = task.result

            process_ran = task.ready()
            process_sucess = task.status

            if process_ran and process_sucess == "SUCCESS":
                pass
            else:
                return "status: " + " run:"

            process_result = task.result
            print(process_result)
            process_result_status_code = int(process_result[-1])

            print(genome_name, str(process_result_status_code))

            if process_result_status_code > 201:
                return {"message": "Profile not uploaded, try again "}, process_result_status_code
            else:
                return {"message": "Profile successfully uploaded at " + isolateUri}, process_result_status_code

        else:
            return {"message": "Profile not uploaded, no alleles to send at {0}".format(isolateUri)}, 200


@species_conf.route('/<int:species_id>/schemas')
class SchemaListAPItypon(Resource):
    """ Schema List Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id):
        """ Get the schemas for a particular species ID """

        species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        # check if there is a species with provided identifier
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SPECIES_NS.format(species_url))

        species_exists = result['boolean']
        if species_exists is False:
            return {'NOT FOUND': 'There is no species in the NS with the provided ID.'}, 404

        # if there is a species with the ID, get all schemas for that species
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SPECIES_SCHEMAS.format(current_app.config['DEFAULTHGRAPH'], species_url)))

        species_schemas = result['results']['bindings']
        if species_schemas == []:
            return {'NOT FOUND': 'There are no schemas for that species.'}, 404
        else:
            return species_schemas, 200

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=["access_token"])
    @api.expect(schema_model, validate=True)
    @w.admin_contributor_required
    def post(self, species_id):
        """ Adds a new schema for a particular species ID """

        c_user = get_jwt_identity()
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

        # get post data
        post_data = request.get_json()

        # schema name
        name = str(post_data['name'])
        # blast score ratio
        bsr = str(post_data['bsr'])
        # prodigal training file
        ptf = str(post_data['prodigal_training_file'])
        # translation table
        translation_table = str(post_data['translation_table'])
        # minimum locus length
        min_locus_len = str(post_data['minimum_locus_length'])
        # size threshold
        size_threshold = str(post_data['size_threshold'])
        # chewBBACA_version
        chewie_version = str(post_data['chewBBACA_version'])
        # clustering word_size
        word_size = str(post_data.get('word_size', 'na'))
        # clustering cluster similarity threshold
        cluster_sim = str(post_data.get('cluster_sim', 'na'))
        # clustering representative similarity exclusion threshold
        rep_filter = str(post_data.get('representative_filter', 'na'))
        # clustering intra cluster similarity exclusion threshold
        intra_filter = str(post_data.get('intraCluster_filter', 'na'))
        # schema description
        description = post_data.get('SchemaDescription', 'na')
        # schema locking property
        session_token = request.headers['Authorization']
        schema_lock = new_user_url

        if '' in (name, bsr, ptf, translation_table, min_locus_len,
                  chewie_version, word_size, cluster_sim, rep_filter,
                  intra_filter):

            return {'message': 'No schema parameters specified.'}, 406

        # check if species exists
        species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SPECIES_NS.format(species_url))

        if not result['boolean']:
            return {'NOT FOUND': 'Species does not exist'}, 404

        # check if a schema already exists with this name for this species
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_DESCRIPTION.format(species_url, name)))
        if result['boolean']:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], species_url, name)))

            schema_url = result["results"]["bindings"][0]['schema']['value']

            return {'message': 'schema with that name already exists {0}'.format(schema_url)}, 409

        # count number of schemas on the server for the uri build and send data to server
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.COUNT_SCHEMAS.format(current_app.config['DEFAULTHGRAPH'], species_url)))

        number_schemas = int(result['results']['bindings'][0]['count']['value'])

        # Create the uri for the new schema
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(number_schemas + 1))

        # The SPARQL query to send to Typon
        insertion_date = 'singularity'
        query2send = (sparql_queries.INSERT_SCHEMA.format(current_app.config['DEFAULTHGRAPH'],
                                                          new_schema_url, species_url,
                                                          new_user_url, name,
                                                          bsr, chewie_version,
                                                          ptf, translation_table,
                                                          min_locus_len, size_threshold,
                                                          word_size, cluster_sim,
                                                          rep_filter, intra_filter,
                                                          insertion_date, insertion_date,
                                                          schema_lock, description))

        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {'message': 'A new schema for {0} was created sucessfully'.format(species_url),
                    "url": new_schema_url}, 201
        else:
            return {'message': 'Could not add new schema to the NS.'}, result.status_code


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>')
class SchemaAPItypon(Resource):
    """ Schema List Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id, schema_id):
        """Return a particular schema for a particular species"""

        user_id = get_jwt_identity()

        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], user_id)

        # check if there is a species with provided identifier
        species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SPECIES_NS.format(species_url))

        species_exists = result['boolean']
        if species_exists is False:
            return {'NOT FOUND': 'There is no species in the NS with the provided ID.'}, 404

        # construct schema URI
        new_schema_url = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                             species_id,
                                                             schema_id)

        # check if schema is deprecated
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_DEPRECATED.format(new_schema_url)))
        if result['boolean'] is True:
            # check user permissions, Admin can access deprecated schemas
            user_info = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                     sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri))
            user_role = user_info['results']['bindings'][0]['role']['value']

            if user_role != 'Admin':
                return {'message': 'Schema is deprecated.'}, 403

        # get schema info
        schema_info = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   (sparql_queries.SELECT_SPECIES_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))

        schema_properties = schema_info['results']['bindings']

        locking_status = schema_properties[0]['Schema_lock']['value']
        schema_properties[0]['Schema_lock']['value'] = 'Locked' if locking_status != 'Unlocked' else locking_status

        if schema_properties == []:
            return {'NOT FOUND': 'Could not find a schema with provided ID.'}, 404
        else:
            return schema_properties

    # it doesnt delete, it just adds an attribute typon:deprecated  "true"^^xsd:boolean to that part of the schema, 
    # the locus is just "removed" for the specific schema!!

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.admin_required
    def delete(self, species_id, schema_id):
        """ Deprecates a particular schema for a particular species """

        c_user = get_jwt_identity()

        new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

        # check if schema exists
        new_schema_url = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_OWNERSHIP.format(new_schema_url, new_user_url)))

        if not result['boolean']:
            return {'message': 'Could not find schema with provided ID or schema is not administrated by current user.'}, 404

        # add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
        query2send = (sparql_queries.INSERT_SCHEMA_DEPRECATE.format(current_app.config['DEFAULTHGRAPH'], new_schema_url))

        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {'message': 'Schema sucessfully removed.'}, 201
        else:
            return {'message': 'Sum Thing Wong.'}, result.status_code


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/administrated')
class SchemaAdminAPItypon(Resource):
    """
    """

    # determine if current user administrates the schema
    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument',
                         500: 'Internal Server Error',
                         403: 'Unauthorized',
                         401: 'Unauthenticated',
                         404: 'Not Found'},
             security=["access_token"])
    @w.admin_contributor_required
    def get(self, species_id, schema_id):
        """Determine if current user administrates schema with provided ID."""

        c_user = get_jwt_identity()

        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], c_user)

        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         species_id,
                                                         schema_id)

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_OWNERSHIP.format(schema_uri, user_uri)))

        administer = result['boolean']

        return administer


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/modified')
class SchemaModDateAPItypon(Resource):
    """
    """

    # get last modification date for the schema
    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id, schema_id):
        """Get last modification date of the schema with the given identifier."""

        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         species_id,
                                                         schema_id)

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        result_data = result['results']['bindings']
        if len(result_data) == 0:
            return {'Not found': 'Could not find a schema with provided ID.'}, 404

        schema_name = result_data[0]['name']['value']
        last_modified = result_data[0]['last_modified']['value']

        return ('Schema {0} ({1}) last modified in: {2}.'.format(schema_id, schema_name, last_modified))

    # change last modification date for the Schema
    # also changes the insertion date if it corresponds to the value inserted when the schema is created in the graph.
    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @api.expect(schema_modification_model, validate=True)
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """Change the last modification date of the schema with the given identifier."""

        c_user = get_jwt_identity()

        new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], new_user_url)))

        # create schema URI
        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         str(species_id),
                                                         str(schema_id))

        user_role = result['results']['bindings'][0]['role']['value']

        # get schema locking status
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        # get post data
        post_data = request.get_json()

        result_data = result['results']['bindings']
        if len(result_data) == 0:
            return {'Not found': 'Could not find a schema with provided ID.'}, 404

        lock_state = result_data[0]['Schema_lock']['value']
        permission = enforce_locking(user_role, new_user_url, lock_state)
        if permission[0] is not True:
            return permission[1], 403

        date = post_data['date']
        # check if date is in a valid date format
        try:
            dt.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
        except ValueError:
            return {'Invalid Argument': 'Invalid date format. Please provide a date in format Y-M-DTH:M:S'}, 400

        # get schema info
        schema_info = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   (sparql_queries.SELECT_SPECIES_SCHEMA.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        schema_properties = schema_info['results']['bindings']

        dateEntered = schema_properties[0]['dateEntered']['value']

        # first delete current modification date value
        delprop_query = (sparql_queries.DELETE_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'],
                                                                  schema_uri, 'last_modified'))

        delprop_result = aux.send_data(delprop_query,
                                       current_app.config['LOCAL_SPARQL'],
                                       current_app.config['VIRTUOSO_USER'],
                                       current_app.config['VIRTUOSO_PASS'])

        # insert new value
        query2send = (sparql_queries.INSERT_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'], schema_uri, 'last_modified', date))

        last_modified_result = aux.send_data(query2send,
                                             current_app.config['LOCAL_SPARQL'],
                                             current_app.config['VIRTUOSO_USER'],
                                             current_app.config['VIRTUOSO_PASS'])

        # check insertion date
        if dateEntered == 'singularity':
            delprop_query = (sparql_queries.DELETE_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'],
                                                                      schema_uri, 'dateEntered'))

            delprop_result = aux.send_data(delprop_query,
                                           current_app.config['LOCAL_SPARQL'],
                                           current_app.config['VIRTUOSO_USER'],
                                           current_app.config['VIRTUOSO_PASS'])

            # insert new value
            query2send = (sparql_queries.INSERT_SCHEMA_DATE.format(current_app.config['DEFAULTHGRAPH'], schema_uri, 'dateEntered', date))

            date_entered_result = aux.send_data(query2send,
                                                current_app.config['LOCAL_SPARQL'],
                                                current_app.config['VIRTUOSO_USER'],
                                                current_app.config['VIRTUOSO_PASS'])

        if last_modified_result.status_code in [200, 201]:
            return {'message': 'Changed schema modification date.'}, 201
        else:
            return {'message': 'Could not change schema modification date.'}, last_modified_result.status_code


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/lock')
class SchemaLockAPItypon(Resource):
    """Schema locking property Resource"""

    # get locking state for the Schema
    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id, schema_id):
        """Get the locking state of the schema with the given identifier."""

        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         str(species_id),
                                                         str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        result_data = result['results']['bindings']
        if len(result_data) == 0:
            return {'Not found': 'Could not find a schema with provided ID.'}, 404

        schema_name = result_data[0]['name']['value']
        locking_value = result_data[0]['Schema_lock']['value']

        if locking_value == 'Unlocked':
            return ('Schema {0} ({1}) status: *unlocked*.'.format(str(schema_id), schema_name))
        else:
            return ('Schema {0} ({1}) status: [locked].'.format(str(schema_id), schema_name))

    # change locking state for the Schema
    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @api.expect(schema_lock_model, validate=True)
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """Change the locking state of the schema with the given identifier."""

        c_user = get_jwt_identity()

        new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], new_user_url)))

        # create schema URI
        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         str(species_id),
                                                         str(schema_id))

        user_role = result['results']['bindings'][0]['role']['value']

        # get schema locking status
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        # get post data
        post_data = request.get_json()

        result_data = result['results']['bindings']
        if len(result_data) == 0:
            return {'Not found': 'Could not find a schema with provided ID.'}, 404

        lock_state = result_data[0]['Schema_lock']['value']

        action = post_data['action']
        if action == 'lock':
            lock_token = new_user_url
            if lock_state == 'Unlocked':
                # first delete Schema_lock property value
                delprop_query = (sparql_queries.DELETE_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'],
                                                                          schema_uri))

                delprop_result = aux.send_data(delprop_query,
                                               current_app.config['LOCAL_SPARQL'],
                                               current_app.config['VIRTUOSO_USER'],
                                               current_app.config['VIRTUOSO_PASS'])

                # insert new value
                query2send = (sparql_queries.INSERT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri, lock_token))

                result = aux.send_data(query2send,
                                       current_app.config['LOCAL_SPARQL'],
                                       current_app.config['VIRTUOSO_USER'],
                                       current_app.config['VIRTUOSO_PASS'])
            else:
                return {'message': 'Schema already locked.'}, 201

        elif action == 'unlock':
            unlock_token = 'Unlocked'
            if lock_state == 'Unlocked':
                return {'message': 'Schema already unlocked.'}, 201
            else:
                # verify user identity and role
                permission = enforce_locking(user_role, new_user_url, lock_state)
                if permission[0] is not True:
                    return permission[1], 403

                # first delete Schema_lock property value
                delprop_query = (sparql_queries.DELETE_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'],
                                                                          schema_uri))
                delprop_result = aux.send_data(delprop_query,
                                               current_app.config['LOCAL_SPARQL'],
                                               current_app.config['VIRTUOSO_USER'],
                                               current_app.config['VIRTUOSO_PASS'])

                # insert new value
                query2send = (sparql_queries.INSERT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri, unlock_token))

                result = aux.send_data(query2send,
                                       current_app.config['LOCAL_SPARQL'],
                                       current_app.config['VIRTUOSO_USER'],
                                       current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {'message': 'Schema sucessfully locked/unlocked.'}, 201
        else:
            return {'message': 'Could not lock/unlock schema.'}, result.status_code


# Prodigal training files Routes
@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/ptf')
class SchemaPtfAPItypon(Resource):
    """ Prodigal training files Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[""])
    def get(self, species_id, schema_id):
        """Download the Prodigal training file for the specified schema."""

        # create schema URI
        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         str(species_id),
                                                         str(schema_id))

        # get the prodigal training file hash
        ptf_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 (sparql_queries.SELECT_SCHEMA_PTF.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        ptf_hash = ptf_query['results']['bindings'][0]['ptf']['value']

        root_dir = os.path.abspath(current_app.config['SCHEMAS_PTF'])

        return send_from_directory(root_dir, ptf_hash, as_attachment=True)

    # upload schema Prodigal training file
    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """Upload the Prodigal training file for the specified schema."""

        root_dir = os.path.abspath(current_app.config['SCHEMAS_PTF'])
        request_data = request.get_json()

        filename = request_data['filename']
        file_content = request_data['content']

        # check if training file hash is the one associated with the schema
        # create schema URI
        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'],
                                                         str(species_id),
                                                         str(schema_id))

        # get the prodigal training file hash
        ptf_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 (sparql_queries.SELECT_SCHEMA_PTF.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))

        ptf_hash = ptf_query['results']['bindings'][0]['ptf']['value']
        if filename != ptf_hash:
            return {'Not acceptable': 'Provided training file is not the one associated with the specified schema.'}, 406

        # list training files in the NS
        ns_ptfs = os.listdir(root_dir)
        if filename in ns_ptfs:
            return {'Conflict': 'Provided training file is already in the NS.'}, 409

        file_path = os.path.join(root_dir, filename)

        with open(file_path, 'wb') as ptf:
            # file was decoded for upload so we have to encode
            # with ISO-8859-1 to return to original format
            ptf.write(file_content.encode(encoding='ISO-8859-1'))

        return {'OK': 'Received new Prodigal training file.'}, 201


# Compressed schemas Routes
@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/zip')
class SchemaZipAPItypon(Resource):
    """ Compressed schemas Routes """

    parser = api.parser()

    parser.add_argument('request_type',
                        type=str,
                        default='check',
                        help='',
                        choices=['check', 'download'])

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=[""])
    @w.use_kwargs(api, parser)
    def get(self, species_id, schema_id, request_type):
        """Checks existence of or downloads zip archive of the specified schema."""

        # check if schema is locked
        schema_uri = os.path.join(current_app.config['BASE_URL'], 'species/{0}/schemas/{1}'.format(species_id, schema_id))
        locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))
        locking_status = locking_status_query['results']['bindings']
        if len(locking_status) == 0:
            return {'Not found': 'Could not find a schema with specified ID.'}, 404

        locking_status = locking_status[0]['Schema_lock']['value']

        if locking_status != 'Unlocked':
            return {'Unauthorized': 'Schema is locked.'}, 403

        zip_prefix = '{0}_{1}'.format(species_id, schema_id)

        root_dir = os.path.abspath(current_app.config['SCHEMAS_ZIP'])

        schema_zip = [z for z in os.listdir(root_dir) if z.startswith(zip_prefix) is True]
        if len(schema_zip) == 1 and '.zip' in schema_zip[0]:
            if request_type == 'check':
                return {'zip': schema_zip}, 200
            elif request_type == 'download':
                return send_from_directory(root_dir, schema_zip[0], as_attachment=True)
        elif (len(schema_zip) == 1 and '.zip' not in schema_zip[0]) or len(schema_zip) > 1:
            return {'Working': 'A new compressed version of the schema is being created. Please try again later.'}, 403
        elif len(schema_zip) == 0:
            return {'Not found': 'Could not find a compressed version of specified schema.'}, 404

    # send post to compress single schema
    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """Give the order to compress a single schema that exists in the NS."""

        user_id = get_jwt_identity()

        user_uri = '{0}users/{1}'.format(current_app.config['BASE_URL'], user_id)

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], user_uri)))
        user_role = result['results']['bindings'][0]['role']['value']

        # check if schema is locked
        schema_uri = os.path.join(current_app.config['BASE_URL'], 'species/{0}/schemas/{1}'.format(species_id, schema_id))
        locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], schema_uri)))
        locking_status = locking_status_query['results']['bindings']
        if len(locking_status) == 0:
            return {'Not found': 'Could not find a schema with specified ID.'}, 404

        # if the schema is locked only the Admin or the Contributor
        # that locked the schema may give the order
        locking_status = locking_status[0]['Schema_lock']['value']
        if locking_status != 'Unlocked':
            permission = enforce_locking(user_role, user_uri, locking_status)
            if permission[0] is not True:
                return permission[1], 403

        # add '&' at the end so that it will not wait for process to finish
        compress_cmd = ('python schema_compressor.py -m single '
                        '--sp {0} --sc {1} &'.format(species_id, schema_id))
        os.system(compress_cmd)

        return {'OK': 'Schema will be compressed by the NS.'}, 201


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/loci')
class SchemaLociAPItypon(Resource):
    """ Schema Loci Resource """

    # Define extra arguments for requests
    parser = api.parser()

    parser.add_argument('date',
                        type=str,
                        help='provide a date in the format YYYY-MM-DDTHH:MM:SS to get the alleles that were uploaded after that defined date')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=['access_token'])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, schema_id, **kwargs):
        """ Returns the loci of a particular schema from a particular species """

        c_user = get_jwt_identity()

        # get request data
        request_data = request.args

        # check if there is a species with provided identifier
        species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SPECIES_NS.format(species_url))

        species_exists = result['boolean']
        if species_exists is False:
            return {'NOT FOUND': 'There is no species in the NS with the provided ID.'}, 404

        # check if schema exists or is deprecated
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                              (sparql_queries.ASK_SCHEMA_DEPRECATED2.format(new_schema_url)))

        if result['boolean']:
            return {'message': 'Schema not found or deprecated.'}, 404

        # if date is provided the request returns the alleles that were added after that specific date for all loci
        # else the request returns the list of loci
        # a correct request returns also the server date at which the request was done
        if 'date' in request_data:

            # query all alleles for the loci of the schema since a specific date, sorted from oldest to newest (limit of max 50k records)
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SCHEMA_LATEST_ALLELES.format(current_app.config['DEFAULTHGRAPH'], new_schema_url, request_data['date'])))

            new_alleles = result['results']['bindings']
            number_of_alleles = len(new_alleles)

            # if there are no new alleles
            if number_of_alleles < 1:

                response = Response(stream_with_context(generate('newAlleles', new_alleles)),
                                    content_type='application/json')
                # if there are no alleles, return server date information
                response.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))

                return response
            else:
                # get the allele with the latest date from all retrieved alleles
                latest_allele = new_alleles[-1]

                # get allele date
                latest_datetime = latest_allele['date']['value']

                response = Response(stream_with_context(generate('newAlleles', new_alleles)),
                                    content_type='application/json')
                response.headers.set('Last-Allele', latest_datetime)
                if number_of_alleles >= 10000:
                    response.headers.set('All-Alleles-Returned', False)
                else:
                    response.headers.set('Server-Date',
                                         str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
                    response.headers.set('All-Alleles-Returned', True)

                return response

        # if no date provided, query for all loci for the schema
        else:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))

            # check if schema has loci
            loci_list = result['results']['bindings']
            if loci_list == []:
                return {'message': 'Schema exists but does not have loci yet.'}, 200

            # return all loci in stream mode
            latestDatetime = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
            r = Response(stream_with_context(generate('Loci', loci_list)), content_type='application/json')
            r.headers.set('Server-Date', latestDatetime)

            return r

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Locus already on schema'},
             security=["access_token"])
    @api.expect(schema_loci_model)
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """Add loci to a particular schema of a particular species."""

        # get user id
        c_user = get_jwt_identity()

        # check if schema exists
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SCHEMA_DEPRECATED2.format(new_schema_url))

        if result['boolean']:
            return {'message': 'Schema not found.'}, 404

        # determine if schema is locked
        locking_status_query = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.SELECT_SCHEMA_LOCK.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))
        locking_status = locking_status_query['results']['bindings'][0]['Schema_lock']['value']

        # if schema is locked, enforce condition that only the Admin
        # or the Contributor that locked the schema may get the FASTA sequences
        if locking_status != 'Unlocked':
            # check the role of the user that is trying to access
            new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_USER.format(current_app.config['DEFAULTHGRAPH'], new_user_url)))

            user_role = result['results']['bindings'][0]['role']['value']
            allow = enforce_locking(user_role, new_user_url, locking_status)
            if allow[0] is False:
                return allow[1], 403

        # get post data
        request_data = request.get_json()

        # check if locus exists
        loci_id = str(request_data['loci_id'])
        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('ASK where {{ <{0}> a typon:Locus}}'.format(new_locus_url)))

        if not result['boolean']:
            return {'message': 'Could not find locus with provided ID.'}, 404

        # check if locus already exists on schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_LOCUS.format(new_schema_url, new_locus_url)))

        if result['boolean']:
            return {"message": "Locus already on schema",
                    "locus_url": new_locus_url}, 409

        # get the number of loci on schema and build the uri based on that number+1 , using a celery queue
        task = add_locus_schema.apply(args=[new_schema_url, new_locus_url])

        process_result = task.result

        process_ran = task.ready()
        process_sucess = task.status

        if process_ran and process_sucess == "SUCCESS":
            pass
        else:
            return {"status: " + process_sucess + " run:" + process_ran}, 400

        # celery results
        new_allele_url = process_result[0]
        process_result_status_code = int(process_result[-1])

        if process_result_status_code > 201:
            # check if process was sucessfull
            return {'message': 'Could not add locus to schema.'}, process_result_status_code
        else:
            return new_allele_url, process_result_status_code

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @w.admin_required
    def delete(self, species_id, schema_id):
        """Delete loci to a particular schema of a particular species."""

        # it doesnt delete, it just adds an attribute typon:deprecated  "true"^^xsd:boolean to that part of the schema,
        # the locus is just "removed" for the specific schema!!!

        c_user = get_jwt_identity()

        # get post data
        request_data = request.args

        try:
            request_data["loci_id"]

        except:
            return {"message": "No valid id for loci provided"}, 404

        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

        # check if schema exists
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        # this will return FALSE for Admin if the schema was uploaded by a Contributor?
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>;'
                               ' typon:deprecated  "true"^^xsd:boolean }}'.format(new_schema_url, new_user_url)))

        if not result['boolean']:
            return {"message": "Schema not found or schema is not yours"}, 404

        # check if locus exists
        new_locus_url = "{0}species/{1}/loci/{2}".format(current_app.config['BASE_URL'], str(species_id), str(request_data["loci_id"]))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_LOCUS.format(new_locus_url)))

        if not result['boolean']:
            return {"message": "Locus not found"}, 404

        # check if locus exists on schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.ASK_SCHEMA_LOCUS2.format(new_schema_url, new_locus_url)))

        if not result['boolean']:
            return {"message": "Locus already on schema"}, 409

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('select ?parts '
                               'from <{0}> '
                               'where '
                               '{{ <{1}> typon:hasSchemaPart ?parts. '
                               '?parts typon:hasLocus <{2}>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url, new_locus_url)))

        schema_link = result["results"]["bindings"][0]['parts']['value']

        # add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:deprecated "true"^^xsd:boolean.}}'.format(current_app.config['DEFAULTHGRAPH'], schema_link))

        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {"message": "Locus sucessfully removed from schema"}, 201
        else:
            return {"message": "Could not remove locus from schema."}, result.status_code


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/loci/<int:loci_id>/data')
class SchemaLociDataAPItypon(Resource):

    @api.doc(responses={201: 'OK', 
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @w.admin_contributor_required
    def post(self, species_id, schema_id, loci_id):
        
        # check if schema has 'singularity' date
        # check if locus exists and has no sequences

        root_dir = os.path.abspath(current_app.config['SCHEMA_UP'])

        # folder to hold files with alleles to insert
        temp_dir = os.path.join(root_dir, '{0}_{1}'.format(species_id, schema_id))

        # create folder when uploading first file
        if os.path.isdir(temp_dir) is False:
            os.mkdir(temp_dir)

        request_data = request.get_json()

        filename = request_data['filename']
        file_content = request_data['content']

        file_path = os.path.join(temp_dir, filename)

        with open(file_path, 'wb') as ptf:
            # file was decoded for upload so we have to encode
            # with ISO-8859-1 to return to original format
            ptf.write(file_content.encode(encoding='ISO-8859-1'))

        # count number of loci in schema
        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'], species_id, schema_id)
        loci_count = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  sparql_queries.COUNT_SCHEMA_LOCI.format(current_app.config['DEFAULTHGRAPH'],
                                                                          schema_uri))
        # 0 if schema has no loci
        loci_count = int(loci_count['results']['bindings'][0]['count']['value'])

        # list files in temp dir
        file_count = len(os.listdir(temp_dir))
        print(loci_count, file_count, flush=True)
        if file_count == loci_count:
            os.system('python schema_inserter.py -i {0} &'.format(temp_dir))

        return {'OK': 'Received file with data to insert alleles of new locus.'}, 201


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/loci/<int:loci_id>/lengths')
class SchemaLociLengthsAPItypon(Resource):

    @api.doc(responses={201: 'OK', 
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        406: 'Not acceptable'},
             security=['access_token'])
    @w.admin_contributor_required
    def post(self, species_id, schema_id, loci_id):

        schema_uri = '{0}species/{1}/schemas/{2}'.format(current_app.config['BASE_URL'], species_id, schema_id)
        locus_uri = '{0}loci/{1}'.format(current_app.config['BASE_URL'], loci_id)

        # check if locus is linked to schema
        schema_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                    sparql_queries.ASK_SCHEMA_LOCUS.format(schema_uri, locus_uri))

        if schema_locus['boolean'] is False:
            return {'Not Found': 'Schema has no locus with provided ID.'}

        root_dir = os.path.abspath(current_app.config['PRE_COMPUTE'])

        # directory that stores the files with alleles length values
        schema_dir = os.path.join(root_dir, '{0}_{1}_lengths'.format(species_id, schema_id))

        request_data = request.get_json()

        file_content = request_data['content']
        file_content = {locus_uri: file_content[k] for k in file_content}

        # if file does not exist
        if os.path.isdir(schema_dir) is False:
            os.mkdir(schema_dir)

        locus_file = os.path.join(schema_dir, '{0}_{1}_{2}'.format(species_id, schema_id, loci_id))

        if os.path.isfile(locus_file) is False:
            with open(locus_file, 'wb') as lf:
                pickle.dump(file_content, lf)
        else:
            with open(locus_file, 'rb') as lf:
                locus_data = pickle.load(lf)

            ns_data = locus_data[loci_id]
            user_data = file_content[loci_id]

            ns_alleles = set(ns_data)
            user_alleles = set(user_data)

            # determine new alleles
            new_alleles = user_alleles - ns_alleles
            # add new alleles
            for a in new_alleles:
                ns_data[a] = user_data[a]

            locus_data[loci_id] = ns_data

            with open(locus_file, 'wb') as lf:
                pickle.dump(locus_data, lf)

        return {'OK': 'Received file alleles lengths to add to schema info.'}, 201

@species_conf.route('/<int:species_id>/loci')
class LociListAPItypon(Resource):
    """ Loci List Resource """

    parser = api.parser()
    parser.add_argument('prefix',
                        type=str,
                        help="Alias for the loci")

    parser.add_argument('sequence',
                        type=str,
                        location='args',
                        help="Loci sequence")

    parser.add_argument('locus_ori_name',
                        type=str,
                        help="Original locus name")

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, **kwargs):
        """ Lists the loci of a particular species """

        # get the request data
        prefix = kwargs['prefix']
        sequence = kwargs['sequence']
        locus_ori_name = kwargs['locus_ori_name']

        # check if species exists
        species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              sparql_queries.ASK_SPECIES_NS.format(species_url))

        if not result['boolean']:
            return {'NOT FOUND': 'There is no species with provided ID.'}, 404

        # sequence was provided, return the locus uri found that has the sequence
        if sequence is not None:

            sequence = sequence.upper()

            # Generate hash
            sequence_hash = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            # Query virtuoso
            sequence_uri = '{0}sequences/{1}'.format(current_app.config['BASE_URL'], str(sequence_hash))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_LOCI_WITH_DNA.format(current_app.config['DEFAULTHGRAPH'], sequence_uri, species_url)))

            res_loci = result['results']['bindings']
        else:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SPECIES_LOCI.format(current_app.config['DEFAULTHGRAPH'], species_url)))

            res_loci = result['results']['bindings']

        if prefix is not None:
            res_loci = [res for res in res_loci if prefix in res['name']['value']]

        if locus_ori_name is not None:
            res_loci = [res for res in res_loci if locus_ori_name in res['original_name']['value']]

        # if result is not empty, stream with context
        if len(res_loci) > 0:
            return Response(stream_with_context(generate('Loci', res_loci)), content_type='application/json', mimetype='application/json')
        # if there are loci with the sequence, filter based on other arguments
        else:
            return {'message': 'None of the loci in the NS meet the filtering criteria.'}, 404

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found'},
             security=["access_token"])
    @api.expect(loci_list_model)
    @w.admin_contributor_required
    def post(self, species_id):
        """ Add a new locus for a particular species """

        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()

        spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
        result_spec = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   ('ASK where {{ <{0}> a <http://purl.uniprot.org/core/Taxon>}}'.format(spec_url)))

        if not result_spec['boolean']:
            return {"message": "Species not found"}, 404

        # count number of loci already created for that species, build the new locus uri and send to server
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select (COUNT(?locus) as ?count) where { ?locus a typon:Locus; typon:isOfTaxon <' + spec_url + '>. }')
        # number_loci_spec = int(result["results"]["bindings"][0]['count']['value'])

        new_locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(post_data["locus_id"]))

        result_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                    ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))

        if not result_locus['boolean']:
            return {"message": "Locus provided not found"}, 404

        # Associate locus to species
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> a typon:Locus; typon:isOfTaxon <{2}> .}}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, spec_url))

        result = aux.send_data(query2send,
                               current_app.config['LOCAL_SPARQL'],
                               current_app.config['VIRTUOSO_USER'],
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {"message": "New locus added to species." + str(species_id)}, 201
        else:
            return {"message": "Could not add locus to species."}, result.status_code


# Isolates Routes

@species_conf.route('/<int:species_id>/isolates')
class IsolatesListAPItypon(Resource):
    """ Isolates Resource """

    parser = api.parser()

    parser.add_argument('isolName',
                        type=str,
                        required=False,
                        location='args',
                        help="Isolate name")

    parser.add_argument('start_date',
                        type=str,
                        required=False,
                        location='args',
                        help="provide a date in the format YYYY-MM-DDTHH:MM:SS to get the isolates that were uploaded after that defined date")

    parser.add_argument('end_date',
                        type=str,
                        required=False,
                        location='args',
                        help="provide a date in the format YYYY-MM-DDTHH:MM:SS to get the isolates that were uploaded after that defined date")


    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, **kwargs):
        """ Get the isolates of a species """

        # get request data
        request_data = request.args

        # check if there are any extra params in request
        isolName = False
        try:
            isolName = request_data['isolName']
        except:
            pass

        startDate = False
        try:
            startDate = request_data['start_date']
        except:
            pass

        endDate = False
        try:
            endDate = request_data['end_date']
        except:
            pass

        # if isolate name is provided return that isolate, else return all isolates
        # if number of isolates >100000 either increase the number of rows the virtuoso return or use the dateEntered property 
        # and make multiple queries to virtuoso based on the date until all have been fetched
        # you can create your own time intervals to better suit your query
        if isolName:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?date '
                                   'from <{0}> '
                                   'where '
                                   '{{ ?isolate a typon:Isolate; typon:isFromTaxon <{1}>; '
                                   ' typon:dateEntered ?date; typon:name "{2}"^^xsd:string.}}'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, isolName)))

        elif startDate and endDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:isFromTaxon <{1}>; typon:name ?name; typon:dateEntered ?date.'
                                   ' FILTER ( ?date > "{2}"^^xsd:dateTime ).'
                                   'FILTER ( ?date < "{3}"^^xsd:dateTime ) }} '
                                   'order by ASC(?date)}} }} LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, startDate, endDate)))

        elif endDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:isFromTaxon <{1}>; typon:name ?name;typon:dateEntered ?date. '
                                   'FILTER ( ?date < "{2}"^^xsd:dateTime ). }}'
                                   ' order by DESC(?date)}} }} LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, endDate)))

        elif startDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name where '
                                   '{{ ?isolate a typon:Isolate; typon:isFromTaxon <{1}>; typon:name ?name;typon:dateEntered ?date. '
                                   'FILTER ( ?date < "{2}"^^xsd:dateTime ). }}'
                                   'order by ASC(?date)}} }} '
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, startDate)))

        else:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:isFromTaxon <{1}>;typon:dateEntered ?date ; typon:name ?name. }}'
                                   'order by ASC(?date)}} }}'
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url)))

        if len(result["results"]["bindings"]) < 1:

            def generate_iso():
                yield '{"Isolates": []}'

            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
            return r

        latestIsolate = (result["results"]["bindings"])[-1]
        isolate_id = latestIsolate['isolate']['value']

        # get latest isolate submission date
        result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                               ('select ?date '
                                'from <{0}> '
                                'where '
                                '{{ <{1}> a typon:Isolate; typon:dateEntered ?date }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_id)))

        latestDatetime = (result2["results"]["bindings"])[0]['date']['value']
        number_of_isolates = len(result["results"]["bindings"])
        try:

            def generate_iso():
                yield '{"Isolates": ['

                try:
                    prev_item = result["results"]["bindings"].pop(0)
                except:
                    yield ']}'

                for item in result["results"]["bindings"]:
                    yield json.dumps(prev_item) + ','
                    prev_item = item

                yield json.dumps(prev_item) + ']}'

            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Last-Isolate', latestDatetime)

            if number_of_isolates > 49999:
                r.headers.set('All-Isolates-Returned', False)
            else:
                r.headers.set('All-Isolates-Returned', True)

            return r

        except:
            return {"message": "Empty man..."}, 404


@species_conf.route('/<int:species_id>/isolates/user')
class IsolatesUserListAPItypon(Resource):
    """ Isolates User Resource """

    parser = api.parser()

    parser.add_argument('isolName',
                        type=str,
                        required=False,
                        location='args',
                        help="Isolate name")

    parser.add_argument('start_date',
                        type=str,
                        required=False,
                        location='args',
                        help="provide a date in the format YYYY-MM-DDTHH:MM:SS to get the isolates that were uploaded after that defined date")

    parser.add_argument('end_date',
                        type=str,
                        required=False,
                        location='args',
                        help="provide a date in the format YYYY-MM-DDTHH:MM:SS to get the isolates that were uploaded after that defined date")

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, **kwargs):
        """ Get the isolates of the current user """

        c_user = get_jwt_identity()

        # get request data
        request_data = request.args

        # check if there are any extra params in request
        isolName = False
        try:
            isolName = request_data['isolName']
        except:
            pass

        startDate = False
        try:
            startDate = request_data['start_date']
        except:
            pass

        endDate = False
        try:
            endDate = request_data['end_date']
        except:
            pass

        user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(c_user))

        # if isolate name is provided return that isolate, else return all isolates
        # if number of isolates >100000 either increase the number of rows the virtuoso return or use the dateEntered property
        # and make multiple queries to virtuoso based on the date until all have been fetched
        # you can create your own time intervals to better suite your query
        if isolName:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?date '
                                   'from <{0}> '
                                   'where '
                                   '{{ ?isolate a typon:Isolate; typon:sentBy <{1}>; '
                                   'typon:isFromTaxon <{2}>; typon:dateEntered ?date; '
                                   'typon:name "{3}"^^xsd:string.}}'.format(current_app.config['DEFAULTHGRAPH'], user_url, new_spec_url, isolName)))

        elif startDate and endDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:sentBy <{1}>; '
                                   'typon:isFromTaxon <{2}>; typon:name ?name;typon:dateEntered ?date. '
                                   'FILTER ( ?date > "{3}"^^xsd:dateTime ).'
                                   'FILTER ( ?date < "{4}"^^xsd:dateTime ) }} '
                                   'order by ASC(?date)}} }}'
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], user_url, new_spec_url, startDate, endDate)))

        elif endDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:sentBy <{1}>; '
                                   'typon:isFromTaxon <{2}>; typon:name ?name;typon:dateEntered ?date.'
                                   'FILTER ( ?date < "{3}"^^xsd:dateTime ). }}'
                                   'order by DESC(?date)}} }} '
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], user_url, new_spec_url, endDate)))

        elif startDate:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:sentBy <{1}>;'
                                   'typon:isFromTaxon <{2}>; typon:name ?name;typon:dateEntered ?date.'
                                   'FILTER ( ?date > "{3}"^^xsd:dateTime ). }}'
                                   'order by ASC(?date)}} }}'
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], user_url, new_spec_url, startDate)))

        else:
            new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?isolate ?name '
                                   'from <{0}> '
                                   'where {{'
                                   '{{ select ?isolate ?name from <{0}> where '
                                   '{{ ?isolate a typon:Isolate; typon:sentBy <{1}>;'
                                   'typon:isFromTaxon <{2}>;typon:dateEntered ?date ; typon:name ?name. }}'
                                   'order by ASC(?date)}} }}'
                                   'LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], user_url, new_spec_url)))

        if len(result["results"]["bindings"]) < 1:

            def generate_iso():
                yield '{"Isolates": []}'

            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
            return r

        latestIsolate = (result["results"]["bindings"])[-1]
        isolate_id = latestIsolate['isolate']['value']

        # get latest isolate submission date
        result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                               ('select ?date '
                                'from <{0}> '
                                'where '
                                '{{ <{1}> a typon:Isolate; typon:dateEntered ?date }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_id)))

        latestDatetime = (result2["results"]["bindings"])[0]['date']['value']
        number_of_isolates = len(result["results"]["bindings"])
        try:

            def generate_iso():
                yield '{"Isolates": ['

                try:
                    prev_item = result["results"]["bindings"].pop(0)
                except:
                    yield ']}'

                for item in result["results"]["bindings"]:
                    yield json.dumps(prev_item) + ','
                    prev_item = item
                yield json.dumps(prev_item) + ']}'

            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Last-Isolate', latestDatetime)

            if number_of_isolates > 49999:
                r.headers.set('All-Isolates-Returned', False)
            else:
                r.headers.set('All-Isolates-Returned', True)
            return r

        except:
            return {"message": "Empty man..."}, 404


@species_conf.route('/<int:species_id>/isolates/<string:isolate_id>')
class IsolatesAPItypon(Resource):

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    @jwt_required
    def get(self, species_id, isolate_id, **kwargs):
        """ Get a particular isolate
        """

        new_isol_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))

        # get information on the isolate, metadata are optional
        query = ('select ?name ?country ?country_name ?accession ?st ?date_entered ?strainID ?col_date ?host ?host_disease ?lat ?long ?isol_source '
                 'from <{0}> '
                 'where {{'
                 '{{ <{1}> a typon:Isolate; typon:name ?name; typon:dateEntered ?date_entered .'
                 'OPTIONAL{{<{1}> typon:isolatedAt ?country. ?country rdfs:label ?country_name}} '
                 'OPTIONAL{{<{1}> typon:accession ?accession.}}'
                 'OPTIONAL{{<{1}> typon:ST ?st.}} '
                 'OPTIONAL{{<{1}> typon:sampleCollectionDate ?col_date.}}'
                 'OPTIONAL{{<{1}> typon:host ?host.}}'
                 'OPTIONAL{{<{1}> typon:hostDisease ?host_disease.}}'
                 'OPTIONAL{{<{1}> <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat.}}'
                 'OPTIONAL{{<{1}> <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long.}} '
                 'OPTIONAL{{<{1}> typon:isolationSource ?isol_source.}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)

        try:
            return (result["results"]["bindings"])
        except:
            return {"message": "It's empty man..."}, 404

    @api.doc(responses={201: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Conflict'},
             security=["access_token"])
    @api.expect(isolate_model)
    @w.admin_contributor_required
    def post(self, species_id, isolate_id):
        """ Adds/updates the metadata of an existing """

        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()

        # only admin can do this
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; '
                                   'typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))

            if not result['boolean']:
                return {"message": "Not authorized, admin only"}, 403

        except:
            return {"message": "Not authorized, admin only"}, 403

        # count number of isolates already created for that species, build the new isolate uri and send to server
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select (COUNT(?isolate) as ?count) where { ?isolate a typon:Isolate . }')
        # print(result)
        # number_isolates_spec = int(result["results"]["bindings"][0]['count']['value'])

        # new_isolate_id = number_isolates_spec + 1

        # new_isol_url = current_app.config['BASE_URL'] + "species/" + str(species_id) + "/isolates/" + str(isolate_id)
        new_isol_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))

        query = ('select ?name ?country ?country_name ?accession ?st ?date_entered ?strainID ?col_date ?host ?host_disease ?lat ?long ?isol_source '
                 'from <{0}> '
                 'where {{'
                 '{{ <{1}> a typon:Isolate; typon:name ?name; typon:dateEntered ?date_entered .'
                 'OPTIONAL{{<{1}> typon:isolatedAt ?country. ?country rdfs:label ?country_name}} '
                 'OPTIONAL{{<{1}> typon:accession ?accession.}}'
                 'OPTIONAL{{<{1}> typon:ST ?st.}} '
                 'OPTIONAL{{<{1}> typon:sampleCollectionDate ?col_date.}}'
                 'OPTIONAL{{<{1}> typon:host ?host.}}'
                 'OPTIONAL{{<{1}> typon:hostDisease ?host_disease.}}'
                 'OPTIONAL{{<{1}> <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat.}}'
                 'OPTIONAL{{<{1}> <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long.}} '
                 'OPTIONAL{{<{1}> typon:isolationSource ?isol_source.}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url))

        result_meta = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),query)

        result_meta = result_meta["results"]["bindings"][0]

        metadataNotUploadable = {}
        metadataUploadable = 0

        data2sendlist = []

        country_name = False
        try:
            # if already this value country already exists for isolate
            auxi = result_meta['country']['value']
        except:
            try:
                country_name = (post_data['country']).lower()
            except:
                pass

        #########
        # if metadata already on database, skip the new one
        # if metadata provided, insert in RDF

        # accession check
        try:
            auxi = result_meta['accession']['value']
        except:
            try:

                # check if accession exists in ENA
                print("checking accession...")
                accession = post_data['accession']

                # accessionTooSmall
                if len(accession) < 5:
                    metadataNotUploadable['accession'] = accession
                else:
                    existsInENA = aux.get_read_run_info_ena(accession)
                    print("Found in ena: {0}".format(str(existsInENA)))
                    if existsInENA:
                        data2sendlist.append(' typon:accession <https://www.ebi.ac.uk/ena/data/view/' + accession + '>')
                        metadataUploadable += 1
                    else:
                        existsInSRA = aux.get_read_run_info_sra(accession)
                        print("Found in sra: {0}".format(str(existsInSRA)))
                        if existsInSRA:
                            data2sendlist.append(' typon:accession <https://www.ncbi.nlm.nih.gov/sra/' + accession + '>')
                            metadataUploadable += 1
                        else:
                            metadataNotUploadable['accession'] = accession
            except:
                pass

        # ST check
        try:
            auxi = result_meta['st']['value']
        except:
            try:
                data2sendlist.append(' typon:ST "' + post_data['ST'] + '"^^xsd:integer')
                metadataUploadable += 1
            except:
                pass

        # collection date check
        try:
            auxi = result_meta['col_date']['value']
        except:
            try:
                col_date = post_data['collection_date']
                try:
                    col_date = str(dt.datetime.strptime(col_date, '%Y-%m-%d'))
                    data2sendlist.append(' typon:sampleCollectionDate "' + col_date + '"^^xsd:dateTime')
                    metadataUploadable += 1
                except:
                    metadataNotUploadable['coldate'] = col_date
            except:
                pass


        # host check
        try:
            auxi = result_meta['host']['value']
        except:
            try:
                # get the taxon id from uniprot, if not found metadata not added
                # capitalize the first letter as per scientific name notation
                hostname = (post_data['host']).capitalize()
                print("host name: " + hostname)

                # query is made to the scientific name first, then common name and then other name
                query = ('PREFIX up:<http://purl.uniprot.org/core/> '
                         'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                         'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                         'SELECT ?taxon FROM <http://sparql.uniprot.org/taxonomy> WHERE'
                         '{{OPTIONAL{{?taxon a up:Taxon; up:scientificName "{0}" }} '
                         'OPTIONAL{{?taxon a up:Taxon; up:commonName "{0}" }} '
                         'OPTIONAL{{?taxon a up:Taxon; up:otherName "{0}" }} .}}'.format(hostname))

                print ("searching on host..")

                result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
                try:
                    url = result2["results"]["bindings"][0]['taxon']['value']
                    data2sendlist.append(' typon:host <'+url+'>')
                    metadataUploadable += 1
                    print("host taxon found")
                except:
                    # not found, lets try the query without capitalized first letter
                    print("host name not found: " + hostname)
                    hostname = post_data['host']
                    print("Trying host name without first capitalized letter: {0}".format(hostname))

                    query = ('PREFIX up:<http://purl.uniprot.org/core/> '
                             'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                             'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                             'SELECT ?taxon FROM  <http://sparql.uniprot.org/taxonomy> WHERE'
                             '{{	OPTIONAL{{?taxon a up:Taxon; up:scientificName "{0}" }} '
                             'OPTIONAL{{?taxon a up:Taxon; up:commonName "{0}" }} '
                             'OPTIONAL{{?taxon a up:Taxon; up:otherName "{0}" }} .}}'.format(hostname))

                    print ("searching on uniprot..")

                    result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
                    try:
                        url = result2["results"]["bindings"][0]['taxon']['value']
                        data2sendlist.append(' typon:host <' + url + '>')
                        metadataUploadable += 1
                        print("host taxon found")
                    except:
                        print("no host names found for: " + hostname)
                        metadataNotUploadable['host'] = hostname
                        print("species name not found on uniprot, search on http://www.uniprot.org/taxonomy/")
                        pass

            except:
                pass

        # host disease check
        try:
            auxi = result_meta['host_disease']['value']
        except:
            try:
                host_disease_ID = post_data['host_disease']

                host_disease_URI = 'http://purl.obolibrary.org/obo/DOID_' + host_disease_ID

                print("checking disease...")
                disease_found = aux.check_disease_resource(host_disease_URI)

                print("disease found: " + str(disease_found))

                if disease_found:
                    data2sendlist.append(' typon:hostDisease <' + host_disease_URI + '>')
                    metadataUploadable += 1
                else:
                    print(host_disease_URI + " is not existant")
                    metadataNotUploadable['host_disease'] = host_disease_ID
            except Exception as e:
                print(e)
                pass

        # isolation source check
        try:
            auxi = result_meta['isol_source']['value']
        except:
            try:
                isol_source = post_data['isol_source']
                data2sendlist.append(' typon:isolationSource "' + isol_source + '"^^xsd:string')
                metadataUploadable += 1
            except:
                pass


        # longitude check
        try:
            auxi = result_meta['long']['value']
        except:
            try:
                longitude = post_data['long']
                try:
                    latitude = float(longitude)
                    data2sendlist.append(' <http://www.w3.org/2003/01/geo/wgs84_pos#long> "' + str(longitude) + '"^^xsd:long')
                    metadataUploadable += 1
                except:
                    metadataNotUploadable['long'] = longitude
            except:
                pass

        # latitude check
        try:
            auxi = result_meta['lat']['value']
        except:
            try:
                latitude = post_data['lat']
                try:
                    latitude = float(latitude)
                    data2sendlist.append(' <http://www.w3.org/2003/01/geo/wgs84_pos#lat> "' + str(latitude) + '"^^xsd:long')
                    metadataUploadable += 1
                except:
                    metadataNotUploadable['lat'] = latitude
            except Exception as e:
                print(e)
                pass

        # country check
        if country_name:
            # search for country on dbpedia, first query may work for some and not for others, try with netherlands for instance
            query = ('select ?country ?label where '
                     '{{?country a <http://dbpedia.org/class/yago/WikicatMemberStatesOfTheUnitedNations>; a dbo:Country; '
                     '<http://www.w3.org/2000/01/rdf-schema#label> ?label. '
                     'FILTER (lang(?label) = "en") '
                     'FILTER (STRLANG("{0}", "en") = LCASE(?label) ) }}'.format(country_name))
            print("searching country on dbpedia..")

            result = aux.get_data(SPARQLWrapper(current_app.config['DBPEDIA_SPARQL']), query)
            try:
                country_url = result["results"]["bindings"][0]['country']['value']
                label = result["results"]["bindings"][0]['label']['value']
                data2sendlist.append('typon:isolatedAt <' + country_url + '>.<' + country_url + '> rdfs:label "' + label + '"@en')
                metadataUploadable += 1
            except:
                try:
                    query = ('select ?country ?label where '
                             '{{?country a <http://dbpedia.org/class/yago/WikicatMemberStatesOfTheUnitedNations>; '
                             '<http://www.w3.org/2000/01/rdf-schema#label> ?label; a dbo:Country; dbo:longName ?longName. '
                             'FILTER (lang(?longName) = "en") '
                             'FILTER (STRLANG("{0}", "en") = LCASE(?longName) ) }}'.format(country_name))

                    print("searching on dbpedia for the long name..")
                    result = aux.get_data(SPARQLWrapper(current_app.config['DBPEDIA_SPARQL']), query)
                    country_url = result["results"]["bindings"][0]['country']['value']
                    label = result["results"]["bindings"][0]['label']['value']
                    data2sendlist.append('typon:isolatedAt <'+country_url+'>.<'+country_url+'> rdfs:label "'+label+'"@en')
                    metadataUploadable += 1
                except:
                    print("Metadata not added, " + str(country_name) + " not found on dbpedia search on http://dbpedia.org/page/Category:Member_states_of_the_United_Nations")
                    metadataNotUploadable['country'] = country_name
                    pass

        print(metadataNotUploadable)

        # if there is metadata to add or metadata to add and not passing the checks
        if len(data2sendlist) > 0 or len(list(metadataNotUploadable.keys())) > 0:

            # if there is metadata to add, build the rdf and send to virtuoso
            if len(data2sendlist) > 0:

                # Insert new information
                rdf2send = ";".join(data2sendlist)

                query2send = ('INSERT DATA IN GRAPH <{0}> {{ <{1}>{2}.}}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url, rdf2send))
                print(query2send)
                result = aux.send_data(query2send,
                                       current_app.config['LOCAL_SPARQL'],
                                       current_app.config['VIRTUOSO_USER'],
                                       current_app.config['VIRTUOSO_PASS'])

                if result.status_code not in [200, 201]:
                    return {"message": "Sum Thing Wong uploading metadata to isolate"}, result.status_code

            def generate_iso():

                yield '{"Uploaded_total": [' + str(metadataUploadable) + '],'

                yield '"Not_uploaded": ['

                auxkeys = list(metadataNotUploadable.keys())
                if len(auxkeys) < 1:
                    yield ']}'
                else:

                    prev_item = {}
                    try:
                        auxi = auxkeys.pop(0)
                        prev_item[auxi] = metadataNotUploadable[auxi]
                    except Exception as e:
                        print(e)
                        yield ']}'

                    for k in auxkeys:
                        yield json.dumps(prev_item) + ','
                        prev_item = {k: metadataNotUploadable[k]}
                    yield json.dumps(prev_item) + ']}'
            r = Response(stream_with_context(generate()), content_type='application/json')

            if metadataUploadable > 0:
                r.headers.set('Metadata-Uploaded', True)
            else:
                r.headers.set('Metadata-Uploaded', False)
            return r

        else:
            return {"message": "No metadata to upload"}, 409


@species_conf.route('/<int:species_id>/isolates/<string:isolate_id>/alleles')
class IsolatesAlleles(Resource):

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    # @w.token_required
    @jwt_required
    def get(self, species_id, isolate_id):
        """ Get all alleles from the isolate, independent of schema
        """

        # return all alleles from the isolate
        new_isol_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))

        # get all alleles from the isolate, independent of schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('select ?alleles '
                               'from <{0}> '
                               'where '
                               '{{ <{1}> a typon:Isolate; typon:hasAllele ?alleles.  }}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url)))

        try:
            return (result["results"]["bindings"])
        except:
            return {"message": "It's empty man..."}, 404

    @api.doc(responses={200: 'OK',
                        201: 'Success',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    @api.expect(allele_model)
    @w.admin_contributor_required
    def post(self, species_id, isolate_id):
        """ Link an allele to an isolate
        """

        # get post data
        post_data = request.get_json()

        # build urls for checks
        isolate_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))

        locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(post_data["locus_id"]))

        allele_url = "{0}/alleles/{1}".format(locus_url, str(post_data["allele_id"]))

        # check if isolate exists
        result_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                      ('ASK where {{ <{0}> a typon:Isolate .}}'.format(isolate_url)))

        if not result_isolate['boolean']:
            return  {"message": "Isolate not found"}, 404

        # check if locus exists
        result_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                    ('ASK where {{ <{0}> a typon:Locus .}}'.format(locus_url)))

        if not result_locus['boolean']:
            return {"message": "Locus not found"}, 404

        # check if allele exists
        result_allele = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                     ('ASK where {{ <{0}> a typon:Locus; typon:hasDefinedAllele <{1}> }}'.format(locus_url, allele_url)))

        if not result_allele['boolean']:
            return {"message": "Allele does not exist for that locus"}, 404

        # check if locus already exists on isolate
        result_locus_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            ('ASK where {{ <{0}> typon:hasAllele ?alleles. '
                                             '?alleles typon:isOfLocus <{1}>.}}'.format(isolate_url, locus_url)))

        if result_locus_isolate['boolean']:
            return {"message" : "An allele was already attributed to that isolate"}, 409

        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:hasAllele <{2}>.}}'.format(current_app.config['DEFAULTHGRAPH'], isolate_url, allele_url))
        result_post = aux.send_data(query2send,
                                    current_app.config['LOCAL_SPARQL'],
                                    current_app.config['VIRTUOSO_USER'],
                                    current_app.config['VIRTUOSO_PASS'])

        if result_post.status_code in [200, 201]:
            return {"message": "Allele and respective locus sucessfully added to isolate"}, 201
        else:
            return {"message": "Sum Thing Wong"}, result_post.status_code


@species_conf.route('/<int:species_id>/isolates/<int:isolate_id>/schemas')
class IsolatesSchema(Resource):

    parser = api.parser()

    parser.add_argument('schema_id',
                        type=str,
                        required=False,
                        location='args',
                        help='ID of a schema on NS')

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, isolate_id, **kwargs):
        """ Get the schemas that are linked to a particular isolate
        """

        # get request data
        request_data = request.args

        # get a specific schema
        if request_data:

            # build urls for checks
            species_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))

            # check if schema exists for that species
            schema_uri = "{0}/schemas/{1}".format(species_url, str(request_data["schema_id"]))

            result_schema = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                         ('ASK where {{ <{0}> a typon:Schema. '
                                          'FILTER NOT EXISTS {{ <{0}> typon:deprecated  "true"^^xsd:boolean }} }}'.format(schema_uri)))

            if not result_schema['boolean']:
                return {"message": ("Schema {0} not found or deprecated".format(schema_uri))}, 404

            # check if isolate exists
            isolate_url = "{0}/isolates/{1}".format(species_url, str(isolate_id))

            result_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                          ('ASK where {{ <{0}> a typon:Isolate .}}'.format(isolate_url)))

            if not result_isolate['boolean']:
                return {"message": "Isolate not found"}, 404

            schema_isolate_query = ('select ?id (str(?name) as ?name) '
                                    'from <{0}> '
                                    'where '
                                    '{{ <{1}> typon:hasAllele ?alleles. '
                                    '?alleles typon:id ?id; typon:isOfLocus ?locus. '
                                    '{{select ?locus ?name from <{0}> where '
                                    '{{<{2}> typon:hasSchemaPart ?part.'
                                    '?part typon:hasLocus ?locus. '
                                    '?locus typon:name ?name. '
                                    'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}} }} }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_url,schema_uri ))

            result_schema_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), schema_isolate_query)

            try:
                return (result_schema_isolate["results"]["bindings"])
            except:
                return {"message": "It's empty man..."}, 404

        # get all schemas linked to the isolate
        else:

            # check if isolate exists
            isolate_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))

            result_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                          ('ASK where {{ <{0}> a typon:Isolate .}}'.format(isolate_url)))

            if not result_isolate['boolean']:
                return {"message": "Isolate not found"}, 404

            schema_isolate_query = ('select ?schema ?id (str(?name) as ?name) '
                                    'from <{0}> '
                                    'where '
                                    '{{ <{1}> typon:hasAllele ?alleles. '
                                    '?alleles typon:id ?id; typon:isOfLocus ?locus. '
                                    '{{select ?schema ?locus ?name from <{0}> where '
                                    '{{?schema a typon:Schema; typon:hasSchemaPart ?part.'
                                    '?part typon:hasLocus ?locus. '
                                    '?locus typon:name ?name. '
                                    'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}} }} }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_url))

            result_schema_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), schema_isolate_query)

            try:
                return (result_schema_isolate["results"]["bindings"])
            except:
                return {"message": "It's empty man..."}, 404


# Sequences Routes

# Namespace
sequences_conf = api.namespace('sequences', description='Sequence related operations.')

@sequences_conf.route('/list')
class SequencesListAPItypon(Resource):
    """ Sequences List Resource """

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @jwt_required
    def get(self):
        """ Gets the total number of sequences """

        # query number of sequences on database
        # should return 0 if there are no sequences
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              (sparql_queries.COUNT_SEQUENCES.format(current_app.config['DEFAULTHGRAPH'])))

        number_sequences = int(result["results"]["bindings"][0]['count']['value'])

        return {"message": "Total number of sequences is: " + str(number_sequences)}


@sequences_conf.route('/seq_info')
class SequencesAPItypon(Resource):
    """ Sequences Resource """

    parser = api.parser()

    parser.add_argument('sequence',
                        type=str,
                        required=False,
                        location='args',
                        help="DNA sequence")

    parser.add_argument('species_id',
                        type=str,
                        required=False,
                        location='args',
                        help="ID of the species")

    parser.add_argument('seq_id',
                        type=str,
                        required=False,
                        location='args',
                        help="DNA sequence hash")

    @api.doc(responses={200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found'},
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, **kwargs):
        """Get information on sequence, DNA string, uniprot URI and uniprot label."""

        # get request data
        request_data = request.args
        if len(request_data) == 0:
            return {'message': 'Please provide a string for a valid DNA sequence or a valid DNA sequence hash.'}, 400

        # determine if species identifier was provided
        query_part = ''
        if 'species_id' in request_data:
            species_id = request_data['species_id']
            species_uri = '{0}{1}/{2}'.format(current_app.config['BASE_URL'], 'species', species_id)
            # create additional query part to filter by species
            query_part = '?locus a typon:Locus; typon:isOfTaxon <{0}> .'.format(species_uri)

        # if DNA sequence is provided, hash it and send request to virtuoso
        if 'sequence' in request_data:

            sequence = request_data['sequence']

            new_id = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            new_seq_url = '{0}sequences/{1}'.format(current_app.config['BASE_URL'], str(new_id))

            # check if the sequence exists
            result_existence = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                            (sparql_queries.ASK_SEQUENCE_HASH.format(new_seq_url)))

            if not result_existence['boolean']:
                return {'message': 'Provided DNA sequence is not in the NS.'}, 404

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SEQUENCE_INFO_BY_DNA.format(current_app.config['DEFAULTHGRAPH'], new_seq_url, query_part)))

            sequence_info = result['results']['bindings']
            if sequence_info != []:
                return {'result': sequence_info,
                        'sequence_uri': new_seq_url}, 200
            else:
                return {'NOT FOUND': 'Could not find provided DNA sequence in the NS.'}, 404
        # if sequence hash is provided
        elif 'seq_id' in request_data:
            new_seq_url = '{0}sequences/{1}'.format(current_app.config['BASE_URL'], str(request_data['seq_id']))

            # get information on sequence, DNA string, uniprot URI and uniprot label
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  (sparql_queries.SELECT_SEQUENCE_INFO_BY_HASH.format(current_app.config['DEFAULTHGRAPH'], new_seq_url, query_part)))

            sequence_info = result['results']['bindings']
            if sequence_info != []:
                return sequence_info, 200
            else:
                return {'NOT FOUND': 'Could not find information for a sequence with provided hash.'}, 404
