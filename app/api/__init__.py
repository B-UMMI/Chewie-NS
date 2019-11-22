from flask import Blueprint
from flask_restplus import Api

blueprint = Blueprint("api", __name__, url_prefix='/NS/api')

# API authorizations
# authorizations = {
#     'apikey' : {
#         'type' : 'apiKey',
#         'in' : 'header',
#         'name' : 'X-API-KEY'
#     }
#}

authorizations = {
    'access_token' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'Authorization'
    },
    'refresh_token' : {
        'type' : 'apiKey',
        'in' : 'header',
        'name' : 'Authorization'
    },
}

security = {}

api = Api(blueprint,
          title="Nomenclature Server API",
          version="1.0",
          doc="/docs",
          security=["access_token", "refresh_token"],
          authorizations=authorizations)

from . import routes
