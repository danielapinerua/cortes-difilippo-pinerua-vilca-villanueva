"""Capa de NEGOCIO de autenticación (US16 - Iniciar sesión)."""
from ..errors import UnauthorizedError, ValidationError
from ..repositories import users_repository as users_repo
from ..security import create_token, verify_password

# US16: ante datos incorrectos hay que informar el error SIN indicar cuál de los
# dos campos falló. Por eso hay un único mensaje para todos los casos.
INVALID_CREDENTIALS = "Email o contraseña incorrectos."


def _public_user(row):
    return {"id": row["id"], "email": row["email"], "role": row["role"]}


def login(data):
    email = data.get("email")
    password = data.get("password")

    errors = {}
    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Es obligatorio."
    if not isinstance(password, str) or not password:
        errors["password"] = "Es obligatoria."
    if errors:
        raise ValidationError("Hay datos inválidos.", details=errors)

    user = users_repo.get_by_email(email.strip())
    if user is None or not user["is_active"] or not verify_password(user["password_hash"], password):
        raise UnauthorizedError(INVALID_CREDENTIALS)

    users_repo.touch_last_login(user["id"])
    return {"token": create_token(user), "token_type": "Bearer", "user": _public_user(user)}


def current_user(user_id):
    """Datos del usuario logueado, leídos de la base (por si lo desactivaron)."""
    user = users_repo.get_by_id(user_id)
    if user is None or not user["is_active"]:
        raise UnauthorizedError("La cuenta no existe o está desactivada.")
    return _public_user(user)
