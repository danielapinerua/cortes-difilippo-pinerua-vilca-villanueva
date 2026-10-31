"""Capa de acceso a datos para solicitudes de servicios."""

from ..db import get_db

SELECT_COLUMNS = """
    id, client_id, service_id, status_id, priority_id,
    administrator_id, modification_type, description,
    rejection_reason, created_at, resolved_at
"""


def create(client_id, service_id, modification_type, description=None):
    with get_db().cursor() as cur:
        cur.execute(
            """
            INSERT INTO service_requests
                (client_id, service_id, modification_type, description)
            VALUES (%s, %s, %s, %s)
            """,
            (client_id, service_id, modification_type, description),
        )
        return cur.lastrowid


def get_by_id(request_id):
    with get_db().cursor() as cur:
        cur.execute(
            f"SELECT {SELECT_COLUMNS} FROM service_requests WHERE id = %s",
            (request_id,),
        )
        return cur.fetchone()


def is_contracted_by_client(client_id, service_id):
    with get_db().cursor() as cur:
        cur.execute(
            """
            SELECT 1
            FROM client_services
            WHERE client_id = %s AND service_id = %s
            LIMIT 1
            """,
            (client_id, service_id),
        )
        return cur.fetchone() is not None
    