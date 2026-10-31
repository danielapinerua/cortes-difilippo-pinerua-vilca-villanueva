"""Capa de acceso a datos para solicitudes de servicios."""

from ..constants import STATUS_PENDING
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


def update_resolution(request_id, status_id, administrator_id, rejection_reason):
    """Marca la solicitud como resuelta (aprobar -> STATUS_COMPLETED,
    rechazar -> STATUS_REJECTED). Solo actualiza si sigue pendiente."""
    with get_db().cursor() as cur:
        cur.execute(
            """
            UPDATE service_requests
            SET status_id = %s,
                administrator_id = %s,
                rejection_reason = %s,
                resolved_at = NOW()
            WHERE id = %s AND status_id = %s
            """,
            (status_id, administrator_id, rejection_reason, request_id, STATUS_PENDING),
        )
        return cur.rowcount
    