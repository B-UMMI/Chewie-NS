from flask import Flask
#from flask.sessions import SecureCookieSessionInterface
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
#from flask_mail import Mail
from flask_bootstrap import Bootstrap
#from flask_moment import Moment
from flask_security import Security, SQLAlchemyUserDatastore, user_registered
from flask_restplus import Api, marshal_with
#from flask_marshmallow import Marshmallow
from flask_cors import CORS
# from flask_talisman import Talisman
#from flask_seasurf import SeaSurf
from flask_jwt_extended import JWTManager
from config import Config
from celery import Celery



#get db
db = SQLAlchemy()
# provide migration
migrate = Migrate()
login_manager = LoginManager()
# mail = Mail()
bootstrap = Bootstrap()
security = Security()
#csrf = SeaSurf()

celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)



####### Config jwt ##############################################################
jwt = JWTManager()


# Create a function that will be called whenever create_access_token
# is used. It will take whatever object is passed into the
# create_access_token method, and lets us define what custom claims
# should be added to the access token.
user_roles_dict = {"<Role Admin>": "Admin",
                   "<Role Contributor>": "Contributor",
                   "<Role User>": "User"}

@jwt.user_claims_loader
def add_claims_to_access_token(user):
    return {'roles': user_roles_dict[str(user.roles[0])]}


# Create a function that will be called whenever create_access_token
# is used. It will take whatever object is passed into the
# create_access_token method, and lets us define what the identity
# of the access token should be.
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

#################################################################################

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    # mail.init_app(app)
    bootstrap.init_app(app)
    datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
    security.init_app(app, datastore=datastore)
    #csrf.init_app(app)
    jwt.init_app(app)
    celery.conf.update(app.config)

    # https://flask.palletsprojects.com/en/1.1.x/deploying/wsgi-standalone/#proxy-setups
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_for=1, x_host=1)

    from app.api import blueprint as api_bp
    app.register_blueprint(api_bp)
    
    from app.front_end import front_end_blueprint
    app.register_blueprint(front_end_blueprint)

    @user_registered.connect_via(app)
    def user_registered_sighandler(app, user, confirm_token, **extra):
        print("User created successfully ")
        default_role = datastore.find_role("User")
        datastore.add_role_to_user(user, default_role)
        db.session.commit()

    return app


from app import models
datastore_cheat = SQLAlchemyUserDatastore(db, models.User, models.Role)



# celery.conf.update(app.config)

# app = Flask(__name__)
# CORS(app)
# app.config.from_object(Config)

# # Disable Session Cookie generation
# class CustomSessionInterface(SecureCookieSessionInterface):
#     """Disable default cookie generation."""
    
#     def should_set_cookie(self, *args, **kwargs):
#         return False

#     """Prevent creating session from API requests."""
#     def save_session(self, *args, **kwargs):
#         if g.get('login_via_header'):
#             #print("Custom session login via header")
#             return
#         return super(CustomSessionInterface, self).save_session(*args, **kwargs)

# app.session_interface = CustomSessionInterface()

# @user_loaded_from_header.connect
# def user_loaded_from_header(self, user=None):
#     g.login_via_header = True

# login_manager = LoginManager(app)
#login_manager.init_app(app)


## HTTPS config

# Content Security Policy
# csp = {
#     'default-src': '\'self\''
# }
# talisman = Talisman(app, content_security_policy=csp)

# # get db
# db = SQLAlchemy(app)

# # provide migration
# migrate = Migrate(app, db)

# # Pretty Things
# bootstrap = Bootstrap(app)

# Pretty date and time
#moment = Moment(app)

# API

# Define a blueprint to change the endpoint for the documentation of the API (Swagger)
#blueprint = Blueprint("api", __name__, url_prefix='/NS/api')


# Celery
# celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
# celery.conf.update(app.config)


# API authorizations
# authorizations = {
#     'apikey' : {
#         'type' : 'apiKey',
#         'in' : 'header',
#         'name' : 'X-API-KEY'
#     }
# }

# api = Api(blueprint,
#           title="Nomenclature Server API",
#           version="2.0",
#           doc="/docs",
#           authorizations=authorizations)
#name_space = api.namespace('/NS/api/docs', description='Nomenclature Server API')

#app.register_blueprint(blueprint)



# from app import models, routes


# if __name__ == "__main__":
#     app.run(Threaded=True, debug=True)
