"""Capa de ACCESO A DATOS para administradores (tabla `administrators`).

    administrators(id, user_id, name, created_at, updated_at)

Relación: un usuario con role 'admin' tiene un perfil en esta tabla
(un único usuario admin = un único administrador).
"""
from ..db import get_db

SELECT_COLUMNS = "id, user_id, name"


def get_by_user_id(user_id):
    """Devuelve el administrador a partir del user_id, o None si no existe."""
    with get_db().cursor() as cur:
        cur.execute(
            f"SELECT {SELECT_COLUMNS} FROM administrators WHERE user_id = %s",
            (user_id,),
        )
        return cur.fetchone()
