"""Seguridad: contraseñas, token de sesión y control de acceso por rol.

Cómo funciona el login (resumen):
  1. El usuario manda email + contraseña a POST /auth/login.
  2. Si son correctos, la API devuelve un TOKEN: un texto firmado con SECRET_KEY
     que adentro lleva {id de usuario, rol} y la hora en que se emitió.
  3. El frontend guarda el token y lo manda en cada pedido:
         Authorization: Bearer <token>
  4. Las rutas protegidas con @login_required / @role_required leen ese header,
     verifican la firma y la antigüedad, y dejan al usuario en g.current_user.

Nadie puede inventar ni modificar un token sin conocer SECRET_KEY (si cambian
una letra, la firma deja de coincidir). Limitación conocida: el rol viaja dentro
del token, así que un cambio de rol o una cuenta desactivada recién se nota
cuando el token vence (TOKEN_MAX_AGE_SECONDS, 8 horas por defecto).
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from .errors import ForbiddenError, UnauthorizedError


# ---- Contraseñas -----------------------------------------------------------
# Nunca se guarda la contraseña: se guarda su "hash" (una huella irreversible).
# Para verificar, se calcula el hash de lo que escribió el usuario y se compara.

def hash_password(password):
    return generate_password_hash(password, method="pbkdf2:sha256")


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


# ---- Token -----------------------------------------------------------------

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth-token")


def create_token(user):
    return _serializer().dumps({"uid": user["id"], "role": user["role"]})


def _read_token(token):
    try:
        return _serializer().loads(token, max_age=current_app.config["TOKEN_MAX_AGE_SECONDS"])
    except SignatureExpired:
        raise UnauthorizedError("La sesión expiró. Iniciá sesión de nuevo.")
    except BadSignature:
        raise UnauthorizedError("Token inválido.")


def _authenticate_request():
    """Lee el header Authorization y deja el usuario en g.current_user."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise UnauthorizedError("Falta el token de autenticación.")
    data = _read_token(token.strip())
    g.current_user = {"id": data["uid"], "role": data["role"]}
    return g.current_user


# ---- Decoradores para proteger rutas ---------------------------------------

def login_required(view):
    """Exige estar logueado (cualquier rol). Uso: @login_required debajo de @bp.get(...)"""
    @wraps(view)
    def wrapper(*args, **kwargs):
        _authenticate_request()
        return view(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """Exige estar logueado Y tener uno de los roles. Uso: @role_required("admin")"""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _authenticate_request()
            if user["role"] not in roles:
                raise ForbiddenError("No tenés permisos para realizar esta acción.")
            return view(*args, **kwargs)
        return wrapper
    return decorator
