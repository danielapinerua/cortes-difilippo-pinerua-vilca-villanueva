"""Rutas para solicitudes de modificación de servicios (US02)."""

from flask import Blueprint, g, jsonify, request

from ..constants import ROLE_CLIENT
from ..security import role_required
from ..services import service_requests_service
from ._helpers import int_query_args


bp = Blueprint("service_requests", __name__, url_prefix="/me/service-requests")

@bp.post("")
@role_required(ROLE_CLIENT)
def create_service_request():
    """Crea una solicitud de modificación de un servicio."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se esperaba un objeto JSON."}), 400

    result = service_requests_service.create_service_request(
        user_id=g.current_user["id"],
        service_id=data.get("service_id"),
        modification_type=data.get("modification_type"),
        description=data.get("description"),
    )

    return jsonify(result), 201


@bp.get("")
@role_required(ROLE_CLIENT)
def list_my_service_requests():
    """Solicitudes del cliente logueado con su estado (US14 / US05).

    Filtro opcional: ?status_id=. El cliente se identifica por el token; un
    client_id en la URL se ignora a propósito.
    """
    filters = int_query_args("status_id")
    return jsonify(
        service_requests_service.list_my_service_requests(g.current_user["id"], **filters)
    )
