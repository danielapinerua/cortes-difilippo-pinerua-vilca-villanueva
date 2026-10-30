"""Capa de NEGOCIO de autenticación (US16 login, US17 registro)."""
from .. import db
from ..constants import DEFAULT_PLAN_ID, ROLE_CLIENT
from ..errors import (
    DuplicateError,
    InvalidReferenceError,
    UnauthorizedError,
    ValidationError,
)
from ..repositories import clients_repository as clients_repo
from ..repositories import plans_repository as plans_repo
from ..repositories import users_repository as users_repo
from ..security import create_token, hash_password, verify_password
from ..validators import validate_registration

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


def register(data):
    """US17: crea la cuenta de un visitante.

    Orden: validar formatos (422) -> detectar duplicados (409) -> crear.
    El rol SIEMPRE es 'client': si el cuerpo trae otro, se ignora.
    No devuelve token a propósito: después del alta hay que iniciar sesión.
    """
    clean, errors = validate_registration(data)
    if errors:
        raise ValidationError("Hay datos inválidos.", details=errors)

    _ensure_available(clean)

    plan = plans_repo.get(DEFAULT_PLAN_ID)
    if plan is None:
        raise InvalidReferenceError(
            "El plan por defecto no está cargado. Volvé a ejecutar el script SQL."
        )

    # El hash es lento a propósito: se calcula antes de abrir la transacción
    # para no tener la conexión tomada mientras tanto.
    password_hash = hash_password(clean["password"])

    with db.transaction():
        user_id = users_repo.create(clean["email"], password_hash, ROLE_CLIENT)
        client_id = clients_repo.create(
            user_id=user_id,
            plan_id=plan["id"],
            name=clean["name"],
            email=clean["email"],
            phone=clean["phone"],
            dni=clean["dni"],
        )

    return {
        "message": "Cuenta creada. Iniciá sesión para continuar.",
        "user": {"id": user_id, "email": clean["email"], "role": ROLE_CLIENT},
        "client": {
            "id": client_id,
            "name": clean["name"],
            "plan": {"id": plan["id"], "name": plan["name"]},
        },
    }


def _ensure_available(clean):
    """Duplicados con mensaje claro. La restricción UNIQUE sigue siendo la red
    de seguridad para dos registros simultáneos (ver error 1062)."""
    email = clean["email"]
    if users_repo.email_exists(email) or clients_repo.get_by_email(email) is not None:
        raise DuplicateError(
            "Ya existe una cuenta con ese email.",
            details={"email": "Ya está registrado."},
        )

    dni = clean["dni"]
    if dni and clients_repo.get_by_dni(dni) is not None:
        raise DuplicateError(
            "Ya existe una cuenta con ese DNI.",
            details={"dni": "Ya está registrado."},
        )
