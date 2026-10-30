"""Rutas de /api/v1/me/services  (US01 - Consultar servicios contratados)."""
from flask import Blueprint, g, jsonify

from ..constants import ROLE_CLIENT
from ..security import role_required
from ..services import services_service

bp = Blueprint("services", __name__, url_prefix="/me/services")


@bp.get("")
@role_required(ROLE_CLIENT)
def list_my_services():
    """Devuelve los servicios que el cliente contrato."""
    return jsonify(services_service.list_my_services(g.current_user["id"]))
