from functools import wraps
# from http import HTTPStatus

# from flask import abort, request
# from flask_principal import Permission, RoleNeed
# from flask_security.decorators import auth_required as security_auth_required
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims

# def roles_required(*roles):
#     """Decorator which specifies that a user must have all the specified roles.

#     Aborts with HTTP 403: Forbidden if the user doesn't have the required roles

#     Example::

#         @app.route('/dashboard')
#         @roles_required('ROLE_ADMIN', 'ROLE_EDITOR')
#         def dashboard():
#             return 'Dashboard'

#     The current user must have both the `ROLE_ADMIN` and `ROLE_EDITOR` roles
#     in order to view the page.

#     :param roles: The required roles.
#     """
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             perms = [Permission(RoleNeed(role)) for role in roles]
#             for perm in perms:
#                 if not perm.can():
#                     abort(HTTPStatus.FORBIDDEN)
#             return fn(*args, **kwargs)
#         return decorated_view
#     return wrapper


# def roles_accepted(*roles):
#     """Decorator which specifies that a user must have at least one of the
#     specified roles.

#     Aborts with HTTP: 403 if the user doesn't have at least one of the roles

#     Example::

#         @app.route('/create_post')
#         @roles_accepted('ROLE_ADMIN', 'ROLE_EDITOR')
#         def create_post():
#             return 'Create Post'

#     The current user must have either the `ROLE_ADMIN` role or `ROLE_EDITOR`
#     role in order to view the page.

#     :param roles: The possible roles.
#     """
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             perm = Permission(*[RoleNeed(role) for role in roles])
#             if not perm.can():
#                 abort(HTTPStatus.FORBIDDEN)
#             return fn(*args, **kwargs)
#         return decorated_view
#     return wrapper


# def auth_required(*decorator_args, **decorator_kwargs):
#     """Decorator for requiring an authenticated user, optionally with roles

#     Roles are passed as keyword arguments, like so:
#     @auth_required(role='REQUIRE_THIS_ONE_ROLE')
#     @auth_required(roles=['REQUIRE', 'ALL', 'OF', 'THESE', 'ROLES'])
#     @auth_required(one_of=['EITHER_THIS_ROLE', 'OR_THIS_ONE'])

#     One of role or roles kwargs can also be combined with one_of:
#     @auth_required(role='REQUIRED', one_of=['THIS', 'OR_THIS'])

#     Aborts with HTTP 401: Unauthorized if no user is logged in, or
#     HTTP 403: Forbidden if any of the specified role checks fail
#     """
#     required_roles = []
#     one_of_roles = []
#     if not (decorator_args and callable(decorator_args[0])):
#         if 'role' in decorator_kwargs and 'roles' in decorator_kwargs:
#             raise RuntimeError('specify only one of `role` or `roles` kwargs')
#         elif 'role' in decorator_kwargs:
#             required_roles = [decorator_kwargs['role']]
#         elif 'roles' in decorator_kwargs:
#             required_roles = decorator_kwargs['roles']

#         if 'one_of' in decorator_kwargs:
#             one_of_roles = decorator_kwargs['one_of']

#     def wrapper(fn):
#         @wraps(fn)
#         @security_auth_required('session', 'token')
#         @roles_required(*required_roles)
#         @roles_accepted(*one_of_roles)
#         def decorated(*args, **kwargs):
#             return fn(*args, **kwargs)
#         return decorated

#     # allow using the decorator without parenthesis
#     if decorator_args and callable(decorator_args[0]):
#         return wrapper(decorator_args[0])
#     return wrapper




# def token_required(f):
#     """ Decorator for requiring a token for authentication.
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):

#         data, status = Auth.get_logged_in_user(request)
#         token = data.get('data')

#         if not token:
#             return data, status

#         return f(*args, **kwargs)

#     return decorated


def use_kwargs(api, parser, validate=True):
    """ Decorator to add extra arguments to GET requests.
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
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] not in ['Admin', 'Contributor']:
            return {'Not authorized': 'Admins or Contributors only!'}, 403
        else:
            return fn(*args, **kwargs)
    return wrapper


