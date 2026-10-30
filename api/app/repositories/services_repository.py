"""Capa de ACCESO A DATOS para servicios contratados.

    client_services(client_id, service_id, contracted_at)  -- relacion N:M "contrata"
    services(id, name, description)                          -- catalogo

Es la UNICA capa que escribe SQL.
"""
from ..db import get_db

CONTRACTED_COLUMNS = "s.id, s.name, s.description, cs.contracted_at"


def list_contracted_by_client(client_id):
    """Devuelve los servicios que el cliente contrato, con su fecha."""
    with get_db().cursor() as cur:
        cur.execute(
            f"SELECT {CONTRACTED_COLUMNS} FROM client_services cs "
            f"JOIN services s ON cs.service_id = s.id "
            f"WHERE cs.client_id = %s ORDER BY s.id",
            (client_id,),
        )
        return cur.fetchall()
