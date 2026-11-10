"""Sesión y permisos de las PÁGINAS del front.

Ojo con la diferencia (esto se pregunta en las defensas):
  * Estos decoradores controlan qué PÁGINA se muestra → es experiencia de usuario.
  * La seguridad REAL está en el API: aunque alguien fuerce una URL, el API
    responde 403 si el rol no corresponde. El front nunca decide permisos "de verdad".
"""
from functools import wraps

from flask import redirect, session, url_for, flash

from .constants import ROLE_ADMIN, ROLE_CLIENT


def start_session(login_response):
    """Guarda en la cookie de sesión lo mínimo: el token y quién es."""
    session.clear()  # evita reutilizar una sesión vieja (session fixation)
    session.permanent = True
    session["token"] = login_response["token"]
    session["user"] = login_response["user"]


def current_user():
    return session.get("user")


def token():
    return session.get("token")


def home_for(user):
    """A qué pantalla va cada rol después de entrar."""
    if user and user.get("role") == ROLE_ADMIN:
        return url_for("admin.inbox")
    return url_for("client.services")


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not token():
            flash("Iniciá sesión para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user().get("role") != role:
                flash("No tenés permiso para ver esa página.", "danger")
                return redirect(home_for(current_user()))
            return view(*args, **kwargs)
        return wrapper
    return decorator


client_required = role_required(ROLE_CLIENT)
admin_required = role_required(ROLE_ADMIN)
