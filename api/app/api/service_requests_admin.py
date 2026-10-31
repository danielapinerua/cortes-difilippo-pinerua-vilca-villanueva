"""Rutas para atender solicitudes de modificación (US09)."""

from flask import Blueprint, g, jsonify

from ..constants import ROLE_ADMIN
from ..security import role_required
from ..services import service_requests_service
from ._helpers import json_body

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
