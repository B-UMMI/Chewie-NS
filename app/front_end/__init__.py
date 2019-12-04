from flask import Blueprint

front_end_blueprint = Blueprint("front_end", __name__)

from . import routes
