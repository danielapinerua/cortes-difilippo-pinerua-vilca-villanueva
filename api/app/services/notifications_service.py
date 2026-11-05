"""Capa de negocio para notificaciones internas.

Solo creación. No envía email/SMS: eso pertenece a US21/NotiSys.
No tiene endpoints propios en esta iteración.
"""
from ..repositories import notifications_repository

MESSAGE_MAX = 500


def _truncate(message):
    """Ajusta el texto al VARCHAR(500) de notifications.message."""
    if len(message) <= MESSAGE_MAX:
        return message
    return message[: MESSAGE_MAX - 3] + "..."


def create_notification(user_id, message):
    """Crea una notificación para `user_id` y devuelve su id.

    - `user_id` debe ser un entero positivo.
    - `message` debe ser texto no vacío.
    - Se trunca a 500 caracteres, que es el límite de la columna.
    - No hace commit: participa de la transacción del caller.
    """
    if isinstance(user_id, bool) or not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id debe ser un entero positivo.")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message es obligatorio y debe ser texto.")

    return notifications_repository.create(
        user_id,
        _truncate(message.strip()),
    )
