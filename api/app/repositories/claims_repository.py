"""Capa de acceso a datos para reclamos (US04)."""

from ..db import get_db


SELECT_COLUMNS = """
    id, client_id, service_id, priority_id, administrator_id,
    category, description, status, created_at, resolved_at
"""


def create(client_id, service_id, category, description, priority_id):
    """Registra un reclamo y devuelve su ID."""

    with get_db().cursor() as cur:
        cur.execute(
            """
            INSERT INTO claims
                (client_id, service_id, priority_id, category, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (client_id, service_id, priority_id, category, description),
        )
        return cur.lastrowid


def get_by_id(claim_id):
    """Obtiene un reclamo por su ID."""

    with get_db().cursor() as cur:
        cur.execute(
            f"SELECT {SELECT_COLUMNS} FROM claims WHERE id = %s",
            (claim_id,),
        )
        return cur.fetchone()