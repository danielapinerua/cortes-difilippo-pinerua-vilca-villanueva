"""Capa de ACCESO A DATOS para clientes (tabla `clients`).

    clients(id, user_id, plan_id, name, email, phone, dni)

Relación: un usuario puede tener perfil de cliente (user_id -> clients.user_id)
o de administrador. Acá se busca el client_id a partir del user_id.
"""
from ..db import get_db


def get_client_id_by_user_id(user_id):
    """Devuelve el id del cliente a partir del user_id, o None si no existe."""
    with get_db().cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        return row["id"] if row else None
