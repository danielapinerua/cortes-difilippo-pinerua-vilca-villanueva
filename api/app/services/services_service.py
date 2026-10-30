"""Capa de NEGOCIO para consultar servicios contratados (US01)."""
from ..errors import NotFoundError
from ..repositories import clients_repository, services_repository


def _to_dict(row):
    """Convierte una fila del repository en el dict que devuelve la API."""
    return dict(row)


def list_my_services(user_id):
    """Devuelve los servicios que el cliente (user_id) contrato."""
    client_id = clients_repository.get_client_id_by_user_id(user_id)
    if client_id is None:
        raise NotFoundError("No existe el perfil de cliente.")
    return [_to_dict(r) for r in services_repository.list_contracted_by_client(client_id)]
