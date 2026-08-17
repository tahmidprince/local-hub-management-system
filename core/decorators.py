"""
core/decorators.py

Reusable role-based access control decorator for function-based views.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(allowed_roles):
    """
    Restrict a view to users whose `.role` is in `allowed_roles`.

    Usage:
        @role_required(['provider', 'admin'])
        def some_view(request):
            ...
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url="login")
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                messages.error(
                    request, "You do not have permission to access that page."
                )
                return redirect("role_dispatch")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
