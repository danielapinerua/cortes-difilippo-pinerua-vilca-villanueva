"""Capa de NEGOCIO para planes.

Acá viven las reglas: qué datos son válidos, qué pasa si el plan no existe,
cómo se arma la respuesta. No sabe nada de HTTP (no importa `request`) ni de
SQL (eso lo hace el repositorio). Por eso se puede probar sin servidor y sin
base de datos.

Los límites de largo (100 / 500) salen del esquema SQL:
    name VARCHAR(100) NOT NULL · description VARCHAR(500) NULL · price DECIMAL(12,2) >= 0
"""
from decimal import Decimal

from ..errors import NotFoundError, ValidationError
from ..repositories import plans_repository as repo

NAME_MAX = 100
DESCRIPTION_MAX = 500
PRICE_MAX = 9_999_999_999.99  # DECIMAL(12,2)


def _to_dict(row):
    """Convierte una fila de la base en lo que devuelve la API.

    MySQL devuelve DECIMAL como Decimal y JSON no lo soporta bien,
    así que el precio sale como número.
    """
    plan = dict(row)
    if isinstance(plan.get("price"), Decimal):
        plan["price"] = float(plan["price"])
    return plan


def _validate(data, partial=False):
    """Valida el cuerpo del pedido y devuelve solo los campos permitidos."""
    errors = {}
    clean = {}

    if "name" in data or not partial:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            errors["name"] = "Es obligatorio y debe ser texto."
        elif len(name.strip()) > NAME_MAX:
            errors["name"] = f"Máximo {NAME_MAX} caracteres."
        else:
            clean["name"] = name.strip()

    if "description" in data:
        desc = data["description"]
        if desc is not None and not isinstance(desc, str):
            errors["description"] = "Debe ser texto."
        elif isinstance(desc, str) and len(desc) > DESCRIPTION_MAX:
            errors["description"] = f"Máximo {DESCRIPTION_MAX} caracteres."
        else:
            clean["description"] = desc

    if "price" in data or not partial:
        price = data.get("price")
        if isinstance(price, bool) or not isinstance(price, (int, float)) or not (0 <= price <= PRICE_MAX):
            errors["price"] = "Es obligatorio y debe ser un número mayor o igual a 0."
        else:
            clean["price"] = price

    if errors:
        raise ValidationError("Hay datos inválidos.", details=errors)
    return clean


def list_plans():
    return [_to_dict(r) for r in repo.list_all()]


def get_plan(plan_id):
    row = repo.get(plan_id)
    if row is None:
        raise NotFoundError(f"No existe el plan {plan_id}.")
    return _to_dict(row)


def create_plan(data):
    clean = _validate(data)
    new_id = repo.create(clean)
    return get_plan(new_id)


def update_plan(plan_id, data):
    get_plan(plan_id)  # si no existe, lanza 404
    clean = _validate(data, partial=True)
    if clean:
        repo.update(plan_id, clean)
    return get_plan(plan_id)


def delete_plan(plan_id):
    get_plan(plan_id)  # si no existe, lanza 404
    repo.delete(plan_id)
