"""Capa de negocio para solicitudes de servicios."""

from flask import current_app

from .. import db
from ..constants import STATUS_COMPLETED, STATUS_PENDING, STATUS_REJECTED
from ..errors import ConflictError, NotFoundError, ValidationError
from ..repositories import administrators_repository, clients_repository, service_requests_repository
from . import notifications_service

MODIFICATION_TYPE_MAX = 100
DESCRIPTION_MAX = 2000


def _validate_create(service_id, modification_type, description):
    """Valida el alta y devuelve (valores_limpios, errores)."""
    errors, clean = {}, {}

    if isinstance(service_id, bool) or not isinstance(service_id, int) or service_id <= 0:
        errors["service_id"] = "Es obligatorio y debe ser un entero positivo."
    else:
        clean["service_id"] = service_id

    if not isinstance(modification_type, str) or not modification_type.strip():
        errors["modification_type"] = "Es obligatorio y debe ser texto."
    elif len(modification_type.strip()) > MODIFICATION_TYPE_MAX:
        errors["modification_type"] = f"Máximo {MODIFICATION_TYPE_MAX} caracteres."
    else:
        clean["modification_type"] = modification_type.strip()

    if description is not None:
        if not isinstance(description, str):
            errors["description"] = "Debe ser texto."
        elif len(description.strip()) > DESCRIPTION_MAX:
            errors["description"] = f"Máximo {DESCRIPTION_MAX} caracteres."
        else:
            clean["description"] = description.strip() or None
    else:
        clean["description"] = None

    return clean, errors


def create_service_request(user_id, service_id, modification_type, description=None):
    """Crea una solicitud de modificación para un servicio contratado (US02)."""
    client_id = clients_repository.get_client_id_by_user_id(user_id)

    if client_id is None:
        raise NotFoundError("No existe el perfil de cliente.")

    clean, errors = _validate_create(service_id, modification_type, description)
    if errors:
        raise ValidationError("Hay datos inválidos.", details=errors)

    if not service_requests_repository.is_contracted_by_client(
        client_id, clean["service_id"]
    ):
        raise NotFoundError("El cliente no tiene contratado ese servicio.")

    request_id = service_requests_repository.create(
        client_id,
        clean["service_id"],
        clean["modification_type"],
        clean["description"],
    )

    row = service_requests_repository.get_detail(request_id)
    if row is None:
        raise NotFoundError("La solicitud no existe.")
    return row


def _resolution_message(detail, decision, reason):
    """Arma el texto de la notificación. El service lo trunca a 500."""
    if decision == "approve":
        return (
            f"Tu solicitud #{detail['id']} ({detail['service_name']}) fue aprobada. "
            f"Estado: {detail['status_name']}."
        )
    return (
        f"Tu solicitud #{detail['id']} ({detail['service_name']}) fue rechazada. "
        f"Motivo: {reason}"
    )


def attend_service_request(admin_user_id, request_id, decision, rejection_reason=None):
    """Atiende una solicitud: aprueba (-> realizado) o rechaza (con motivo).

    El UPDATE de la solicitud y el INSERT de la notificación son atómicos:
    si falla la notificación, se revierte la resolución.
    """

    # 1. Validar la decisión: solo "approve" o "reject".
    if decision not in ("approve", "reject"):
        raise ValidationError(
            "La decisión debe ser 'approve' o 'reject'.",
            details={"decision": "Debe ser 'approve' o 'reject'."},
        )

    # 2. Si se rechaza, el motivo es obligatorio.
    reason = None
    if decision == "reject":
        reason = rejection_reason.strip() if isinstance(rejection_reason, str) else ""
        if not reason:
            raise ValidationError(
                "El motivo del rechazo es obligatorio.",
                details={"rejection_reason": "El motivo del rechazo es obligatorio."},
            )
        if len(reason) > 500:
            raise ValidationError(
                "El motivo del rechazo no puede superar los 500 caracteres.",
                details={"rejection_reason": "El motivo del rechazo no puede superar los 500 caracteres."},
            )

    # 3. Buscar la solicitud.
    request = service_requests_repository.get_by_id(request_id)
    if request is None:
        raise NotFoundError("La solicitud no existe.")

    # 4. Solo se atiende una solicitud en estado pendiente.
    if request["status_id"] != STATUS_PENDING:
        raise ConflictError("La solicitud ya no está pendiente.")

    # 5. Buscar el administrador que atiende.
    administrator = administrators_repository.get_by_user_id(admin_user_id)
    if administrator is None:
        raise NotFoundError("No existe el perfil de administrador.")

    # 6. Definir el estado de salida.
    status_id = STATUS_COMPLETED if decision == "approve" else STATUS_REJECTED

    # 7. Resolver la solicitud y notificar en una sola transacción.
    with db.transaction():
        client = clients_repository.get_by_id(request["client_id"])
        recipient_user_id = client["user_id"] if client else None

        rows = service_requests_repository.update_resolution(
            request_id, status_id, administrator["id"], reason
        )

        # Si no se actualizó, la solicitud ya no estaba pendiente.
        if rows == 0:
            raise ConflictError("La solicitud ya no está pendiente.")

        detail = service_requests_repository.get_detail(request_id)
        if detail is None:
            raise NotFoundError("La solicitud no existe.")

        if recipient_user_id is None:
            current_app.logger.warning(
                "Solicitud %s resuelta sin notificación: "
                "el cliente %s no tiene user_id.",
                request_id,
                request["client_id"],
            )
        else:
            notifications_service.create_notification(
                recipient_user_id,
                _resolution_message(detail, decision, reason),
            )

    # 8. Devolver el detalle legible.
    return detail



# ---- Consulta de solicitudes (US14 / US05) -----------------------------------

def list_service_requests(client_id=None, status_id=None, priority_id=None):
    """Bandeja del administrador: todas las solicitudes, con filtros opcionales."""
    return service_requests_repository.search(
        client_id=client_id, status_id=status_id, priority_id=priority_id
    )


def get_service_request(request_id):
    """Detalle de una solicitud (administrador)."""
    row = service_requests_repository.get_detail(request_id)
    if row is None:
        raise NotFoundError("La solicitud no existe.")
    return row


def list_my_service_requests(user_id, status_id=None):
    """Solicitudes del cliente logueado (US05: ahí ve el estado de cada una).

    El client_id se resuelve desde el usuario del token. Nunca se acepta uno
    que venga en la URL: así un cliente solo puede ver SUS solicitudes.
    Una lista vacía es una respuesta válida (todavía no pidió nada).
    """
    client_id = clients_repository.get_client_id_by_user_id(user_id)
    if client_id is None:
        raise NotFoundError("No existe el perfil de cliente.")
    return service_requests_repository.search(client_id=client_id, status_id=status_id)
