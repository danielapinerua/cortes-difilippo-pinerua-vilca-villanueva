"""Capa de negocio para solicitudes de servicios."""

from ..errors import NotFoundError, ValidationError
from ..repositories import clients_repository, service_requests_repository

def create_service_request(user_id, service_id, modification_type, description=None):
    """Crea una solicitud de modificación para un servicio contratado."""

    client_id = clients_repository.get_client_id_by_user_id(user_id)

    if client_id is None:
        raise NotFoundError("No existe el perfil de cliente.")

    if not service_requests_repository.is_contracted_by_client(client_id, service_id):
        raise NotFoundError("El cliente no tiene contratado ese servicio.")

    if not isinstance(modification_type, str) or not modification_type.strip():
        raise ValidationError("El tipo de modificación es obligatorio.")

    modification_type = modification_type.strip()

    if len(modification_type) > 100:
        raise ValidationError("El tipo de modificación no puede superar los 100 caracteres.")

    if description is not None:
        if not isinstance(description, str):
            raise ValidationError("La descripción debe ser un texto.")

        description = description.strip()

        if not description:
            description = None

    request_id = service_requests_repository.create(
        client_id, service_id, modification_type, description
    )

    return service_requests_repository.get_by_id(request_id)

    