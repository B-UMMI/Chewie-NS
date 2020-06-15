from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
# from flask_bootstrap import Bootstrap
from flask_security import Security, SQLAlchemyUserDatastore, user_registered
from flask_restplus import Api, marshal_with
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from celery import Celery


'''
App route:
    - Defining the global app instance.
    - Launching database.
    - Set the queue management.
    - Load all the other files required for the application to work:
        - models (load all the datatabase Resource models)
        - api (load all the app endpoints)
        - app_configuration (before first request)
'''


#get db
db = SQLAlchemy()

# provide migration
migrate = Migrate()

# Login Manager
login_manager = LoginManager()

# Bootstrap for prototype frontend
# bootstrap = Bootstrap()

# App security
security = Security()

# Queue management
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)


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
    # Setup app
    app = Flask(__name__)

    # Setup CORS 
    CORS(app)

    # Reads the config file
    app.config.from_object(config_class)

    # Setup db
    db.init_app(app)

    # Setup migration
    migrate.init_app(app, db)

    # Setup login manager
    login_manager.init_app(app)

    # Setup bootstrap
    # bootstrap.init_app(app)

    # Setup SQLAlchemy datastore
    datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)

    # Setup Flask-Security
    security.init_app(app, datastore=datastore)

    # Setup JWT
    jwt.init_app(app)

    # Setup Celery
    celery.conf.update(app.config)

    # https://flask.palletsprojects.com/en/1.1.x/deploying/wsgi-standalone/#proxy-setups
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_for=1, x_host=1)

    from app.api import blueprint as api_bp
    app.register_blueprint(api_bp)
    
    # from app.front_end import front_end_blueprint
    # app.register_blueprint(front_end_blueprint)

    @user_registered.connect_via(app)
    def user_registered_sighandler(app, user, confirm_token, **extra):
        print("User created successfully ")
        default_role = datastore.find_role("User")
        datastore.add_role_to_user(user, default_role)
        db.session.commit()

    return app


from app import models
datastore_cheat = SQLAlchemyUserDatastore(db, models.User, models.Role)
