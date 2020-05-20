"""
Purpose
-------
This module contains decorators used throughout the API routes.

Code documentation
------------------
"""

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims


def use_kwargs(api, parser, validate=True):
    """ Decorator to add extra arguments to GET requests.

    Parameters
    ----------
    api: flask-restplus API object
        Object contaning the API
    parser: API parser

    """
    def decorated(f):

        @api.expect(parser)
        @wraps(f)
        def wrapper(*args, **kwargs):
            v = parser.parse_args()
            kwargs.update(v)
            return f(*args, **kwargs)

        return wrapper

    return decorated


# Here is a custom decorator that verifies the JWT is present in
# the request, as well as insuring that this user has a role of
# `admin` in the access token
def admin_required(fn):
    """
    Decorator that verifies the JWT is present in
    the request, as well as ensuring that this user has a role of
    `admin` in the access token.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] != 'Admin':
            return {'Not authorized': 'Admins only!'}, 403
        else:
            return fn(*args, **kwargs)
    return wrapper


# Here is a custom decorator that verifies the JWT is present in
# the request, as well as insuring that this user has a role of
# `admin` or contributor in the access token
def admin_contributor_required(fn):
    """
    Decorator that verifies the JWT is present in
    the request, as well as insuring that this user has a role of
    `admin` or contributor in the access token.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] not in ['Admin', 'Contributor']:
            return {'Not authorized': 'Admins or Contributors only!'}, 403
        else:
            return fn(*args, **kwargs)
    return wrapper
