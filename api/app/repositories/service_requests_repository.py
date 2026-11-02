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


# ---- Consultas de solicitudes con datos legibles (US14 / US05) ---------------
# Una sola consulta con JOIN trae, además de los ids, el nombre del cliente, del
# servicio, del estado y de la prioridad. LEFT JOIN en priorities porque una
# solicitud recién creada todavía no tiene prioridad asignada (priority_id NULL).
_LIST_SELECT = """
    SELECT r.id, r.client_id, c.name AS client_name,
           r.service_id, s.name AS service_name,
           r.status_id, st.name AS status_name,
           r.priority_id, p.name AS priority_name, p.level AS priority_level,
           r.modification_type, r.description, r.rejection_reason,
           r.created_at, r.resolved_at
    FROM service_requests r
    JOIN clients c ON c.id = r.client_id
    JOIN services s ON s.id = r.service_id
    JOIN request_statuses st ON st.id = r.status_id
    LEFT JOIN priorities p ON p.id = r.priority_id
"""

# Más urgentes primero (level 1 = alta). Las que todavía no tienen prioridad van
# al final: en MySQL un NULL se ordena primero por defecto, por eso el
# `(p.level IS NULL)` previo. Dentro de cada prioridad, las más antiguas primero.
_LIST_ORDER = " ORDER BY (p.level IS NULL), p.level ASC, r.created_at ASC, r.id ASC"


def search(client_id=None, status_id=None, priority_id=None):
    """Lista solicitudes. Cada filtro es opcional; los que llegan se combinan con AND.

    Las condiciones son textos FIJOS escritos acá y los valores van por %s,
    así que no hay forma de inyectar SQL desde la URL.
    """
    conditions, params = [], []
    if client_id is not None:
        conditions.append("r.client_id = %s")
        params.append(client_id)
    if status_id is not None:
        conditions.append("r.status_id = %s")
        params.append(status_id)
    if priority_id is not None:
        conditions.append("r.priority_id = %s")
        params.append(priority_id)

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db().cursor() as cur:
        cur.execute(_LIST_SELECT + where + _LIST_ORDER, params)
        return cur.fetchall()


def get_detail(request_id):
    """Una solicitud con los mismos datos legibles que el listado, o None si no existe."""
    with get_db().cursor() as cur:
        cur.execute(_LIST_SELECT + " WHERE r.id = %s", (request_id,))
        return cur.fetchone()
