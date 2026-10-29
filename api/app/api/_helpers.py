"""Utilidades compartidas por las rutas."""
from flask import request

from ..errors import ValidationError


def json_body():
    """Devuelve el cuerpo JSON del pedido (un objeto) o lanza 422."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo del pedido debe ser un JSON (objeto).")
    return data
