from flask import Blueprint, url_for
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

#security = {}

class Custom_API(Api):
    @property
    def specs_url(self):
        '''
        The Swagger specifications absolute url (ie. `swagger.json`)

        :rtype: str
        '''
        return url_for(self.endpoint('specs'), _external=False)

# Fix for reverse proxy issue.
# Fix of returning swagger.json on HTTP
# https://github.com/noirbizarre/flask-restplus/issues/223#issuecomment-381439513
api = Custom_API(blueprint,
          title="Nomenclature Server API",
          version="1.0",
          doc="/docs",
          security=["access_token", "refresh_token"],
          authorizations=authorizations)

from . import routes
