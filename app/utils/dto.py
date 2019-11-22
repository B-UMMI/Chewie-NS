from flask_restplus import Namespace, fields
#from app import api

class UserDto:
    
    api = Namespace('user', description='user related operations')
    
    user_model = api.model('user', {
        'id': fields.Integer(description="User ID"),
        'email': fields.String(required=True, description='user email address'),
        'roles': fields.String(required=True, description='Role of the user')
    })
    
    current_user_model = api.model("current_user", {
    'id': fields.Integer(description="User ID"),
    'email': fields.String,
    'last_login_at': fields.DateTime,
    "roles": fields.String
    })
    
    create_user_model = api.model("CreateUserModel", {
    'email': fields.String(required=True, description="user email address"),
    'password': fields.String(required=True, description="user password, minimum 6 characters.")
    })
