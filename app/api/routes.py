# stdlib imports
import os
import jwt
import sys
import time
import hashlib
import datetime as dt
import requests, json

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

# App imports
from app.utils import aux
from app.models import User, Role
from app.utils import wrappers as w
from app import (db, celery, login_manager, 
                datastore_cheat, security, jwt)

from app.api import api, blueprint

# Helper imports
#from app.utils.blacklist_service import save_token

from SPARQLWrapper import SPARQLWrapper

# Get the error handlers to work with restplus
jwt._set_error_handler_callbacks(api)

#queue to add locus do schema
@celery.task(time_limit=20)
def add_locus_schema(new_schema_url, new_locus_url):	
    
    #get number of loci on schema and build the uri based on that number+1
    result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                         ('select (COUNT(?parts) as ?count) '
                          'from <{0}>'
                          'where {{ <{1}> typon:hasSchemaPart ?parts. }}'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))
    
    number_schema_parts = int(result["results"]["bindings"][0]['count']['value'])
    
    new_schema_part_url = "{0}/loci/{1}".format(new_schema_url, str(number_schema_parts + 1))
    
    #send data to graph
    query2send = ('INSERT DATA IN GRAPH <{0}> '
                  '{{ <{1}> a typon:SchemaPart ; '
                  'typon:index "{2}"^^xsd:int ; '
                  'typon:hasLocus <{3}>.'
                  '<{4}> typon:hasSchemaPart <{5}>.}}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                              new_schema_part_url, 
                                                              str(number_schema_parts + 1), 
                                                              new_locus_url, 
                                                              new_schema_url, 
                                                              new_schema_part_url))
    
    #result = aux.send_data(query2send, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
    result = aux.send_data(query2send, 
                           current_app.config['LOCAL_SPARQL'], 
                           current_app.config['VIRTUOSO_USER'], 
                           current_app.config['VIRTUOSO_PASS'])
    
    if result.status_code in [200, 201] :
        return {"message" : "Locus sucessfully added to schema"}, 201		
    else:
        return {"message" : "Sum Thing Wong"}, result.status_code


#queue to add alleles
@celery.task(time_limit=20)
def add_allele(new_locus_url, spec_name, loci_id, new_user_url, new_seq_url, isNewSeq, add2send2graph, sequence):
    
    query = ('SELECT ?alleles '
             'FROM <{0}>'
             'WHERE '
             '{{ ?alleles typon:isOfLocus <{1}>; typon:hasSequence ?seq. '
             '?seq a typon:Sequence; typon:nucleotideSequence "{2}"^^xsd:string.}}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, sequence))
    
    if len(sequence) > 9000:
        result = aux.send_big_query(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)
    else:
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)

    
    #if sequence exists return the allele uri, if not create new sequence
    try:
        new_allele_url = result["results"]["bindings"][0]['alleles']['value']
        return {"message" : "already exists" + new_allele_url}, 409
    
    except:
        pass
    

    #get number of alleles for locus
    result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                         ('select (COUNT(?alleles) as ?count)'
                         'from <{0}>'
                         'where '
                          '{{ ?alleles typon:isOfLocus <{1}>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))
    
    number_alleles_loci = int(result["results"]["bindings"][0]['count']['value'])
    new_allele_url = "{0}loci/{1}/alleles/{2}".format(current_app.config['BASE_URL'], str(loci_id), str(number_alleles_loci + 1))
    
    #add allele to virtuoso
    if isNewSeq:
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> a typon:Sequence {2} ; '
                      'typon:nucleotideSequence "{3}"^^xsd:string . '
                      '<{4}> a typon:Allele; '
                      'typon:name "{5}"^^xsd:string; '
                      'typon:sentBy <{6}>; '
                      'typon:isOfLocus <{7}>; '
                      'typon:dateEntered "{8}"^^xsd:dateTime; '
                      'typon:id "{9}"^^xsd:integer; '
                      'typon:hasSequence <{1}> . '
                      '<{7}> typon:hasDefinedAllele <{4}>.}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                     new_seq_url,
                                                                     add2send2graph,
                                                                     sequence,
                                                                     new_allele_url,
                                                                     spec_name,
                                                                     new_user_url,
                                                                     new_locus_url,
                                                                     str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                     str(number_alleles_loci+1)
                                                                     ))

        # result = aux.send_data(query2send, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])

    #add new link from allele to sequence
    else:
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> a typon:Allele; '
                      'typon:name "{2}"; '
                      'typon:sentBy <{3}> ;'
                      'typon:isOfLocus <{4}>; '
                      'typon:dateEntered "{5}"^^xsd:dateTime; '
                      'typon:id "{6}"^^xsd:integer ; '
                      'typon:hasSequence <{7}>. '
                      '<{4}> typon:hasDefinedAllele <{1}>.}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                    new_allele_url,
                                                                    spec_name,
                                                                    new_user_url,
                                                                    new_locus_url,
                                                                    str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                    str(number_alleles_loci+1),
                                                                    new_seq_url
                                                                    ))
        
        # result = aux.send_data(query2send, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])

        #return {"message" : "Sequence was already attributed to a loci/allele"}, 418

    #print(result)
    if result.status_code not in [200, 201] :
        return {"message" : "Sum Thing Wong creating sequence 1"}, result.status_code
    else:
        return {"message" : "A new allele has been added to " + new_allele_url}, result.status_code


#queue to add profile		
@celery.task(time_limit=20)
def add_profile(rdf_2_ins):
    
    # result = aux.send_data(rdf_2_ins, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
    result = aux.send_data(rdf_2_ins, 
                           current_app.config['LOCAL_SPARQL'], 
                           current_app.config['VIRTUOSO_USER'], 
                           current_app.config['VIRTUOSO_PASS'])
    
    #try to send it a few times if error
    try:
        if result.status_code > 201 :
            time.sleep(2)
            # result = aux.send_data(rdf_2_ins, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
            result = aux.send_data(rdf_2_ins, 
                                   current_app.config['LOCAL_SPARQL'], 
                                   current_app.config['VIRTUOSO_USER'], 
                                   current_app.config['VIRTUOSO_PASS'])

            if result.status_code not in [200, 201] :
                return {"message" : "Sum Thing Wong creating profile"}, result.status_code
            
            else:
                return True, result.status_code
        
        else:
            return True, result.status_code
    
    except Exception as e:
        try:
            if result.status_code > 201 :
                time.sleep(2)
                # result = aux.send_data(rdf_2_ins, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
                result = aux.send_data(rdf_2_ins, 
                                       current_app.config['LOCAL_SPARQL'], 
                                       current_app.config['VIRTUOSO_USER'], 
                                       current_app.config['VIRTUOSO_PASS'])
                
                if result.status_code not in [200, 201] :
                    return {"message" : "Sum Thing Wong creating profile"}, result.status_code
                else:
                    return True, result.status_code
                    
            else:
                return True, result.status_code
        except Exception as e:
            
            return e, 400
        return e, 400
    

# Get datastore from init. 
# This is cheating and extremely inelegant!!
# TODO
user_datastore = datastore_cheat

# Create a default admin user on Postgres and Virtuoso
@blueprint.before_app_first_request
def create_role():
    try:
    
        db.drop_all() #FOR DEBUG ONLY!!
        db.create_all()
        user_datastore.create_role(name="Admin")
        user_datastore.create_role(name="Contributor")
        user_datastore.create_role(name="User")

        u = user_datastore.create_user(email="test@refns.com", password=hash_password("mega_secret"))
        user_datastore.add_role_to_user(u, "Admin")
        db.session.commit()
        # role = user_datastore.find_role("User")
        # user_datastore.add_role_to_user(user, role)
        
        # Send user to Virtuoso
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(u.id))
        newUserRole = "Admin"
        sparql_query = ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                       'INSERT DATA IN GRAPH <{0}> '
                       '{{ <{1}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "{2}"^^xsd:string}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                                                             new_user_url,
                                                                                                             newUserRole))
        
        # result = aux.send_data(sparql_query, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], 
        #                        current_app.config['VIRTUOSO_USER'], 
        #                        current_app.config['VIRTUOSO_PASS'])
        
        result = aux.send_data(sparql_query, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])
        #print("NICE")

    except:
        db.session.rollback()
        print("Role created already...")

######## API ROUTES ##########################################################################

# Namespace for Login
auth_conf = api.namespace('auth', description='authentication operations')

# Login model
auth_model = api.model("LoginModel", {
    'email': fields.String(required=True,
                           description="user email address", 
                           example="test@refns.com"),
    'password': fields.String(required=True, 
                              description="user password",
                              example="mega_secret")
})

# refresh_model = api.model("RefreshModel", {
#     'refresh_token': fields.String(required=True,
#                                    description="refresh token")
# })


@auth_conf.route("/login")
class UserLoginAPI(Resource):
    """ 
    User login resource 
    """

    @api.doc(responses={ 200 : "Success"})
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
                #db.session.commit() 
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
                    ## Front-end communicating with back-end?
                    #set_access_cookies(jsonify(response_object), auth_token)
                    #set_refresh_cookies(jsonify(response_object), auth_refresh_token)
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
    """ 
    Refresh token resource 
    """

    @api.doc(responses={ 200 : "Success"},
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
    
    @api.doc(responses={ 201: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated' },
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

# Namespace for User operations
user_conf = api.namespace('user', description='user related operations')

# User models
user_model = api.model("UserModel", {
    'id': fields.Integer(description="user ID"),
    'email': fields.String(required=True, 
                           description='user email address'),
    'roles': fields.String(required=True, 
                           description='role of the user')
})

current_user_model = api.model("CurrentUserModel", {
    'id': fields.Integer(description="User ID"),
    'email': fields.String,
    'last_login_at': fields.DateTime,
    "roles": fields.String
})

create_user_model = api.model("CreateUserModel", {
    'email': fields.String(required=True,
                           description="user email address",
                           example= "user@test.com"),
    'password': fields.String(required=True,
                              description="user password",
                              example="giga_secret",
                              min_length=6)
})

# User routes
@user_conf.route("/users")
class AllUsers(Resource):
    """ Returns a list of users """

    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument',
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated' },
             security=['access_token'])
    @api.marshal_with(user_model)
    @w.admin_required
    def get(self):
        """ Returns a list of users """
        
        users = db.session.query(User).all()
        
        return users, 200


    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated' },
             security=['access_token'])
    @api.expect(create_user_model, validate=True)
    @w.admin_required
    def post(self):
        """ Creates a user (Admin only) """

        ### TODO: ADD SPARQL QUERY

        # Get post data
        data = request.get_json()

        email = data["email"]
        password = data["password"]

        # Check if user already exists
        us = user_datastore.get_user(email)

        if us == None:

            # Create the new user
            u = user_datastore.create_user(email=email, password=hash_password(password))

            # Add the default role of "User" to the new user
            default_role = user_datastore.find_role("User")
            user_datastore.add_role_to_user(u, default_role)

            # Commit changes to the database
            db.session.commit()

            return {"message" : "User created successfully"}, 201

        else:
            return {"message" : "User already exists, please login."}, 403
        

@user_conf.route("/register_user")
class RegisterUser(Resource):
    """ Registers a user """

    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated' },
             security=[])
    @api.expect(create_user_model, validate=True)
    def post(self):
        """ Registers a user """

        ### TODO: ADD SPARQL QUERY
       
        # Get post data
        data = request.get_json()

        email = data["email"]
        password = data["password"]

        # Check if user already exists
        us = user_datastore.get_user(email)

        if us == None:

            # Create the new user
            u = user_datastore.create_user(email=email, password=hash_password(password))

            # Add the default role of "User" to the new user
            default_role = user_datastore.find_role("User")
            user_datastore.add_role_to_user(u, default_role)

            # Commit changes to the database
            db.session.commit()

            # Get the new user id
            new_user_id = user_datastore.get_user(email).id

            # Get the new user role
            new_user_role = "User"

            # Build the new user url
            new_user_url = '{0}users/{1}'.format(current_app.config['BASE_URL'], str(new_user_id))

            # Insert new user on Virtuoso
            sparql_query = ('INSERT DATA IN GRAPH <{0}> '
                           '{{ <{1}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "{2}"^^xsd:string }}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                                                                                  new_user_url, 
                                                                                                                  new_user_role))
            
            # result = aux.send_data(sparql_query, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
            result = aux.send_data(sparql_query, 
                                   current_app.config['LOCAL_SPARQL'], 
                                   current_app.config['VIRTUOSO_USER'], 
                                   current_app.config['VIRTUOSO_PASS'])
            
            if result.status_code in [200, 201]:
                return {"message" : "User created successfully",}, 201
            
            else:
                return {"message": "Sum Thing Wong"}, 500

        else:
            return {"message" : "User already exists, please login."}, 403



@user_conf.route("/current_user")
class CurrentUser(Resource):
    """
    returns the current user
    """

    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated' },
             security=['access_token'])
    @api.marshal_with(current_user_model)
    @jwt_required
    def get(self):
        """Returns the current user"""

        current_user = get_jwt_identity()
        
        user = User.query.get_or_404(current_user)

        return user, 200


@user_conf.route("/<int:id>")
class Users(Resource):
    """
    Returns the user with the provided id
    """

    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated', 
                         404: 'Not Found' }, 
             params={ 'id': 'Specify the ID associated with the user' },
             security=['access_token'])
    @api.marshal_with(user_model)
    @w.admin_required
    def get(self, id):
        """Returns the user with the provided id"""
        
        user = User.query.get_or_404(id)

        return user, 200
        


    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated', 
                         404: 'Not Found' }, 
             params={ 'id': 'ID of the user to promote' },
             security=['access_token'])
    @w.admin_required
    def put(self, id):
        """ Promote User """

        # Get user data
        user = User.query.get_or_404(id)
        remove_this_role = user.roles[0]
        promote_to_this_role = user_datastore.find_role("Contributor")
        
        # Remove User's current role
        user_datastore.remove_role_from_user(user, remove_this_role) 

        # Add new role to the User (Promotion) 
        user_datastore.add_role_to_user(user, promote_to_this_role)
        
        # Commit changes to the database
        db.session.commit()

        return {"message" : "The user {0} has been promoted to {1}".format(str(user.email), str(promote_to_this_role))}, 200

    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated', 
                         404: 'Not Found' }, 
             params={'id': 'ID of the user to delete' },
             security=['access_token'])
    @w.admin_required
    def delete(self, id):
        """ Delete user """

        # Get user data
        user = User.query.get_or_404(id)

        # Remove user
        user_datastore.delete_user(user)

        # Commit changes to the database
        db.session.commit()

        return {"message" : "The user {0} has been deleted".format(str(user.email))}, 200

############################################## Stats Routes ##############################################

stats_conf = api.namespace('stats', description = 'statistics of the database.')

# new_loci_model = api.model("NewLociModel", {
#     'prefix' : fields.String(required=True, description="Alias for the loci"),
#     'locus_ori_name' : fields.String(description="Original name of the locus")    
# })

# allele_list_model = api.model("AlleleListModel", {
#     'sequence' : fields.String(required=False, description="Allele DNA sequence"),
#     'species_name' : fields.String(required=True, description="Name of the species (assumes it exists already)"),
#     'uniprot_url': fields.String(required=False, default=False, description="Url to the Uniprot result of the allele"), 
#     'uniprot_label': fields.String(required=False, default=False, description="Uniprot label of the allele"),
#     'uniprot_sname': fields.String(required=False, default=False, description="Uniprot sname of the allele"),
#     'sequence_uri': fields.String(required=False, default=False, description="URI of an existing sequence"),
#     'enforceCDS' : fields.Boolean(required=False, default=False, description="Enforce CDS"),
#     'input': fields.String(required=False, enum=["manual, auto, link"],
#                            description="Type of input. Options are manual, auto, link." 
#                                        "Manual presumes that only one allele will be inserted."
#                                        "Auto presumes that a whole schema is being loaded."
#                                        "Link is useful to add an existing sequence to a new allele and locus.")
# })

##########################################################################################################


@stats_conf.route("/summary")
class StatsSummary(Resource):
    """ Summary of the data. """
    
    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=[])
    def get(self):	
        """ Count the number of items in Typon """
    
        #count stuff from on virtuoso
        try:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                        ('select * '
                        'from <{0}>'
                        'where {{ '
                        '{{ select (COUNT(?spec) as ?species) where {{?spec a <http://purl.uniprot.org/core/Taxon>}} }} '
                        '{{ select (COUNT(?loc) as ?loci) where {{?loc a typon:Locus }} }} '
                        '{{ select (COUNT(?schema) as ?schemas) where {{?schema a typon:Schema. }} }} '
                        '{{ select (COUNT(?all) as ?alleles) where {{?all a typon:Allele. }} }} }}'.format(current_app.config['DEFAULTHGRAPH'])))

            
            return {"message" : result["results"]["bindings"]}, 200
        
        except:
            return {"message" : "Sum thing wong"}, 404

@stats_conf.route("/species")
class StatsSpecies(Resource):
    """ Summary of all species data. """
    
    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=[])
    def get(self):	
        """ Count the number of schemas for each species. """
    
        #count stuff from on virtuoso
        try:
            
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                ('select ?species ?name (COUNT(?sch) AS ?schemas) '    # HURR-DURR with a space after the end it works...
                    'from <{0}> '
                    'where '
                    '{{ ?sch a typon:Schema; typon:isFromTaxon ?species . '
                    '?species a <http://purl.uniprot.org/core/Taxon>; typon:name ?name . }}'
                    'ORDER BY ?species'.format(current_app.config['DEFAULTHGRAPH'])))

            
            return {"message" : result["results"]["bindings"]}, 200
        
        except:
            return {"message" : "Sum thing wong"}, 404


@stats_conf.route("/species/<int:species_id>")
class StatsSpeciesId(Resource):
    """ Summary of one species' data. """
    
    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=[])
    def get(self, species_id):	
        """ Get the loci and count the alleles for each schema of a particular species. """

        new_species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))
    
        #count stuff from on virtuoso
        try:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                ('select ?schema ?name ?user ?chewie ?bsr ?ptf ?tl_table ?minLen (COUNT(DISTINCT ?locus) as ?nr_loci) (COUNT(DISTINCT ?allele) as ?nr_allele) '    # HURR-DURR with a space after the end it works...
                    'from <{0}> '
                    'where '
                    '{{ ?schema a typon:Schema; typon:isFromTaxon <{1}>; '
                    'typon:schemaName ?name; typon:administratedBy ?user; '
                    'typon:chewBBACA_version ?chewie; typon:bsr ?bsr; '
                    'typon:ptf ?ptf; typon:translation_table ?tl_table; '
                    'typon:minimum_locus_length ?minLen; '
                    'typon:hasSchemaPart ?part . '
                    '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                    '?allele a typon:Allele; typon:isOfLocus ?locus .}}'
                    'ORDER BY ?schema'.format(current_app.config['DEFAULTHGRAPH'], new_species_url)))


                        
            return {"message" : result["results"]["bindings"]}, 200
        
        except:
            return {"message" : "Sum thing wong"}, 404


@stats_conf.route("/species/<int:species_id>/schema")
class StatsSpeciesSchemas(Resource):
    """ Summary of one species' data. """
    
    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=[])
    def get(self, species_id):	
        """ Get the loci and count the alleles for each schema of a particular species. """

        new_species_url = '{0}species/{1}'.format(current_app.config['BASE_URL'], str(species_id))
    
        #count stuff from on virtuoso
        try:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                ('select ?schema ?locus (COUNT(DISTINCT ?allele) as ?nr_allele) (str(?UniprotLabel) as ?UniprotLabel) (str(?UniprotSName) as ?UniprotSName) (str(?UniprotURI) as ?UniprotURI) '    # HURR-DURR with a space after the end it works...
                    'from <{0}> '
                    'where '
                    '{{ ?schema a typon:Schema; typon:isFromTaxon <{1}>; '
                    'typon:hasSchemaPart ?part . '
                    '?part a typon:SchemaPart; typon:hasLocus ?locus .'
                    '?allele a typon:Allele; typon:isOfLocus ?locus . '
                    '?allele typon:hasSequence ?sequence . '
                    'OPTIONAL{{?sequence typon:hasUniprotLabel ?UniprotLabel.}} '
                    'OPTIONAL{{?sequence typon:hasUniprotSName ?UniprotSName.}} '
                    'OPTIONAL{{?sequence typon:hasUniprotSequence ?UniprotURI }} }}'
                    'ORDER BY ?schema'.format(current_app.config['DEFAULTHGRAPH'], new_species_url)))


                    # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                    #          ('select distinct (str(?UniprotLabel) as ?UniprotLabel) (str(?UniprotSName) as ?UniprotSName) (str(?UniprotURI) as ?UniprotURI) '
                    #           'from <{0}>'
                    #           'where '
                    #           '{{ <{1}> a typon:Locus; typon:name ?name. '
                    #           '?alleles typon:isOfLocus <{1}> .'
                    #           '?alleles typon:hasSequence ?sequence. '
                    #           'OPTIONAL{{?sequence typon:hasUniprotLabel ?UniprotLabel.}} '
                    #           'OPTIONAL{{?sequence typon:hasUniprotSName ?UniprotSName.}}'
                    #           'OPTIONAL{{?sequence typon:hasUniprotSequence ?UniprotURI }} }}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))


                        
            return {"message" : result["results"]["bindings"]}, 200
        
        except:
            return {"message" : "Sum thing wong"}, 404

############################################## Loci Routes ##############################################

loci_conf = api.namespace('loci', description = 'loci related operations')

new_loci_model = api.model("NewLociModel", {
    'prefix' : fields.String(required=True, description="Alias for the loci"),
    'locus_ori_name' : fields.String(description="Original name of the locus")    
})

allele_list_model = api.model("AlleleListModel", {
    'sequence' : fields.String(required=False, description="Allele DNA sequence"),
    'species_name' : fields.String(required=True, description="Name of the species (assumes it exists already)"),
    'uniprot_url': fields.String(required=False, default=False, description="Url to the Uniprot result of the allele"), 
    'uniprot_label': fields.String(required=False, default=False, description="Uniprot label of the allele"),
    'uniprot_sname': fields.String(required=False, default=False, description="Uniprot sname of the allele"),
    'sequence_uri': fields.String(required=False, default=False, description="URI of an existing sequence"),
    'enforceCDS' : fields.Boolean(required=False, default=False, description="Enforce CDS"),
    'input': fields.String(required=False, enum=["manual, auto, link"],
                           description="Type of input. Options are manual, auto, link." 
                                       "Manual presumes that only one allele will be inserted."
                                       "Auto presumes that a whole schema is being loaded."
                                       "Link is useful to add an existing sequence to a new allele and locus.")
})

##########################################################################################################

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
    
    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument',
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @w.admin_contributor_required
    def get(self, **kwargs):
        """ Get a list of all loci on NS """

        # Get list of loci that contain the provided DNA sequence
        try: 
            
            # Get sequence from request
            sequence = str(request_data["sequence"]).upper()
            
            # Generate hash
            new_id = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            # Query virtuoso
            new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(new_id))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?locus (str(?name) as ?name) '
                                   'from <{0}>'
                                   'where '
                                   '{{?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus .'
                                   ' ?locus a typon:Locus; typon:name ?name .}}'.format(current_app.config['DEFAULTHGRAPH'], new_seq_url)))

            try:
                return (result["results"]["bindings"])
            
            except:
                return {"message" : "Loci not found"}, 404
                
        except:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?locus (str(?name) as ?name) '
                                  'from <{0}> '
                                  'where '
                                  '{{ ?locus a typon:Locus; typon:name ?name .}}'
                                  'order by ?locus'.format(current_app.config['DEFAULTHGRAPH'])))

            # Return records containing prefix only
            try:
            
                request_data["prefix"]
                
                try:
                    def generate():

                        if len(result["results"]["bindings"]) == 0:
                            yield '{ "Loci": [] }'
                        
                        else:

                            resp = []

                            for item in result["results"]["bindings"]:
                                #print(item)
                                
                                if request_data["prefix"] in item["name"]["value"]:
                                    resp.append(json.dumps(item))

                            resp = ','.join(resp)

                            yield '{ "Loci": ['
                            yield resp
                            yield '] }'

                    return Response(stream_with_context(generate()), content_type='application/json', mimetype='application/json')
                    
                except:
                    return {"message" : "Bad argument"}, 400
            
            # return all records
            except:
                
                try:
                    def generate():

                        resp = []

                        for item in result["results"]["bindings"]:
                            resp.append(json.dumps(item))

                        resp = ','.join(resp)

                        yield '{ "Loci": ['
                        yield resp
                        yield '] }'

                    return Response(stream_with_context(generate()), content_type='application/json', mimetype='application/json')
                    
                except:
                    return {"message" : "Bad argument"}, 400



    
    
    @api.doc(responses={201: 'OK', 
                        400: 'Invalid Argument', 
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Conflict' },
            security=["access_token"])
    @api.expect(new_loci_model)
    @w.admin_contributor_required
    def post(self):
        """ Add a new locus """

        # get user data
        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()
 
        try:
            post_data["prefix"]
            aux.check_len(post_data['prefix'])
        except:
            return {"message" : "Provide prefix"}, 400
        
        
        #only admin can do this
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
            
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  'ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "Admin"^^xsd:string}}'.format(new_user_url))
            
            if not result['boolean']:
                return {"message" : "Not authorized, admin only"}, 403
        
        except:
            return {"message" : "Not authorized, admin only"}, 403
        

        
        #check if already exists locus with that aliases
        #result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 'SELECT (str(?name) as ?name) where { ?locus a typon:Locus; typon:name ?name . FILTER CONTAINS(str(?name), "' + post_data["prefix"] + '")}')
        #result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 'ASK where { ?locus a typon:Locus; typon:name ?name . FILTER CONTAINS(str(?name), "' + post_data["prefix"] + '")}')
        #print(result)
        
        #count number of loci already created, build the new locus uri and send to server
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('select (COUNT(?locus) as ?count) '
                               'from <{0}> '
                               'where '
                               '{{ ?locus a typon:Locus . }}'.format(current_app.config['DEFAULTHGRAPH'])))

        number_loci_spec = int(result["results"]["bindings"][0]['count']['value'])
        
        newLocusId = number_loci_spec + 1
        
        #name will be something like prefix-000001.fasta
        aliases = post_data['prefix'] + "-" + "%06d" % (newLocusId,) + ""

        #check if already exists locus with that aliases
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                              ('ASK where {{ ?locus a typon:Locus; typon:name ?name . '
                               'FILTER CONTAINS(str(?name), "{0}")}}'.format(aliases)))

        if result['boolean']:
            return {"message" : "Locus already exists"}, 409

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(newLocusId))
        
        #if locus_ori_name then also save the original fasta name
        try:
            
            locus_ori_name = post_data["locus_ori_name"]
            
            query2send = ('INSERT DATA IN GRAPH <{0}> '
                         '{{ <{1}> a typon:Locus; typon:name "{2}"^^xsd:string; typon:originalName "{3}"^^xsd:string.}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                                                                                new_locus_url, 
                                                                                                                                aliases, 
                                                                                                                                locus_ori_name))
            
            result = aux.send_data(query2send, 
                                   current_app.config['LOCAL_SPARQL'], 
                                   current_app.config['VIRTUOSO_USER'], 
                                   current_app.config['VIRTUOSO_PASS'])
            
        except:
            query2send = ('INSERT DATA IN GRAPH <{0}> '
                          '{{ <{1}> a typon:Locus; typon:name "{2}"^^xsd:string .}}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                                                            new_locus_url, 
                                                                                            aliases))

            result = aux.send_data(query2send, 
                                   current_app.config['LOCAL_SPARQL'], 
                                   current_app.config['VIRTUOSO_USER'], 
                                   current_app.config['VIRTUOSO_PASS'])
        
        # "New locus added at " + new_locus_url + " with the alias: " + aliases
        # "New locus added at {0} with the alias {1}".format(new_locus_url, aliases)
        if result.status_code in [200, 201] :
            return {"message" : "New locus added at {0} with the alias {1}".format(new_locus_url, aliases), 
                    "url" : new_locus_url,
                    "id" : str(newLocusId)}, 201
        else:
            return {"message" : "Sum Thing Wong"}, result.status_code


@loci_conf.route("/<int:loci_id>")
class LociNS(Resource):
    """ Gets a particular locus ID """


    @api.doc(responses={200: 'OK', 
                        400: 'Invalid Argument',
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not Found' },
            security=["access_token"])
    @jwt_required
    def get(self, loci_id, **kwargs):
        """ Get a particular locus """
        
        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        try:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('select (str(?name) as ?name) (str(?original_name) as ?original_name) '
                                  'from <{0}>'
                                  ' where '
                                  '{{ <{1}> a typon:Locus; typon:name ?name . '
                                  'OPTIONAL{{<{1}> typon:originalName ?original_name.}} '
                                  'OPTIONAL{{<{1}> typon:isOfTaxon ?taxon}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))
            
            response = result["results"]["bindings"]
        
            if response == []:
                return {"message": "No loci found with the provided id."}, 404

            else:
                return (response)
            
        except:
            return {"message" : "Empty man..."}, 404


@loci_conf.route('/<int:loci_id>/fasta')
class LociNSFastaAPItypon(Resource):
    """ Loci NS Fasta Resource """


    @api.doc(responses={ 200: 'OK', 
                        400: 'Invalid Argument', 
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not found' },
            security=["access_token"])
    @jwt_required
    def get(self, loci_id):
        """ Gets the FASTA sequence of the alleles from a particular loci from a particular species """

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))
        
        # find all alleles from the locus and return the sequence and id sorted by id
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select ?allele_id (str(?nucSeq) as ?nucSeq) '
                              'from <{0}> '
                              'where '
                              '{{ <{1}> a typon:Locus; typon:name ?name. '
                              '?alleles typon:isOfLocus <{1}> .'
                              '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .'
                              '?sequence typon:nucleotideSequence ?nucSeq. }} '
                              'order by ASC(?allele_id)'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))
        
        if result["results"]["bindings"] == []:
            return {"message": "No alleles found with the provided loci id."}, 404
        
        # sometimes virtuoso returns an error 
        # "Max row length is exceeded when trying to store a string of"
        # due to the sequences being too large,
        # if it happens there is a way around
        try:
            result["results"]["bindings"]
        
        except:
            #virtuoso returned an error, if it excedeed length request each allele one at a time
            if "Max row length is exceeded when trying to store a string of" in str(result):
                
                print ("sequence too long")
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                     ('select ?allele_id ?sequence '
                                      'from <{0}>'
                                      'where '
                                      '{{ <{1}> a typon:Locus; typon:name ?name. '
                                      '?alleles typon:isOfLocus <{1}> .'
                                      '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .}} '
                                      'order by ASC(?allele_id)'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))
                
                i = 0
                for seq in result["results"]["bindings"]:
                                         
                    result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                          ('select (str(?nucSeq) as ?nucSeq) '
                                           'from <{0}>'
                                           'where '
                                           '{{<{1}> typon:nucleotideSequence ?nucSeq. }}'.format(current_app.config['DEFAULTHGRAPH'], seq['sequence']['value'])))
                                         
                    realsequence = result2["results"]["bindings"][0]['nucSeq']['value']
                    
                    seq['nucSeq']={'value' : str(realsequence)}
                    #seq['nucSeq']['value']=str(realsequence)
                    
                    result["results"]["bindings"][i]['nucSeq'] = result2["results"]["bindings"][0]['nucSeq']
                    i += 1
                

                ## stream way to send data
                
                try:
                    def generate():
                        yield '{"Fasta": ['
                        
                        try:
                            prev_item = result["results"]["bindings"].pop(0)
                        
                        except:
                            yield ']}'
                        
                        for item in result["results"]["bindings"]:
                            yield json.dumps(prev_item) + ','
                            prev_item = item
                        
                        yield json.dumps(prev_item) + ']}'
                    
                    r = Response(stream_with_context(generate()), content_type='application/json')
                        
                    return Response(stream_with_context(generate()), content_type='application/json')
                    
                except:
                    return {"message" : "Empty man..."}
                return result["results"]["bindings"]
            
            #the query returned some error, retry it one last time
            time.sleep(1)
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                ('select ?allele_id (str(?nucSeq) as ?nucSeq) '
                                 'from <{0}>'
                                 'where '
                                 '{{ <{1}> a typon:Locus; typon:name ?name. '
                                 '?alleles typon:isOfLocus <{1}> .'
                                 '?alleles typon:hasSequence ?sequence; typon:id ?allele_id .'
                                 '?sequence typon:nucleotideSequence ?nucSeq. }} '
                                 'order by ASC(?allele_id)'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))            
                     
        try:
            def generate():
                yield '{"Fasta": ['
                
                try:
                    prev_item = result["results"]["bindings"].pop(0)
                
                except:
                    yield ']}'
                
                for item in result["results"]["bindings"]:
                    yield json.dumps(prev_item) + ','
                    prev_item = item
                    
                yield json.dumps(prev_item) + ']}'
            
            r = Response(stream_with_context(generate()), content_type='application/json')
                
            return r
            
        except:
            return {"message" : "Bad request"}, 400


@loci_conf.route('/<int:loci_id>/uniprot')
class LociNSUniprotAPItypon(Resource):
    """ Loci Uniprot Resource """


    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not found' },
        security=["access_token"])
    @jwt_required
    def get(self, loci_id):
        """ Gets Uniprot annotations for a particular loci from a particular species """

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))
        
        #get all uniprot labels and URI from all alleles of the selected locus
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select distinct (str(?UniprotLabel) as ?UniprotLabel) (str(?UniprotSName) as ?UniprotSName) (str(?UniprotURI) as ?UniprotURI) '
                              'from <{0}>'
                              'where '
                              '{{ <{1}> a typon:Locus; typon:name ?name. '
                              '?alleles typon:isOfLocus <{1}> .'
                              '?alleles typon:hasSequence ?sequence. '
                              'OPTIONAL{{?sequence typon:hasUniprotLabel ?UniprotLabel.}} '
                              'OPTIONAL{{?sequence typon:hasUniprotSName ?UniprotSName.}}'
                              'OPTIONAL{{?sequence typon:hasUniprotSequence ?UniprotURI }} }}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

        if result["results"]["bindings"] == []:
            return {"message": "No Uniprot annotations found with the provided loci id."}, 404

        
        try:
            def generate():
                
                yield '{"UniprotInfo": ['
                
                try:
                    prev_item = result["results"]["bindings"].pop(0)
                
                except:
                    yield ']}'
                
                for item in result["results"]["bindings"]:
                    if len(prev_item.keys())>0:
                        yield json.dumps(prev_item) + ','
                    prev_item = item
                
                yield json.dumps(prev_item) + ']}'
                
            return Response(stream_with_context(generate()), content_type='application/json')
            
        except:
            return {"message" : "Bad Argument"}, 400



@loci_conf.route("/<int:loci_id>/alleles")
class LociNSAlleles(Resource):
    """ Gets all alleles from a particular locus ID """

    parser = api.parser()
    parser.add_argument('species_name', 
                        type=str,
                        help="Species name")

    @api.doc(responses={ 200: 'OK', 
                        400: 'Invalid Argument',
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not Found' },
            security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, loci_id, **kwargs):
        """ Gets all alleles from a particular locus ID """

        # Get request data
        request_data = request.args

        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))

        #### ADD SPECIES NAME CHECK WITH UNIPROT QUERY!!!

        # if user provided a species name, filter the query to contain only that species
        try:
            request_data["species_name"]

            # get the taxon id from uniprot, if not found return 404
            query = ('PREFIX up:<http://purl.uniprot.org/core/> '
                     'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                     'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                     'SELECT ?taxon FROM <http://sparql.uniprot.org/taxonomy> WHERE'
                     '{{ ?taxon a up:Taxon; rdfs:subClassOf taxon:2; up:scientificName "{0}" .}}'.format(request_data["species_name"]))
            
            print("searching on uniprot..")
            
            # Check if species exists on uniprot 
            result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
            try:
                url = result2["results"]["bindings"][0]['taxon']['value']
            except:
                return {"message" : "species name not found on uniprot, search on http://www.uniprot.org/taxonomy/"}, 404 
            
            # check if species already exists locally (typon)
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('ASK where {{ ?species owl:sameAs <{0}>}}'.format(url)))
            
            if not result['boolean']:
                return {"message" : "Species does not exists in NS"}, 409

            # check if provided loci id exists 
            result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                        ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))
            
            if not result_loci['boolean']:
                return {"message" : "Locus not found"}, 404

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?alleles '
                                  'from <{0}> '
                                  'where '
                                  '{{ <{1}> a typon:Locus; typon:hasDefinedAllele ?alleles. '
                                  '?alleles typon:id ?id; typon:name ?name . '
                                  'FILTER CONTAINS(str(?name), "{2}")}}  '
                                  'ORDER BY ASC(?id)'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, request_data["species_name"])))

            try:
                
                if result["results"]["bindings"] == []:
                    return {"message" : "Allele not found or not added yet"}, 404

                else:    
                    return (result["results"]["bindings"]), 200
            
            except:
                return {"message" : "Allele not found"}, 404


        except:

            # check if provided loci id exists 
            result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                        ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))
            
            if not result_loci['boolean']:
                return {"message" : "Locus not found."}, 404

            #get list of alleles from that locus
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?alleles '
                                  'from <{0}> '
                                  'where '
                                  '{{ <{1}> a typon:Locus; typon:hasDefinedAllele ?alleles. '
                                  '?alleles typon:id ?id }}'
                                  'ORDER BY ASC(?id)'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))

            try:
                
                if result["results"]["bindings"] == []:
                    return {"message" : "Allele not found or not added yet."}, 404

                else:    
                    return (result["results"]["bindings"]), 200
            
            except:
                return {"message" : "Allele not found"}, 404

    


    @api.doc(responses={ 201: 'OK', 
                        400: 'Invalid Argument', 
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not found',
                        409: 'Conflict' },
            security=["access_token"])
    @api.expect(allele_list_model)
    @w.admin_required
    def post(self, loci_id):
        """ Add alleles to a loci of a species """

        # get user data
        c_user = get_jwt_identity()   
        
        # get post data
        post_data = request.get_json()
        
        try:
            aux.check_len(post_data['sequence'])
        except KeyError:
            pass
        
        enforceCDS = True
        try:
            if "False" in post_data['enforceCDS']:
                enforceCDS = False
        except:
            pass
            
        print("Enforce a cds: " + str(enforceCDS))
        
        #this is the user uri
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
        
        # get the taxon id from uniprot, if not found return 404
        species_name = str(post_data["species_name"])

        # if input is auto, the url to the Uniprot entry is provided
        species_name_url = aux.is_url(species_name)

        if post_data["input"] == "manual" and not species_name_url:

            query = ('PREFIX up:<http://purl.uniprot.org/core/> '
                     'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                     'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                     'SELECT ?taxon FROM <http://sparql.uniprot.org/taxonomy> WHERE'
                     '{{?taxon a up:Taxon; rdfs:subClassOf taxon:2; up:scientificName "{0}" .}}'.format(species_name))
            
            print("searching on uniprot if species exists...")
            
            # Check if species exists on uniprot 
            result_species = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
            
            try:
                url = result_species["results"]["bindings"][0]['taxon']['value']
            except:
                return {"message" : "species name not found on uniprot, search on http://www.uniprot.org/taxonomy/"}, 404 

        
        #check if locus exist (needs to be created before, hence the check)
        new_locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(loci_id))
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                              ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))
        
        if not result['boolean']:
            return {"message" : "Locus not found"}, 404
        
        if post_data["input"] == "link":

            try:

                sequence_uri = post_data["sequence_uri"]

                #get number of alleles for locus
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                        ('select (COUNT(?alleles) as ?count) '
                                         'from <{0}> '
                                         'where '
                                         '{{ ?alleles typon:isOfLocus <{1}>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url)))
                
                number_alleles_loci = int(result["results"]["bindings"][0]['count']['value'])
                new_allele_url = "{0}loci/{1}/alleles/{2}".format(current_app.config['BASE_URL'], 
                                                                  str(loci_id), 
                                                                  str(number_alleles_loci + 1))

                query2send = ('INSERT DATA IN GRAPH <{0}> '
                              '{{ <{1}> a typon:Allele; '
                              'typon:name "{2}"; '
                              'typon:sentBy  <{3}> ;'
                              'typon:isOfLocus <{4}>; '
                              'typon:dateEntered "{5}"^^xsd:dateTime; '
                              'typon:id "{6}"^^xsd:integer ; '
                              'typon:hasSequence <{7}>. '
                              '<{4}> typon:hasDefinedAllele <{1}>.}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                              new_allele_url,
                                                                              species_name,
                                                                              new_user_url,
                                                                              new_locus_url,
                                                                              str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')),
                                                                              str(number_alleles_loci+1),
                                                                              sequence_uri
                                                                              ))
        
                result = aux.send_data(query2send, 
                                       current_app.config['LOCAL_SPARQL'], 
                                       current_app.config['VIRTUOSO_USER'], 
                                       current_app.config['VIRTUOSO_PASS'])
                
                return {"message" : "New allele created with existing sequence"}, 201

            except:
                return {"message" : "Sequence uri not provided or something wrong"}, 418

        #sequences need to translate, that's the chewie way
        sequence = (str(post_data['sequence'])).upper()
        
        #sequence may no longer be translatable on user request, sad chewie :(
        sequenceIstranslatable = False
        #proteinSequence = ''
        #~ if enforceCDS:
        
        #will attempt to translate even if not enforced CDS
        #if translatable and enforce, ok
        #if translatable and not enforce, ok
        #if not translatable and enforce, error
        if post_data["input"] == "manual":
            print("trying to translate")
            try:
                proteinSequence = aux.translateSeq(sequence, False, enforceCDS)
                sequenceIstranslatable = True
                print(sequenceIstranslatable)
            except Exception as e:
                
                if enforceCDS:
                    return {"message" : "sequence failed to translate, not a CDS"}, 418
                else:
                    sequenceIstranslatable = False
                

        #check if sequence is already present on locus query
        query = ('select ?alleles '
                 'from <{0}> '
                 'where '
                 '{{ ?alleles typon:isOfLocus <{1}>; typon:hasSequence ?seq. '
                 '?seq a typon:Sequence; typon:nucleotideSequence "{2}"^^xsd:string.}}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                                                               new_locus_url, 
                                                                                               sequence))
        
        if len(sequence) > 9000:
            result = aux.send_big_query(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)
        else:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), query)
        
        #if sequence already exists on locus return the allele uri, if not create new sequence
        try:
            new_allele_url = result["results"]["bindings"][0]['alleles']['value']
            return {"message" : "Allele already exists at " + new_allele_url}, 409
    
        
        #sequence doesnt exist, create new and link to new allele uri. return the new allele uri
        except IndexError:
            
            
            ##check if sequence exists in uniprot only if the sequence was translatable
            if post_data["input"] == "manual":
               
                if sequenceIstranslatable:
                    add2send2graph = ''
                    print("check if in uniprot")
                    try:
                        
                        # query the uniprot sparql endpoint and build the RDF with the info on uniprot
                        proteinSequence = proteinSequence.replace("*", "")
                        query = ('PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> '
                                 'PREFIX up: <http://purl.uniprot.org/core/> '
                                 'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                                 'select ?seq ?label ?sname where '
                                 '{{ ?b a up:Simple_Sequence; rdf:value "{0}". ?seq up:sequence ?b. '
                                 'OPTIONAL {{?seq rdfs:label ?label.}} '
                                 'OPTIONAL {{?seq up:submittedName ?rname2. ?rname2 up:fullName ?sname.}} }}'
                                 'LIMIT 20'.format(proteinSequence))
                        
                        result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
                        
                        url = result2["results"]["bindings"][0]['seq']['value']
                        add2send2graph += '; typon:hasUniprotSequence <{0}>'.format(url)
                        try:
                            url2 = result2["results"]["bindings"][0]['label']['value']
                            url2 = aux.sanitize_input(url2)
                            add2send2graph += '; typon:hasUniprotLabel "{0}"^^xsd:string'.format(url2)
                        except:
                            print ("no label associated")
                            pass
                        try:
                            url3 = result["results"]["bindings"][0]['sname']['value']
                            url3 = aux.sanitize_input(url3)
                            add2send2graph += '; typon:hasUniprotSName "{0}"^^xsd:string'.format(url3)
                        except:
                            pass

                    #the sequence is not on uniprot or there was an error querying uniprot, just continue
                    except Exception as e:
                        add2send2graph = ''
                        pass
                        
                else:
                    add2send2graph = ''
            
            # Get the uniprot info if it's provided
            elif post_data["input"] == "auto":

                add2send2graph = ''

                try:
                    uniprot_url = post_data["uniprot_url"]
                    add2send2graph += '; typon:hasUniprotSequence <{0}>'.format(uniprot_url)

                    try:
                        uniprot_label = post_data["uniprot_label"]
                        uniprot_label = aux.sanitize_input(uniprot_label)
                        add2send2graph += '; typon:hasUniprotLabel "{0}"^^xsd:string'.format(uniprot_label)
                    except:
                        print("no label associated")
                        pass

                    try:
                        uniprot_sname = post_data["uniprot_sname"]
                        uniprot_sname = aux.sanitize_input(uniprot_sname)
                        add2send2graph += '; typon:hasUniprotSName "{0}"^^xsd:string'.format(uniprot_sname)
                    except:
                        pass
                #the sequence is not on uniprot, something went wrong
                except:
                    add2send2graph = ''                
                        
            #build the id of the sequence hashing it
            new_id = hashlib.sha256(sequence.encode('utf-8')).hexdigest()
            
            # build the remaining new seq uri
            new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(new_id))

            
            #check if the uri with the hash is already attributed
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                  ('ASK where {{ <{0}> typon:nucleotideSequence ?seq.}}'.format(new_seq_url)))
            
            print("check if hash is attributed")

            if result['boolean']:
                
                #check if the same sequence is attributed or there is a hash collision
                result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                      ('ASK where {{ <{0}> a typon:Sequence; '
                                       'typon:nucleotideSequence "{1}"^^xsd:string.}}'.format(new_seq_url, sequence)))
                
                #sequence was already attributed to the exact same sequence, reusing it
                if result['boolean']:
                    
                    # celery task
                    task = add_allele.apply(args=[new_locus_url, species_name, loci_id, new_user_url, new_seq_url, False, add2send2graph, sequence])
                    
                    process_result = task.result
                    
                    process_ran = task.ready()
                    process_sucess = task.status
                    
                    if process_ran and process_sucess == "SUCCESS":
                        pass
                    else:
                        return "status: " + str(process_sucess) + " run:" + str(process_ran), 400
                    
                    # celery result
                    process_result = task.result
                    print(process_result)
                    new_allele_url = process_result[0]
                    process_result_status_code = int(process_result[-1])

                    if process_result_status_code == 418 :
                        
                        #check if process was sucessfull
                        return {"message" : "Sequence was already attributed to a loci/allele"}, 418
                    
                    elif process_result_status_code > 201 :
                        
                        #check if process was sucessfull
                        return {"message" : "Sum Thing Wong creating sequence 3"}, process_result_status_code
                    
                    else:
                        return new_allele_url, process_result_status_code
                    
                # attention, there was a hash collision!!!!1111111 a different sequence was attributed to the same hash
                else:
                    return {"message" : ("URI {0} already has sequence {1} with that hash, contact the admin!".format(new_seq_url, sequence))}, 409
            
            #the hash is not yet attributed
            else:
                # celery task
                task = add_allele.apply(args=[new_locus_url, species_name, loci_id, new_user_url, new_seq_url, True, add2send2graph, sequence])
                                 
                process_ran = task.ready()
                process_sucess = task.status
                
                if process_ran and process_sucess == "SUCCESS":
                    pass
                else:
                    return ("status: {0} run: {1}".format(str(process_sucess), str(process_ran))), 400

                # celery result
                process_result = task.result
                print(process_result)
                new_allele_url = process_result[0]
                process_result_status_code = int(process_result[-1])
                
                if process_result_status_code > 201 :
                    
                    #check if process was sucessfull
                    return {"message" : "Sum Thing Wong creating sequence 4"}, process_result_status_code
                else:
                    return new_allele_url, process_result_status_code

        ######?      
        except Exception as e:
            print ('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))
            print (e)
            return "Sum Thing Wong creating sequence", 400


@loci_conf.route("/<int:loci_id>/alleles/<int:allele_id>")
class AlleleNSAPItypon(Resource):
    """ Allele List Resource """
    
    @api.doc(responses={ 200: 'OK', 
                    400: 'Invalid Argument', 
                    500: 'Internal Server Error', 
                    403: 'Unauthorized', 
                    401: 'Unauthenticated',
                    404: 'Not found' },
            security=["access_token"])
    @jwt_required
    def get(self, loci_id, allele_id):
        """ Gets a particular allele from a particular loci """
        
        new_allele_url = "{0}loci/{1}/alleles/{2}".format(current_app.config['BASE_URL'], str(loci_id), str(allele_id))

        # check if provided loci id exists
        new_locus_url = '{0}loci/{1}'.format(current_app.config['BASE_URL'], str(loci_id))
        result_loci = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                  ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))
            
        if not result_loci['boolean']:
            return {"message" : "Locus not found."}, 404
        
        #get information on allele, sequence, submission date, id and number of isolates with this allele
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select ?sequence (str(?name) as ?source) ?date ?id (COUNT(?isolate) as ?isolate_count) '
                              'from <{0}> '
                              'where '
                              '{{ <{1}> a typon:Allele; typon:name ?name; typon:dateEntered ?date; typon:hasSequence ?sequence; typon:id ?id. '
                              'OPTIONAL {{?isolate a typon:Isolate; typon:hasAllele <{1}>}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_allele_url)))
        

        if result["results"]["bindings"] == []:
            return 	{"message" : "No allele found with the provided id."}, 404

        else:
            return (result["results"]["bindings"])
            
            




############################################## Schema Routes

# Namespace
species_conf = api.namespace('species', description = 'species related operations')

sequences_conf = api.namespace('sequences', description = "sequence related operations")

species_model = api.model("SpeciesModel", {
    'name': fields.String(required=True, description="Name of the species to add.")
})

schema_model = api.model("SchemaModel", {
    'name': fields.String(required=True, description="Name of the schema to add."),
    'bsr': fields.String(required=True, description="Blast Score Ratio used to create the schema."),
    'ptf': fields.String(required=True, description="Link to the Prodigal training file used to create the schema"),
    'translation_table': fields.String(required=True, description="Translation table used to create the schema."),
    'min_locus_len': fields.String(required=True, description="Minimum locus length used to create the schema."),
    'chewBBACA_version': fields.String(required=True, description="Version of chewBBACA used to create the schema.") 
})

schema_loci_model = api.model("SchemaLociModel", {
    'loci_id' : fields.String(required = True, description = "Id of the loci")
})

loci_list_model = api.model("LociListModel", {
    'locus_id' : fields.String(required = True, description = "ID of the locus")    
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

allele_model = api.model("AlleleModel", {
    'locus_id' : fields.String(required = True, description = "ID of the locus"),
    'allele_id' : fields.String(required = True, description = "The ID of the allele in NS")
})

profile_model = api.model("ProfileModel", {
    'profile' : fields.Raw(required=True, description="AlleleCall profile"),
    'headers' : fields.Raw(required=True, description="Headers of the profile file")
})

############################################################

@species_conf.route('/list') 
class SpeciesListAPItypon(Resource):
    """ Species List Resource"""

    # Define extra arguments for requests
    parser = api.parser()
    
    parser.add_argument('species_name', 
                        type=str,
                        help='Name of the species')
    
    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument',
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, **kwargs):
        """ Get a list of all species on Typon """

        try:
            request_data["species_name"]
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                                    'select ?species ?name '
                                    'from <{0}> '
                                    'where '
                                    '{{ ?species owl:sameAs ?species2; '
                                    'a <http://purl.uniprot.org/core/Taxon>; typon:name "{1}"^^xsd:string. }}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                                                                                      request_data["species_name"])))

            if result["results"]["bindings"] == []:
                return {"message": "Species not found."}, 404
            
            else:
                return (result["results"]["bindings"])

        except:
            #get all species
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#>' 
                                    'select ?species ?name '
                                    'from <{0}> '
                                    'where '
                                    '{{ ?species owl:sameAs ?species2; '
                                    'a <http://purl.uniprot.org/core/Taxon>; typon:name ?name. }}'.format(current_app.config['DEFAULTHGRAPH'])))

            if result["results"]["bindings"] == []:
                return {"message": "No species have been added yet"}, 404

            else:
                return (result["results"]["bindings"])
    
    
    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument',
                         500: 'Internal Server Error',
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         409: 'Species already exists',
                         404: 'Species name not found on uniprot' 
                         },
             security=["access_token"])
    @api.expect(species_model, validate=True)
    @w.admin_required
    def post(self):
        """ Add a new species to Typon """

        # get user data
        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()

        # get species name from the post data
        name = str(post_data["name"])
            
        try:
            
            # Check user role in Typon
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
            
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                                  'ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; '
                                  'typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))

            if not result['boolean']:
                return {"message" : "not authorized, admin only"}, 403
        
        except:
            return {"message" : "not authorized, admin only"}, 403

        
        # get number of taxon already on the graph
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select (COUNT(?taxon) as ?count) '
                              'from <{0}> '
                              'where '
                              '{{ ?taxon a <http://purl.uniprot.org/core/Taxon> }}'.format(current_app.config['DEFAULTHGRAPH'])))

        
        number_taxon = int(result["results"]["bindings"][0]['count']['value'])
        
        # get the taxon id from uniprot, if not found return 404
        query = ('PREFIX up:<http://purl.uniprot.org/core/> '
                 'PREFIX taxon:<http://purl.uniprot.org/taxonomy/> '
                 'PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> '
                 'SELECT ?taxon FROM <http://sparql.uniprot.org/taxonomy> WHERE'
                 '{{	?taxon a up:Taxon; rdfs:subClassOf taxon:2; up:scientificName "{0}" .}}'.format(name))
        
        print("searching on uniprot..")
        
        # Check if species exists on uniprot 
        result2 = aux.get_data(SPARQLWrapper(current_app.config['UNIPROT_SPARQL']), query)
        try:
            url = result2["results"]["bindings"][0]['taxon']['value']
        except:
            return {"message" : "species name not found on uniprot, search on http://www.uniprot.org/taxonomy/"}, 404 
        
        # check if species already exists locally (typon)
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('ASK where {{ ?species owl:sameAs <{0}>}}'.format(url)))
        
        if result['boolean']:
            return {"message" : "Species already exists"}, 409
        
        # species exists on uniprot, everything ok to create new species
        new_spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(number_taxon + 1))
        
        data2send = ('PREFIX typon:<http://purl.phyloviz.net/ontology/typon#> '
                     'INSERT DATA IN GRAPH <{0}> '
                     '{{ <{1}> owl:sameAs <{2}>; typon:name "{3}"^^xsd:string; a <http://purl.uniprot.org/core/Taxon>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_spec_url, url, name))

        # return {"msg": data2send,
        #          "msg2": name}

        #result = aux.send_data(data2send, current_app.config['URL_SEND_LOCAL_VIRTUOSO'], current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
        #result = aux.send_data(data2send, 'http://172.19.1.3:8890/DAV/test_folder/data', current_app.config['VIRTUOSO_USER'], current_app.config['VIRTUOSO_PASS'])
        result = aux.send_data(data2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])

        if result.status_code in [200, 201]:
            return {"message" : "Species created"}, 201

        else:
            return {"message" :"Sum Thing Wong",
                    "msg": result.text}, result.status_code



@species_conf.route('/<int:species_id>') 
class SpeciesAPItypon(Resource):
    """ Species Resource """

    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
            security=["access_token"])
    @jwt_required
    def get(self, species_id):
        """ Returns the species corresponding to the given id """

        url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))


        # get species name and its schemas
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                ('select ?species ?name ?schemas ?schemaName '
                                'from <{0}> '
                                'where '
                                '{{ {{<{1}> owl:sameAs ?species; typon:name ?name.}} '
                                'UNION {{ ?schemas typon:isFromTaxon <{1}>; a typon:Schema; typon:schemaName ?schemaName. '
                                'FILTER NOT EXISTS {{ ?schemas typon:deprecated  "true"^^xsd:boolean }} }} }}'.format(current_app.config['DEFAULTHGRAPH'], url)))

        if result["results"]["bindings"] == []:
            return {"message": "No species found with the provided id."}, 404

        else:    
            return (result["results"]["bindings"])
        
        # else:
        #     return {"message" : "Unauthorized"}, 403



@species_conf.route('/<int:species_id>/profiles')
class SpeciesProfiles(Resource):
    """ AlleleCall Profiles Resources
    """

    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found',
                         409: 'Conflict' },
            security=["access_token"])
    @api.expect(profile_model)
    @jwt_required
    def post(self, species_id):
        """ Add a an allele call profile
        """
        
        # get user data
        c_user = get_jwt_identity()
                
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result['boolean']:
                return {"message" : "Not authorized, admin only"}, 403
        
        except:
            return {"message" : "Not authorized, admin only"}, 403

        
        # get post data
        post_data = request.get_json()

        if not post_data:
            return {"message" : "No profile provided"}, 400

        profile_dict = post_data["profile"]
        headers = post_data["headers"]

        species_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))

        dict_genes = {}

        #get all locus from the species and their respective name, to compare to the name of the locus from the profile the user sent
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('select (str(?originalName) as ?originalName) ?locus '
                              'from <{0}> '
                              'where '
                              '{{?locus a typon:Locus; typon:isOfTaxon <{1}>; typon:originalName ?originalName. }}'.format(current_app.config['DEFAULTHGRAPH'], 
                                                                                                                           species_url)))
        
        for gene in result["results"]["bindings"]:
            dict_genes[str(gene['originalName']['value'])] = str(gene['locus']['value'])

        genome_name = next(iter(profile_dict))

        #create the new isolate id for the uri
        nameWdata2hash = genome_name + str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
        new_isolate_id = hashlib.sha256(nameWdata2hash.encode('utf-8')).hexdigest()
        
        rdf_2_ins = ('PREFIX typon: <http://purl.phyloviz.net/ontology/typon#> \nINSERT DATA IN GRAPH <{0}> {{\n'.format(current_app.config['DEFAULTHGRAPH']))

        isolateUri = "{0}/isolates/{1}".format(species_url, str(new_isolate_id))

        # Check if isolate already exists
        check_result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                   ('ASK where {{ <{0}> a typon:Isolate }}'.format(isolateUri)))

        if not check_result['boolean']:
            return {"message" : "Isolate already exists"}, 409


        rdf_2_ins += ('<{0}> a typon:Isolate;\ntypon:name "{1}"^^xsd:string; typon:sentBy <{2}>;'
                      ' typon:dateEntered "{3}"^^xsd:dateTime; typon:isFromTaxon <{4}>;'.format(isolateUri, 
                                                                                                genome_name, 
                                                                                                new_user_url, 
                                                                                                str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')), 
                                                                                                species_url))
        i = 0
        hasAlleles = 0

        #build the rdf with all alleles
        while i < len(profile_dict[genome_name]):
            gene = headers[i+1]
            
            #get the allele id
            try:
                allele = int(profile_dict[genome_name][i])
                
            except:
                i += 1
                continue

            #get the locus uri
            try:
                loci_uri = dict_genes[headers[i+1]]
            except:
                return {"message" : ("{0} locus was not found, profile not uploaded".format(str(headers[i+1])))}, 404
                                
            #check if allele exists
            allele_uri = "{0}/alleles/{1}".format(loci_uri, str(allele))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('ASK where {{ <{0}> a typon:Locus; typon:hasDefinedAllele <{1}> }}'.format(loci_uri, allele_uri)))
            if result['boolean']:
                
                rdf_2_ins += '\ntypon:hasAllele <{0}>;'.format(allele_uri)
                hasAlleles += 1
                
            i += 1
        
        #if the genome has alleles, send the rdf
        if hasAlleles > 0:

            #remove last semicolon from rdf and close the brackets
            rdf_2_ins = rdf_2_ins[:-1]
            
            rdf_2_ins += ".}"                
            
            #add to the queue to send the profile
            task = add_profile.apply(args=[rdf_2_ins])
                
            process_result = task.result
            
            process_ran = task.ready()
            process_sucess = task.status
            
            if process_ran and process_sucess == "SUCCESS":
                pass
            else:
                return  "status: " + " run:"
            
            process_result=task.result
            print(process_result)
            process_result_status_code=int(process_result[-1])
                            
            print (genome_name, str(process_result_status_code))
            
            if process_result_status_code > 201:
                return {"message": "Profile not uploaded, try again "} , process_result_status_code
            else:
                return {"message": "Profile successfully uploaded at " + isolateUri} , process_result_status_code
            
        else:
            return {"message" : "Profile not uploaded, no alleles to send at {0}".format(isolateUri)}, 200


@species_conf.route('/<int:species_id>/schemas') 
class SchemaListAPItypon(Resource):
    """ Schema List Resource """
        
    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
            security=["access_token"])
    @jwt_required
    def get(self, species_id):
        """ Get the schemas for a particular species ID """

        species_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                ('select ?schemas ?name '
                                'from <{0}> '
                                'where '
                                '{{ ?schemas a typon:Schema; typon:isFromTaxon <{1}>; typon:schemaName ?name. '
                                'FILTER NOT EXISTS {{ ?schemas typon:deprecated  "true"^^xsd:boolean }} }}'.format(current_app.config['DEFAULTHGRAPH'], species_url)))
        try:

            if result["results"]["bindings"] == []:
                return {"message" : "No schemas added yet for this species"}, 200
            
            else:
                return result["results"]["bindings"]
        
        except:
            return {"message" : "It's empty man...."}, 404



    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found',
                         406: 'Not acceptable' },
            security=["access_token"])
    @api.expect(schema_model, validate=True)
    @w.admin_contributor_required
    def post(self, species_id):
        """ Adds a new to schema for a particular species ID """

        c_user = get_jwt_identity()

        ### get post data
        post_data = request.get_json()
        
        # schema name
        name = str(post_data["name"])
        # blast score ratio
        bsr = str(post_data["bsr"])
        # prodigal training file
        ptf = str(post_data["ptf"])
        # translation table
        translation_table = str(post_data["translation_table"])
        # minimum locus length
        min_locus_len = str(post_data["min_locus_len"])
        # chewBBACA_version
        chewie_version = str(post_data["chewBBACA_version"])
        
        if "" in (name, bsr, ptf, translation_table, min_locus_len, chewie_version):
            return {"message": "No schema parameters specified."}, 406

        # check if species exists
        species_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('ASK where {{ <{0}> a <http://purl.uniprot.org/core/Taxon>}}'.format(species_url)))
        
        if not result['boolean']:
            return {"message" : "Species doesn't exist"}, 404
        
        # check if a schema already exists with this description for this species
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ ?schema a typon:Schema; typon:isFromTaxon <{0}>; typon:schemaName "{1}"^^xsd:string .}}'.format(species_url, name)))
        if result['boolean']:
            
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                ('select ?schema '
                                 'from <{0}> '
                                 'where {{?schema a typon:Schema; typon:isFromTaxon <{1}>; typon:schemaName "{2}"^^xsd:string .}}'.format(current_app.config['DEFAULTHGRAPH'], species_url, name)))
            
            schema_url = result["results"]["bindings"][0]['schema']['value']
            
            return {"message" : "schema with that description already exists {0}".format(schema_url)}, 409
        
        # only users with role Admin or Contributor can do this
        # TODO: need to change SPARQL query to include Contributor role
        try:
            # new_user_url = current_app.config['BASE_URL'] + "users/" + str(c_user.id)
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result['boolean']:
                return {"message" : "not authorized, admin only"}, 403
                
        except:
            return {"message" : "not authorized, admin only"}, 403

        
        # only user 1 can add schemas, change at your discretion
        # TODO: Add SPARQL query to check if the user is modifying their schemas
        
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
        
        # count number of schemas on the server for the uri build and send data to server
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select (COUNT(?schemas) as ?count) '
                              'from <{0}> '
                              'where '
                              '{{ ?schemas a typon:Schema;typon:isFromTaxon <{1}>. }}'.format(current_app.config['DEFAULTHGRAPH'], species_url)))
        
        number_schemas = int(result["results"]["bindings"][0]['count']['value'])
        
        # Create the uri for the new schema
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(number_schemas + 1))

        # The SPARQL query to send to Typon
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> a typon:Schema; typon:isFromTaxon <{2}>; '
                      'typon:administratedBy <{3}>; typon:schemaName "{4}"^^xsd:string; '
                      'typon:bsr "{5}"^^xsd:string; typon:chewBBACA_version "{6}"^^xsd:string; '
                      'typon:ptf "{7}"^^xsd:string; typon:translation_table "{8}"^^xsd:string; '
                      'typon:minimum_locus_length "{9}"^^xsd:string .}}'.format(current_app.config['DEFAULTHGRAPH'],
                                                                               new_schema_url,
                                                                               species_url,
                                                                               new_user_url,
                                                                               name, 
                                                                               bsr,
                                                                               chewie_version,
                                                                               ptf,
                                                                               translation_table,
                                                                               min_locus_len))
    
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])
        
        if result.status_code in [200, 201]:
            return {"message" : "A new schema for {0} was created sucessfully".format(species_url),
                    "url" : new_schema_url}, 201
        
        else:
            return {"message" : "Sum Thing Wong"}, result.status_code



@species_conf.route('/<int:species_id>/schemas/<int:schema_id>') 
class SchemaAPItypon(Resource):
    """ Schema List Resource """
    
    @api.doc(responses={ 200: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
             security=["access_token"])
    @jwt_required
    def get(self, species_id, schema_id):
        """ Return a particular schema for a particular species """

        
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], 
                                                                str(species_id), 
                                                                str(schema_id))
        
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                ('ASK where {{ <{0}> typon:deprecated "true"^^xsd:boolean.}}'.format(new_schema_url)))
        if result['boolean']:
            return {"message" : "Schema is now deprecated"}, 200
            
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                ('select (str(?description) as ?name) '
                                '(str(?bsr) as ?bsr) (str(?chewBBACA_version) as ?chewBBACA_version) '
                                '(str(?ptf) as ?prodigal_training_file) (str(?trans) as ?translation_table) '
                                '(str(?min_locus_len) as ?minimum_locus_length) '
                                'from <{0}> '
                                'where '
                                '{{ <{1}> typon:schemaName ?description; '
                                'typon:bsr ?bsr; typon:chewBBACA_version ?chewBBACA_version; typon:ptf ?ptf; '
                                'typon:translation_table ?trans; typon:minimum_locus_length ?min_locus_len. }}'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))
        
        if result["results"]["bindings"] == []:
            return {"message": "Schema not found with provided id."}, 404
        
        else:
            finalresult = result["results"]["bindings"]
            return (finalresult)
                    
    # it doesnt delete, it just adds an attribute typon:deprecated  "true"^^xsd:boolean to that part of the schema, 
    # the locus is just "removed" for the specific schema!!!11
    
    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
            security=["access_token"])
    @w.admin_required
    def delete(self, species_id, schema_id):
        """ Deletes a particular schema for a particular species """

        c_user = get_jwt_identity()
                
        #only admin can do this
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result['boolean']:
                return {"message" : "not authorized, admin only"}, 403
                
        except:
            return {"message" : "not authorized, admin only"}, 403
        
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
        
        #check if schema exists
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))
        
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>.}}'.format(new_schema_url, new_user_url)))
        
        if not result['boolean']:
            return {"message" : "Schema not found or schema is not yours"}, 404
        
        
        #add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:deprecated "true"^^xsd:boolean.}}'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url))
        
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])
        
        if result.status_code in [200, 201] :
            return {"message" : "Schema sucessfully removed."}, 201	
        
        else:
            return {"message" : "Sum Thing Wong"}, result.status_code


### DOWNLOAD SCHEMA ENDPOINT (WIP)
# @species_conf.route('/<int:species_id>/schemas/<int:schema_id>/compressed') 
# class SchemaZipAPItypon(Resource):
#     """ Schema Zip Resource """
    
#     @api.doc(responses={ 200: 'OK',
#                          400: 'Invalid Argument', 
#                          500: 'Internal Server Error', 
#                          403: 'Unauthorized', 
#                          401: 'Unauthenticated' },
#             security="apikey")
#     #@w.auth_required(one_of=["Admin", "Contributor", "User"])
#     @w.token_required
#     #@login_required
#     def get(self, species_id, schema_id):
#         """ Download the schema as a compressed file """
        
# 		#check if schema exists
#         new_schema_url = current_app.config['BASE_URL'] + "species/" + str(species_id) + "/schemas/" + str(schema_id)
#         result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select ?description (COUNT(?part) as ?number_loci) where { <' + new_schema_url + '> typon:schemaName ?description; typon:hasSchemaPart ?part. FILTER NOT EXISTS { <' + new_schema_url + '> typon:deprecated  "true"^^xsd:boolean }}')
#         #print(result)
#         try:
#             schema_name = result["results"]["bindings"][0]["description"]["value"]
#             #print(schema_name)
            
#         except:
#             return {"message" : "Schema not found"}, 404

#         # get the number of loci
#         nr_loci_request = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select ?description (COUNT(?part) as ?number_loci) where { <' + new_schema_url + '> typon:schemaName ?description; typon:hasSchemaPart ?part. }')
        
#         nr_loci = nr_loci_request["results"]["bindings"][0]["number_loci"]["value"]

#         # get the fasta

#         #fasta_uri = "http://127.0.0.1:5000/NS/api/species/" + str(species_id) + "/loci/"

#         #new_locus_url = current_app.config['BASE_URL'] + "species/" + str(species_id) + "/loci/" + str(loci)
#         new_locus_url = current_app.config['BASE_URL'] + "species/" + str(species_id) + "/loci/1"

#         fasta_r = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select ?allele_id (str(?nucSeq) as ?nucSeq) where { <' + new_locus_url + '> a typon:Locus; typon:name ?name. ?alleles typon:isOfLocus <' + new_locus_url + '> .?alleles typon:hasSequence ?sequence; typon:id ?allele_id .?sequence typon:nucleotideSequence ?nucSeq. } order by ASC(?allele_id)')

#         print(fasta_r["results"]["bindings"][0]["nucSeq"]["value"])


#         #for loci in range(1, nr_loci + 1):

#         #fasta_loci_uri = fasta_uri + str(loci) + "/fasta"
#         # fasta_loci_uri = fasta_uri + "1/fasta"

#         # waitFactor = 2
#         #attempts=0

#         # fasta_r = requests.get(fasta_loci_uri, timeout=10)
        
#         # if fasta_r.status_code > 201:
#         #     time.sleep(waitFactor)

#         # fasta_r_result = fasta_r.text
#         # print(fasta_r_result)


# 		# #build the dowload path
#         # down_folder = os.path.join(app.config['DOWNLOAD_FOLDER'], str(species_id), str(schema_id))
        
#         # zippath = os.path.join(down_folder, "schema_" + schema_name + ".zip")
        
#         # if os.path.isfile(zippath):
#         #     return send_from_directory(down_folder, "schema_" + schema_name + ".zip", as_attachment=True)
        
#         # else:
#         #     return {"message" : "File doesn't exist"}, 404


@species_conf.route('/<int:species_id>/schemas/<int:schema_id>/loci')
class SchemaLociAPItypon(Resource):
    """ Schema Loci Resource """

    # Define extra arguments for requests
    parser = api.parser()
    
    parser.add_argument('date', 
                        type=str,
                        help='provide a date in the format YYYY-MM-DDTHH:MM:SS to get the alleles that were uploaded after that defined date')



    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument',
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
            security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, schema_id, **kwargs):
        """ Returns the loci of a particular schema from a particular species """
        
        # get request data
        request_data = request.args
        
        #check if schema exists or deprecated
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))
        
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('ASK where {{ <{0}> a typon:Schema; typon:deprecated  "true"^^xsd:boolean }}'.format(new_schema_url)))
        
        if result['boolean']:
            return {"message" : "Schema not found or deprecated"}, 404
        
        # if date is provided the request returns the alleles that were added after that specific date for all loci
        # else the request returns the list of loci
        # a correct request returns also the server date at which the request was done
        try: 
            
            request_data["date"]
            
            #query all alleles for the loci of the schema since a specific date, sorted from oldest to newest (limit of max 50k records)
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?locus_name ?allele_id ?sequence '
                                 'from <{0}> '
                                 'where {{ '
                                 ' {{ select ?locus_name ?allele_id ?sequence '
                                 'from <{0}> '
                                 'where {{ <{1}> typon:hasSchemaPart ?part. '
                                 '?part typon:hasLocus ?locus . '
                                 '?alleles typon:isOfLocus ?locus ; typon:dateEntered ?date; typon:hasSequence ?sequence; typon:id ?allele_id. '
                                 '?locus typon:name ?locus_name. '
                                 'FILTER ( ?date > "{2}"^^xsd:dateTime ). '
                                 'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}}'
                                 'order by ASC(?date)}} }} LIMIT 50000'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url, request_data["date"])))
            
            if len(result["results"]["bindings"])<1:
                
                def generate():
                    yield '{"newAlleles": []}'
                r = Response(stream_with_context(generate()), content_type='application/json')
                r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
                return r
            
            #get the latest allele date (the newest)
            latestAllele = (result["results"]["bindings"])[-1]
            geneFasta = latestAllele['locus_name']['value']
            alleleid = latestAllele['allele_id']['value']
            result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('select ?date from <{0}> '
                                   'where '
                                   '{{ ?locus typon:name "{1}"^^<http://www.w3.org/2001/XMLSchema#string>. '
                                   '?alleles typon:isOfLocus ?locus ; typon:dateEntered ?date; typon:id {2}. }}'.format(current_app.config['DEFAULTHGRAPH'], geneFasta, alleleid)))
            
            latestDatetime = (result2["results"]["bindings"])[0]['date']['value']
            
            number_of_alleles = len(result["results"]["bindings"])
            try:
                
                def generate():
                    yield '{"newAlleles": ['
                    
                    try:
                        prev_item = result["results"]["bindings"].pop(0)
                    except:
                        yield ']}'

                    for item in result["results"]["bindings"]:
                        yield json.dumps(prev_item) + ','
                        prev_item = item
                    
                    yield json.dumps(prev_item) + ']}'
                    
                r = Response(stream_with_context(generate()), content_type='application/json')
                r.headers.set('Last-Allele', latestDatetime)
                if number_of_alleles > 49999:
                    r.headers.set('All-Alleles-Returned', True)
                else:
                    r.headers.set('All-Alleles-Returned', False)
                return r
                
            except:
                
                def generate():
                    yield '{"newAlleles": []}'
                
                r = Response(stream_with_context(generate()), content_type='application/json')
                r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
                return r
        
        #if no date provided, query for all loci for the schema
        except:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?locus (str(?name) as ?name) (str(?original_name) as ?original_name)'
                                  'from <{0}> '
                                  'where '
                                  '{{ <{1}> typon:hasSchemaPart ?part. '
                                  '?part typon:hasLocus ?locus.'
                                  '?locus typon:name ?name ; typon:originalName ?original_name. '
                                  'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }} }}'
                                  'order by (?name) '.format(current_app.config['DEFAULTHGRAPH'], new_schema_url)))

            # check if schema has loci
            try:      
                result["results"]["bindings"][0]
            except:
                return {"message" : "Schema exists but does not have loci yet."}, 200

            #return all loci in stream mode
            try:
                
                latestDatetime = str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f'))
                
                def generate():
                    yield '{"Loci": ['
                    
                    try:
                        prev_item = result["results"]["bindings"].pop(0)
                    except:
                        yield ']}'
                    
                    for item in result["results"]["bindings"]:
                        yield json.dumps(prev_item) + ','
                        prev_item = item
                    
                    yield json.dumps(prev_item) + ']}'
                    
                r = Response(stream_with_context(generate()), content_type='application/json')
                r.headers.set('Server-Date',latestDatetime)
                return r
                
            except :
                return {"message" : "Invalid Argument"}, 400

        


    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not found',
                         409: 'Locus already on schema' },
             security=["access_token"])
    @api.expect(schema_loci_model)
    @w.admin_contributor_required
    def post(self, species_id, schema_id):
        """ Add loci to a particular schema of a particular species """

        c_user = get_jwt_identity()

        # get post data
        request_data = request.get_json()

        try:
            request_data["loci_id"]

        except:
            return {"message" : "No valid id for loci provided"}, 404

        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
        
        #check if schema exists
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>;'
                              ' typon:deprecated "true"^^xsd:boolean }}'.format(new_schema_url, new_user_url)))
        
        if result['boolean']:
            return {"message" : "Schema not found or schema is not yours"}, 404
        
        #check if locus exists
        # new_locus_url = current_app.config['BASE_URL'] + "species/" + str(species_id) + "/loci/" + str(request_data["loci_id"])
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'ASK where { <' + new_locus_url + '> a typon:Locus}')
        # if not result['boolean']:
        #     return {"message" : "Locus not found"}, 404

        #check if locus exists
        # new_locus_url = current_app.config['BASE_URL'] + "loci/" + str(request_data["loci_id"])
        new_locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(request_data["loci_id"]))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ <{0}> a typon:Locus}}'.format(new_locus_url)))
        
        if not result['boolean']:
            return {"message" : "Locus not found"}, 404
        
        #check if locus already exists on schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ <{0}> typon:hasSchemaPart ?part. '
                              '?part typon:hasLocus <{1}>.}}'.format(new_schema_url, new_locus_url)))
        
        if result['boolean']:
            return {"message" : "Locus already on schema",
                    "locus_url" : new_locus_url}, 409
                
        #get the number of loci on schema and build the uri based on that number+1 , using a celery queue
        task = add_locus_schema.apply(args=[new_schema_url, new_locus_url])
        
        process_result = task.result
        
        process_ran = task.ready()
        process_sucess = task.status
        
        if process_ran and process_sucess == "SUCCESS":
            pass
        else:
            return {"status: " + process_sucess + " run:" + process_ran}, 400
        
        # celery results
        process_result = task.result
        print(process_result)
        new_allele_url = process_result[0]
        process_result_status_code = int(process_result[-1])
        
        if process_result_status_code > 201 :
            #check if process was sucessfull
            return {"message" : "Sum Thing Wong creating sequence 2"}, process_result_status_code
        
        else:
            return new_allele_url, process_result_status_code
    


    @api.doc(responses={ 201: 'OK', 
                        400: 'Invalid Argument', 
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not found' },
            security=["access_token"])
    @w.use_kwargs(api, parser)
    @w.admin_required
    def delete(self, species_id, schema_id):
        """ Delete loci to a particular schema of a particular species """
        
        # it doesnt delete, it just adds an attribute typon:deprecated  "true"^^xsd:boolean to that part of the schema, 
        # the locus is just "removed" for the specific schema!!!11

        c_user = get_jwt_identity()

        # get post data
        request_data = request.args

        try:
            request_data["loci_id"]

        except:
            return {"message" : "No valid id for loci provided"}, 404	
                    
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; '
                                  'typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result['boolean']:
                return {"message" : "Not authorized, admin only"}, 403
        except:
            return {"message" : "Not authorized, admin only"}, 403
            
        
        new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))
        
        # check if schema exists
        new_schema_url = "{0}species/{1}/schemas/{2}".format(current_app.config['BASE_URL'], str(species_id), str(schema_id))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('ASK where {{ <{0}> a typon:Schema; typon:administratedBy <{1}>;'
                              ' typon:deprecated  "true"^^xsd:boolean }}'.format(new_schema_url, new_user_url)))
        
        if not result['boolean']:
            return {"message" : "Schema not found or schema is not yours"}, 404
        
        # check if locus exists
        new_locus_url = "{0}species/{1}/loci/{2}".format(current_app.config['BASE_URL'], str(species_id), str(request_data["loci_id"]))

        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('ASK where {{ <{0}> a typon:Locus}}'.format(new_locus_url)))
        
        if not result['boolean']:
            return {"message" : "Locus not found"}, 404
        
        # check if locus exists on schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('ASK where {{ <{0}> typon:hasSchemaPart ?part. '
                              '?part typon:hasLocus <{1}>. '
                              'FILTER NOT EXISTS {{ ?part typon:deprecated  "true"^^xsd:boolean }}.}}'.format(new_schema_url, new_locus_url)))
        
        if not result['boolean']:
            return {"message" : "Locus already on schema"}, 409
            
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                             ('select ?parts '
                              'from <{0}> '
                              'where '
                              '{{ <{1}> typon:hasSchemaPart ?parts. '
                              '?parts typon:hasLocus <{2}>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_schema_url, new_locus_url)))
        
        schema_link = result["results"]["bindings"][0]['parts']['value']
                        
        
        #add a triple to the link between the schema and the locus implying that the locus is deprecated for that schema
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> typon:deprecated "true"^^xsd:boolean.}}'.format(current_app.config['DEFAULTHGRAPH'], schema_link))
        
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])
        
        if result.status_code in [200, 201]:
            return {"message" : "Locus sucessfully removed from schema"}, 201
            
        else:
            return {"message" : "Sum Thing Wong"}, result.status_code



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

    
    @api.doc(responses={ 200: 'OK', 
                    400: 'Invalid Argument', 
                    500: 'Internal Server Error', 
                    403: 'Unauthorized', 
                    401: 'Unauthenticated',
                    404: 'Not found' },
        security=["access_token"])
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, species_id, **kwargs):
        """ Lists the loci of a particular species """

        # get the request data
        request_data = request.args
        
        # build the species uri
        spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
        
        #sequence was provided, return the locus uri found that has the sequence, else give all locus from that species
        try: 
            
            sequence = str(request_data["sequence"]).upper()
            
            new_id = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(new_id))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?locus '
                                  'from <{0}> '
                                  'where '
                                  '{{?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus.'
                                  '?locus typon:isOfTaxon <{2}>.}}'.format(current_app.config['DEFAULTHGRAPH'], new_seq_url, spec_url)))

            try:
                return (result["results"]["bindings"])
            
            except:
                return {"message" : "Loci not found"}, 404
                
        except:

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select (str(?name) as ?name) ?locus (str(?original_name) as ?original_name) '
                                  'from <{0}> '
                                  'where '
                                  '{{ ?locus a typon:Locus; typon:isOfTaxon <{1}>; typon:name ?name. '
                                  'OPTIONAL{{?locus typon:originalName ?original_name.}} }}'.format(current_app.config['DEFAULTHGRAPH'], spec_url)))

            # Return records containing prefix only
            try:
            
                request_data["prefix"]
                
                try:
                    def generate():

                        if len(result["results"]["bindings"]) == 0:
                            yield '{ "Loci": [] }'
                        
                        else:

                            resp = []

                            for item in result["results"]["bindings"]:
                                
                                if request_data["prefix"] in item["name"]["value"]:
                                    resp.append(json.dumps(item))

                            resp = ','.join(resp)
                            #print(resp)

                            yield '{ "Loci": ['
                            yield resp
                            yield '] }'

                    return Response(stream_with_context(generate()), content_type='application/json', mimetype='application/json')
                    
                except:
                    return {"message" : "Bad argument"}, 400
            
            # return all records
            except:
                
                try:
                    def generate():

                        resp = []

                        for item in result["results"]["bindings"]:
                            resp.append(json.dumps(item))

                        resp = ','.join(resp)

                        yield '{ "Loci": ['
                        yield resp
                        yield '] }'

                    return Response(stream_with_context(generate()), content_type='application/json', mimetype='application/json')
                    
                except:
                    return {"message" : "Bad argument"}, 400


    @api.doc(responses={ 201: 'OK', 
                         400: 'Invalid Argument', 
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not found' },
             security=["access_token"])
    @api.expect(loci_list_model)
    @w.admin_contributor_required
    def post(self, species_id):
        """ Add a new locus for a particular species """

        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()
         
        #only admin can do this
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result_user = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                      ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; '
                                       'typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result_user['boolean']:
                return {"message" : "Not authorized, admin only"}, 403
        
        except:
            return {"message" : "Not authorized, admin only"}, 403
        
        spec_url = "{0}species/{1}".format(current_app.config['BASE_URL'], str(species_id))
        result_spec = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                  ('ASK where {{ <{0}> a <http://purl.uniprot.org/core/Taxon>}}'.format(spec_url)))
        
        if not result_spec['boolean']:
            return {"message" : "Species not found"}, 404
        

        #count number of loci already created for that species, build the new locus uri and send to server
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select (COUNT(?locus) as ?count) where { ?locus a typon:Locus; typon:isOfTaxon <' + spec_url + '>. }')
        # number_loci_spec = int(result["results"]["bindings"][0]['count']['value'])

        new_locus_url = "{0}loci/{1}".format(current_app.config['BASE_URL'], str(post_data["locus_id"]))
        
        result_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                   ('ASK where {{ <{0}> a typon:Locus .}}'.format(new_locus_url)))
        
        if not result_locus['boolean']:
            return {"message" : "Locus provided not found"}, 404
        
        # Associate locus to species
        query2send = ('INSERT DATA IN GRAPH <{0}> '
                      '{{ <{1}> a typon:Locus; typon:isOfTaxon <{2}> .}}'.format(current_app.config['DEFAULTHGRAPH'], new_locus_url, spec_url))
        
        result = aux.send_data(query2send, 
                               current_app.config['LOCAL_SPARQL'], 
                               current_app.config['VIRTUOSO_USER'], 
                               current_app.config['VIRTUOSO_PASS'])
            
        if result.status_code in [200, 201]:
            return {"message" : "New locus added to species " + str(species_id)}, 201
        else:
            return {"message" : "Sum Thing Wong"}, result.status_code


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


    @api.doc(responses={ 200: 'OK',
                    400: 'Invalid Argument',
                    500: 'Internal Server Error', 
                    403: 'Unauthorized', 
                    401: 'Unauthenticated',
                    404: 'Not Found' },
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
        
        #if isolate name is provided return that isolate, else return all isolates
        #if number of isolates >100000 either increase the number of rows the virtuoso return or use the dateEntered property 
        #and make multiple queries to virtuoso based on the date until all have been fetched
        #you can create your own time intervals to better suit your query
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
            
        if len(result["results"]["bindings"])<1:
            
            def generate():
                yield '{"Isolates": []}'
                
            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
            return r
            
        latestIsolate = (result["results"]["bindings"])[-1]
        isolate_id = latestIsolate['isolate']['value']
        
        #get latest isolate submission date
        result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                              ('select ?date '
                               'from <{0}> '
                               'where '
                               '{{ <{1}> a typon:Isolate; typon:dateEntered ?date }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_id)))
        
        latestDatetime = (result2["results"]["bindings"])[0]['date']['value']
        number_of_isolates = len(result["results"]["bindings"])
        try:
            
            def generate():
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
            r.headers.set('Last-Isolate',latestDatetime)
            
            if number_of_isolates > 49999:
                r.headers.set('All-Isolates-Returned', False)
            else:
                r.headers.set('All-Isolates-Returned', True)
            
            return r
            
        except:
            return {"message" : "Empty man..."}, 404



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


    @api.doc(responses={ 200: 'OK',
                    400: 'Invalid Argument',
                    500: 'Internal Server Error', 
                    403: 'Unauthorized', 
                    401: 'Unauthenticated',
                    404: 'Not Found' },
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

        #if isolate name is provided return that isolate, else return all isolates
        #if number of isolates >100000 either increase the number of rows the virtuoso return or use the dateEntered property 
        #and make multiple queries to virtuoso based on the date until all have been fetched
        #you can create your own time intervals to better suite your query
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
            
            def generate():
                yield '{"Isolates": []}'
                
            r = Response(stream_with_context(generate()), content_type='application/json')
            r.headers.set('Server-Date', str(dt.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')))
            return r
            
        latestIsolate = (result["results"]["bindings"])[-1]
        isolate_id = latestIsolate['isolate']['value']
        
        #get latest isolate submission date
        result2 = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                              ('select ?date '
                              'from <{0}> '
                              'where '
                              '{{ <{1}> a typon:Isolate; typon:dateEntered ?date }}'.format(current_app.config['DEFAULTHGRAPH'], isolate_id)))
        
        latestDatetime = (result2["results"]["bindings"])[0]['date']['value']
        number_of_isolates = len(result["results"]["bindings"])
        try:
            
            def generate():
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
            return {"message" : "Empty man..."}, 404


@species_conf.route('/<int:species_id>/isolates/<string:isolate_id>')
class IsolatesAPItypon(Resource):

    
    @api.doc(responses={ 200: 'OK',
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
        
        #get information on the isolate, metadata are optional
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
            return {"message" : "It's empty man..."}, 404



    @api.doc(responses={ 201: 'OK', 
                    400: 'Invalid Argument', 
                    500: 'Internal Server Error', 
                    403: 'Unauthorized', 
                    401: 'Unauthenticated',
                    404: 'Not found',
                    409: 'Conflict' },
        security=["access_token"])
    @api.expect(isolate_model)
    @w.admin_contributor_required
    def post(self, species_id, isolate_id):
        """ Adds/updates the metadata of an existing 
        """

        c_user = get_jwt_identity()

        # get post data
        post_data = request.get_json()
         
        #only admin can do this
        try:
            new_user_url = "{0}users/{1}".format(current_app.config['BASE_URL'], str(c_user))

            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('ASK where {{ <{0}> a <http://xmlns.com/foaf/0.1/Agent>; '
                                  'typon:Role "Admin"^^xsd:string}}'.format(new_user_url)))
            
            if not result['boolean']:
                return {"message" : "Not authorized, admin only"}, 403
        
        except:
            return {"message" : "Not authorized, admin only"}, 403

        
        # #count number of isolates already created for that species, build the new isolate uri and send to server
        # result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),'select (COUNT(?isolate) as ?count) where { ?isolate a typon:Isolate . }')
        # #print(result)
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
            #if already this value country already exists for isolate
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
            except :
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
        

        #collection date check
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


        #host check
        try:
            auxi = result_meta['host']['value']
        except:
            try:
                
                #get the taxon id from uniprot, if not found metadata not added
                #capitalize the first letter as per scientific name notation
                hostname = (post_data['host']).capitalize()
                print("host name: " + hostname)
                
                #query is made to the scientific name first, then common name and then other name
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
                    #not found, lets try the query without capitalized first letter
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

        #isolation source check
        try:
            auxi = result_meta['isol_source']['value']
        except:
            try:
                isol_source = post_data['isol_source']
                data2sendlist.append(' typon:isolationSource "' + isol_source + '"^^xsd:string')
                metadataUploadable += 1
            except:
                pass


        #longitude check
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
        

        #latitude check
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

        
        #country check
        if country_name:
            #search for country on dbpedia, first query may work for some and not for others, try with netherlands for instance
            query = ('select ?country ?label where '
                     '{{?country a <http://dbpedia.org/class/yago/WikicatMemberStatesOfTheUnitedNations>; a dbo:Country; '
                     '<http://www.w3.org/2000/01/rdf-schema#label> ?label. '
                     'FILTER (lang(?label) = "en") '
                     'FILTER (STRLANG("{0}", "en") = LCASE(?label) ) }}'.format(country_name))
            print("searching country on dbpedia..")
            
            result = aux.get_data(SPARQLWrapper(current_app.config['DBPEDIA_SPARQL']),query)
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
                    result = aux.get_data(SPARQLWrapper(current_app.config['DBPEDIA_SPARQL']),query)
                    country_url = result["results"]["bindings"][0]['country']['value']
                    label = result["results"]["bindings"][0]['label']['value']
                    data2sendlist.append('typon:isolatedAt <'+country_url+'>.<'+country_url+'> rdfs:label "'+label+'"@en')
                    metadataUploadable += 1
                except:
                    print("Metadata not added, " + str(country_name) + " not found on dbpedia search on http://dbpedia.org/page/Category:Member_states_of_the_United_Nations")
                    metadataNotUploadable['country'] = country_name
                    pass

        
        print(metadataNotUploadable)
        
        #if there is metadata to add or metadata to add and not passing the checks
        if len(data2sendlist)>0 or len(list(metadataNotUploadable.keys()))>0:
            
            #if there is metadata to add, build the rdf and send to virtuoso	
            if len(data2sendlist)>0:
                
                # Insert new information
                rdf2send = ";".join(data2sendlist)

                query2send = ('INSERT DATA IN GRAPH <{0}> {{ <{1}>{2}.}}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url, rdf2send))
                print(query2send)
                result = aux.send_data(query2send, 
                                       current_app.config['LOCAL_SPARQL'], 
                                       current_app.config['VIRTUOSO_USER'], 
                                       current_app.config['VIRTUOSO_PASS'])

                if result.status_code not in [200, 201] :
                    return {"message" : "Sum Thing Wong uploading metadata to isolate"}, result.status_code
                    
            def generate():

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
                        prev_item = {k:metadataNotUploadable[k]}
                    yield json.dumps(prev_item) + ']}'
            r = Response(stream_with_context(generate()), content_type='application/json')
            
            if metadataUploadable > 0:
                r.headers.set('Metadata-Uploaded',True)
            else:
                r.headers.set('Metadata-Uploaded',False)
            return r
                
        else:
            return {"message" : "No metadata to upload"}, 409






@species_conf.route('/<int:species_id>/isolates/<string:isolate_id>/alleles')
class IsolatesAlleles(Resource):
    
    @api.doc(responses={ 200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error',
                        403: 'Unauthorized',
                        401: 'Unauthenticated',
                        404: 'Not Found',
                        409: 'Conflict'},
             security=["access_token"])
    #@w.token_required
    @jwt_required
    def get(self, species_id, isolate_id):
        """ Get all alleles from the isolate, independent of schema
        """

        #return all alleles from the isolate
        new_isol_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))
        
        #get all alleles from the isolate, independent of schema
        result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                             ('select ?alleles '
                              'from <{0}> '
                              'where '
                              '{{ <{1}> a typon:Isolate; typon:hasAllele ?alleles.  }}'.format(current_app.config['DEFAULTHGRAPH'], new_isol_url)))
        
        try:
            return (result["results"]["bindings"])
        except:
            return {"message" : "It's empty man..."}, 404

    
    @api.doc(responses={ 200: 'OK',
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
            return  {"message" : "Isolate not found"}, 404

        # check if locus exists
        result_locus = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                   ('ASK where {{ <{0}> a typon:Locus .}}'.format(locus_url)))
        
        if not result_locus['boolean']:
            return {"message" : "Locus not found"}, 404

        # check if allele exists
        result_allele = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                    ('ASK where {{ <{0}> a typon:Locus; typon:hasDefinedAllele <{1}> }}'.format(locus_url, allele_url)))
        
        if not result_allele['boolean']:
            return {"message" : "Allele does not exist for that locus"}, 404

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

        if result_post.status_code in [200, 201] :
            return {"message" : "Allele and respective locus sucessfully added to isolate"}, 201	
        else:
            return {"message" : "Sum Thing Wong"}, result_post.status_code



@species_conf.route('/<int:species_id>/isolates/<int:isolate_id>/schemas')
class IsolatesSchema(Resource):

    parser = api.parser()
    
    parser.add_argument('schema_id',
                        type=str,
                        required=False,
                        location='args',
                        help='ID of a schema on NS')
 

    @api.doc(responses={ 200: 'OK',
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

            if not result_schema['boolean'] :
                return {"message" : ("Schema {0} not found or deprecated".format(schema_uri))} , 404

            # check if isolate exists
            isolate_url = "{0}/isolates/{1}".format(species_url, str(isolate_id))

            result_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                         ('ASK where {{ <{0}> a typon:Isolate .}}'.format(isolate_url)))
            
            if not result_isolate['boolean']:
                return  {"message" : "Isolate not found"}, 404

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
                return {"message" : "It's empty man..."}, 404

        # get all schemas linked to the isolate
        else:

            # check if isolate exists
            isolate_url = "{0}species/{1}/isolates/{2}".format(current_app.config['BASE_URL'], str(species_id), str(isolate_id))
            
            result_isolate = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                         ('ASK where {{ <{0}> a typon:Isolate .}}'.format(isolate_url)))
            
            if not result_isolate['boolean']:
                return  {"message" : "Isolate not found"}, 404

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
                return {"message" : "It's empty man..."}, 404



    

@sequences_conf.route('/list')
class SequencesListAPItypon(Resource):
    """ Sequences List Resource """
    
    @api.doc(responses={ 200: 'OK',
                        400: 'Invalid Argument',
                        500: 'Internal Server Error', 
                        403: 'Unauthorized', 
                        401: 'Unauthenticated',
                        404: 'Not Found' },
        security=["access_token"])
    @jwt_required
    def get(self):
        """ Gets the total number of sequences """
        
        #query number of sequences on database
        try:
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']),
                                 ('select (COUNT(?seq) as ?count) '
                                  'from <{0}> '
                                  'where '
                                  '{{?seq a typon:Sequence }}'.format(current_app.config['DEFAULTHGRAPH'])))
            
            number_sequences_vir = int(result["results"]["bindings"][0]['count']['value'])

            return {"message" : "Total number of sequences is: " + str(number_sequences_vir)}
        except:
            return {"message" : "No sequences were found."}, 404


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


    @api.doc(responses={ 200: 'OK',
                         400: 'Invalid Argument',
                         500: 'Internal Server Error', 
                         403: 'Unauthorized', 
                         401: 'Unauthenticated',
                         404: 'Not Found' },
            security=["access_token"])
    # @w.token_required
    @w.use_kwargs(api, parser)
    @jwt_required
    def get(self, **kwargs):
        """ Get information on sequence, DNA string, uniprot URI and uniprot label """

        # get request data
        request_data = request.args
        
        if len(request_data) == 0:
            return {"message" : "No DNA sequence or hash provided"}, 400

        # if sequence is provided, hash it and send request to virtuoso
        try:

            sequence = request_data["sequence"]

            new_id = hashlib.sha256(sequence.encode('utf-8')).hexdigest()

            new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(new_id))

            #check if the sequence exists
            result_existence = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                           ('ASK where {{ <{0}> typon:nucleotideSequence ?seq.}}'.format(new_seq_url)))

            if not result_existence['boolean']:
                return {"message" : "Sequence not found"}, 404
            
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?schemas ?locus ?alleles ?uniprot ?label '
                                  'from <{0}> '
                                  'where '
                                  '{{ ?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus. '
                                  '?schemas a typon:Schema; typon:hasSchemaPart ?part . '
                                  '?part a typon:SchemaPart; typon:hasLocus ?locus . '
                                  'OPTIONAL {{ <{1}> typon:hasUniprotSequence ?uniprot.}}. '
                                  'OPTIONAL {{ <{1}> typon:hasUniprotLabel ?label.}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_seq_url)))
            
            
            if result["results"]["bindings"] == []:
                return {"message": "Sequence not found."}, 404
            
            else:
                return {"result": result["results"]["bindings"], 
                        "sequence_uri": new_seq_url}, 200

        except:
            
            new_seq_url = "{0}sequences/{1}".format(current_app.config['BASE_URL'], str(request_data["seq_id"]))

            #get information on sequence, DNA string, uniprot URI and uniprot label
            result = aux.get_data(SPARQLWrapper(current_app.config['LOCAL_SPARQL']), 
                                 ('select ?schemas ?locus ?alleles ?sequence ?uniprot ?label '
                                  'from <{0}> '
                                  'where '
                                  '{{ <{1}> a typon:Sequence; typon:nucleotideSequence ?sequence . '
                                  '?alleles typon:hasSequence <{1}>; typon:isOfLocus ?locus .'
                                  '?schemas a typon:Schema; typon:hasSchemaPart ?part .'
                                  '?part a typon:SchemaPart; typon:hasLocus ?locus . '
                                  'OPTIONAL {{ <{1}> typon:hasUniprotSequence ?uniprot.}}. '
                                  'OPTIONAL {{ <{1}> typon:hasUniprotLabel ?label.}} }}'.format(current_app.config['DEFAULTHGRAPH'], new_seq_url)))
            #print(result)

            try:
                return (result["results"]["bindings"][0])
            except:
                return {"message" : "Empty man..."}, 404


