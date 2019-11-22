from flask_security.decorators import auth_required as security_auth_required
from functools import wraps

from .roles_accepted import roles_accepted
from .roles_required import roles_required


def auth_required(*decorator_args, **decorator_kwargs):
    """Decorator for requiring an authenticated user, optionally with roles

    Roles are passed as keyword arguments, like so:
    @auth_required(role='REQUIRE_THIS_ONE_ROLE')
    @auth_required(roles=['REQUIRE', 'ALL', 'OF', 'THESE', 'ROLES'])
    @auth_required(one_of=['EITHER_THIS_ROLE', 'OR_THIS_ONE'])

    One of role or roles kwargs can also be combined with one_of:
    @auth_required(role='REQUIRED', one_of=['THIS', 'OR_THIS'])

    Aborts with HTTP 401: Unauthorized if no user is logged in, or
    HTTP 403: Forbidden if any of the specified role checks fail
    """
    required_roles = []
    one_of_roles = []
    if not (decorator_args and callable(decorator_args[0])):
        if 'role' in decorator_kwargs and 'roles' in decorator_kwargs:
            raise RuntimeError('specify only one of `role` or `roles` kwargs')
        elif 'role' in decorator_kwargs:
            required_roles = [decorator_kwargs['role']]
        elif 'roles' in decorator_kwargs:
            required_roles = decorator_kwargs['roles']

        if 'one_of' in decorator_kwargs:
            one_of_roles = decorator_kwargs['one_of']

    def wrapper(fn):
        @wraps(fn)
        @security_auth_required('session', 'token')
        @roles_required(*required_roles)
        @roles_accepted(*one_of_roles)
        def decorated(*args, **kwargs):
            return fn(*args, **kwargs)
        return decorated

    # allow using the decorator without parenthesis
    if decorator_args and callable(decorator_args[0]):
        return wrapper(decorator_args[0])
    return wrapper
