"""Utilidades compartidas por las rutas."""
from flask import request

from ..errors import ValidationError


def json_body():
    """Devuelve el cuerpo JSON del pedido (un objeto) o lanza 422."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo del pedido debe ser un JSON (objeto).")
    return data


def int_query_args(*names):
    """Lee parámetros numéricos OPCIONALES de la URL (ej. ?status_id=1&client_id=).

    - Ausente o vacío  -> None (el filtro no se aplica).
    - Entero positivo  -> int.
    - Cualquier otra cosa (letras, negativos, decimales) -> 422 indicando cuáles.

    Devuelve un diccionario {nombre: valor}, listo para pasar con **.
    """
    values, errors = {}, {}
    for name in names:
        raw = request.args.get(name, "").strip()
        if raw == "":
            values[name] = None
        elif raw.isascii() and raw.isdigit():
            values[name] = int(raw)
        else:
            errors[name] = "Debe ser un número entero."
    if errors:
        raise ValidationError("Hay datos inválidos.", details=errors)
    return values
