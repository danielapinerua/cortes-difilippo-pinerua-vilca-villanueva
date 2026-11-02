"""Capa de NEGOCIO para gestionar clientes (US06 / CU5).

Reglas que viven acá:
  - El admin da de alta y modifica perfiles de clientes (no credenciales).
  - `plan_id` es obligatorio y debe existir en `plans`.
  - `email` y `dni` no se repiten entre clientes.
  - Si el email ya pertenece a una cuenta de cliente que todavía no tiene
    perfil, se vincula automáticamente (`clients.user_id`). Si ya tiene perfil,
    se rechaza. Así no queda un email "ocupado" sin forma de resolverlo.

No sabe nada de HTTP (no importa `request`) ni de SQL (eso lo hace el
repositorio). Por eso se puede probar sin servidor y sin base de datos.
"""
from decimal import Decimal

from ..constants import ROLE_CLIENT
from ..errors import DuplicateError, NotFoundError, ValidationError
from ..repositories import clients_repository as repo
from ..repositories import plans_repository, users_repository
from ..validators import validate_client

INVALID = "Hay datos inválidos."


def _to_dict(row):
    """Convierte una fila del repositorio en lo que devuelve la API.

    La respuesta es plana (igual que US14): `plan_name` y `plan_price` en vez
    de un objeto anidado. `has_login` indica si el cliente tiene cuenta, sin
    exponer el `user_id` interno.
    """
    client = dict(row)
    if isinstance(client.get("plan_price"), Decimal):
        client["plan_price"] = float(client["plan_price"])
    client["has_login"] = client.get("user_id") is not None
    client.pop("user_id", None)
    return client


def list_clients(search=None, plan_id=None):
    """Listado para el administrador, con filtros opcionales."""
    return [_to_dict(r) for r in repo.search(search=search, plan_id=plan_id)]


def get_client(client_id):
    row = repo.get_detail(client_id)
    if row is None:
        raise NotFoundError(f"No existe el cliente {client_id}.")
    return _to_dict(row)


def create_client(data):
    """Alta de un cliente. Devuelve el perfil ya guardado."""
    clean, errors = validate_client(data, partial=False)
    if errors:
        raise ValidationError(INVALID, details=errors)

    _ensure_plan(clean["plan_id"])
    _ensure_unique(clean)

    user_id = _find_linkable_user(clean["email"])

    new_id = repo.create(
        user_id=user_id,
        plan_id=clean["plan_id"],
        name=clean["name"],
        email=clean["email"],
        phone=clean.get("phone"),
        dni=clean.get("dni"),
    )
    return get_client(new_id)


def update_client(client_id, data):
    """Modificación parcial. Un cuerpo vacío devuelve el cliente sin cambios."""
    current = repo.get_detail(client_id)
    if current is None:
        raise NotFoundError(f"No existe el cliente {client_id}.")

    clean, errors = validate_client(data, partial=True)
    if errors:
        raise ValidationError(INVALID, details=errors)
    if not clean:
        return _to_dict(current)

    # Los valores que van a quedar guardados: lo actual pisado por lo nuevo.
    effective = {**current, **clean}

    _ensure_plan(effective["plan_id"])
    _ensure_unique(effective, exclude_id=client_id)

    # El email de contacto se cruza con las cuentas de login SOLO si cambió.
    # Si no, un cliente vinculado a un usuario con el mismo email se rechazaría
    # a sí mismo al modificar cualquier otro campo.
    if "email" in clean and clean["email"] != current["email"]:
        _ensure_email_not_taken_by_user(clean["email"], current)

    repo.update(client_id, clean)
    return get_client(client_id)


def _ensure_plan(plan_id):
    if plans_repository.get(plan_id) is None:
        raise ValidationError(INVALID, details={"plan_id": "El plan no existe."})


def _ensure_unique(clean, exclude_id=None):
    """Duplicados dentro de `clients`. El UNIQUE de MySQL queda como red de seguridad."""
    if repo.email_exists(clean["email"], exclude_id=exclude_id):
        raise DuplicateError(
            "Ya existe un cliente con ese email.",
            details={"email": "Ya está registrado."},
        )

    dni = clean.get("dni")
    if dni and repo.dni_exists(dni, exclude_id=exclude_id):
        raise DuplicateError(
            "Ya existe un cliente con ese DNI.",
            details={"dni": "Ya está registrado."},
        )


def _find_linkable_user(email):
    """Devuelve el `user_id` a vincular, o None si el email no es una cuenta.

    Solo se vincula una cuenta con rol `client` que todavía no tenga perfil.
    """
    user = users_repository.get_by_email(email)
    if user is None:
        return None

    if user["role"] != ROLE_CLIENT:
        raise DuplicateError(
            "Ese email pertenece a un administrador.",
            details={"email": "Ese email ya está en uso."},
        )

    if repo.user_id_exists(user["id"]):
        raise DuplicateError(
            "Ese usuario ya tiene un perfil de cliente.",
            details={"email": "Ese email ya tiene un perfil de cliente."},
        )

    return user["id"]


def _ensure_email_not_taken_by_user(email, current):
    """En una modificación, el email nuevo no puede ser el login de otra cuenta."""
    user = users_repository.get_by_email(email)
    if user is None or user["id"] == current.get("user_id"):
        return
    raise DuplicateError(
        "Ese email ya pertenece a una cuenta.",
        details={"email": "Ese email ya está en uso."},
    )
