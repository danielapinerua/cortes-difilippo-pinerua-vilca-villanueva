"""Rutas para atender solicitudes de modificación (US09)."""

from flask import Blueprint, g, jsonify

from ..constants import ROLE_ADMIN
from ..security import role_required
from ..services import service_requests_service
from ._helpers import int_query_args, json_body

bp = Blueprint(
    "service_requests_admin",
    __name__,
    url_prefix="/service-requests",
)


@bp.put("/<int:request_id>/resolution")
@role_required(ROLE_ADMIN)
def attend_service_request(request_id):
    """Atiende una solicitud: aprueba o rechaza."""

    data = json_body()
    result = service_requests_service.attend_service_request(
        admin_user_id=g.current_user["id"],
        request_id=request_id,
        decision=data.get("decision"),
        rejection_reason=data.get("rejection_reason"),
    )
    return jsonify(result), 200


@bp.get("")
@role_required(ROLE_ADMIN)
def list_service_requests():
    """Bandeja del administrador (US14), ordenada por prioridad y antigüedad.

    Filtros opcionales: ?status_id=&priority_id=&client_id=
    """
    filters = int_query_args("status_id", "priority_id", "client_id")
    return jsonify(service_requests_service.list_service_requests(**filters))


@bp.get("/<int:request_id>")
@role_required(ROLE_ADMIN)
def get_service_request(request_id):
    """Detalle de una solicitud (404 si no existe)."""
    return jsonify(service_requests_service.get_service_request(request_id))
