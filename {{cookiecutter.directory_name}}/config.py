import os
import datetime
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """ Configuration settings for the application """

    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'you-will-never-guess'

    # Postgres setup
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:test@172.19.1.2:5432/ref_ns_sec'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Security setup
    SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
    SECURITY_TRACKABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_REGISTERABLE = True
    SECURITY_PASSWORD_SALT = ''
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_MSG_INVALID_PASSWORD = (
        'Your username/password do not match our records', 'error')
    SECURITY_MSG_USER_DOES_NOT_EXIST = (
        'Your username/password do not match our records', 'error')
    SECURITY_HASHING_SCHEMES = ['plaintext']
    SECURITY_DEPRECATED_HASHING_SCHEMES = []

    # JWT Config
    JWT_SECRET_KEY = 'super-secret'
    JWT_TOKEN_LOCATION = ['headers']
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=3)
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = ''

    # Only allow JWT cookies to be sent over https.
    JWT_COOKIE_SECURE = False

    # Enable csrf double submit protection
    JWT_COOKIE_CSRF_PROTECT = True

    # EMAIL CONFIGS
    MAIL_SERVER = "{{cookiecutter.flask_email_server}}"
    MAIL_PORT = "{{cookiecutter.flask_email_port}}"
    MAIL_USE_TLS = "{{cookiecutter.flask_email_use_tls}}"
    MAIL_USE_SSL = "{{cookiecutter.flask_email_use_ssl}}"
    MAIL_USERNAME = "{{cookiecutter.flask_email}}"
    MAIL_PASSWORD = "{{cookiecutter.flask_email_password}}"
    MAIL_DEFAULT_SENDER = "{{cookiecutter.flask_email_default_sender}}"

    # VIRTUOSO CONFIGS
    BASE_URL = os.environ.get('BASE_URL')
    DEFAULTHGRAPH = os.environ.get('DEFAULTHGRAPH')
    VIRTUOSO_USER = 'dba'
    VIRTUOSO_PASS = 'ummi'
    LOCAL_SPARQL = os.environ.get('LOCAL_SPARQL')
    UNIPROT_SPARQL = 'http://sparql.uniprot.org/sparql'
    DBPEDIA_SPARQL = 'http://dbpedia.org/sparql/'

    URL_SEND_LOCAL_VIRTUOSO = os.environ.get('URL_SEND_LOCAL_VIRTUOSO')

    # CELERY CONFIG
    CELERY_BROKER_URL = 'redis://172.19.1.4:6379/0'
    CELERY_RESULT_BACKEND = 'redis://172.19.1.4:6379/0'

    # FLASK-RESTPLUS CONFIG
    SWAGGER_UI_JSON_EDITOR = True
    RESTPLUS_MASK_SWAGGER = False

    # file transfer configs
    SCHEMAS_PTF = './prodigal_training_files'
    SCHEMAS_ZIP = './compressed_schemas'

    # pre-computed stats for frontend
    PRE_COMPUTE = './pre-computed-data'

    # schema upload directory
    SCHEMA_UP = './schema_insertion_temp'
