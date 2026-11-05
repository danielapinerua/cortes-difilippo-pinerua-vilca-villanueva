"""Capa de acceso a datos para notificaciones internas.

La tabla `notifications` ya existe en el esquema:
    id, user_id, message, is_read, created_at

En esta iteración solo se crea. La bandeja y el marcado como leídas
son US11/US12.
"""
from ..db import get_db


def create(user_id, message):
    """Inserta una notificación y devuelve su id.

    `is_read` y `created_at` usan los DEFAULT de la tabla:
        0 y CURRENT_TIMESTAMP.

    No hace commit: participa de la transacción abierta por el caller.
    """
    with get_db().cursor() as cur:
        cur.execute(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (user_id, message),
        )
        return cur.lastrowid
