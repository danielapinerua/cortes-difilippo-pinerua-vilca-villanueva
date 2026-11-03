"""Capa de negocio para reclamos (US04)."""

from ..constants import PRIORITY_MEDIUM
from ..errors import NotFoundError, ValidationError
from ..repositories import (
    clients_repository,
    claims_repository,
    service_requests_repository,
)


def create_claim(user_id, service_id, category, description):
    """Registra un reclamo sobre un servicio contratado."""

    # 1. Buscar el perfil de cliente asociado al usuario autenticado.
    client_id = clients_repository.get_client_id_by_user_id(user_id)

    if client_id is None:
        raise NotFoundError("No existe el perfil de cliente.")

    # 2. Validar el servicio seleccionado.
    if isinstance(service_id, bool) or not isinstance(service_id, int):
        raise ValidationError("El servicio seleccionado no es válido.")

    if not service_requests_repository.is_contracted_by_client(client_id, service_id):
        raise NotFoundError("El cliente no tiene contratado ese servicio.")

    # 3. Validar la categoría.
    valid_categories = ("technical", "support", "service", "other")

    if not isinstance(category, str) or category not in valid_categories:
        raise ValidationError(
            "La categoría debe ser technical, support, service u other."
        )

    # 4. Validar la descripción.
    if not isinstance(description, str) or not description.strip():
        raise ValidationError("El motivo del reclamo es obligatorio.")

    description = description.strip()

    # 5. Registrar el reclamo con prioridad media inicial.
    claim_id = claims_repository.create(
        client_id=client_id,
        service_id=service_id,
        category=category,
        description=description,
        priority_id=PRIORITY_MEDIUM,
    )

    # 6. Recuperar el reclamo registrado.
    return claims_repository.get_by_id(claim_id)