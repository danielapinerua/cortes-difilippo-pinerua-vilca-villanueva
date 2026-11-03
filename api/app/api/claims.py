"""Rutas para reclamos (US04)."""

from flask import Blueprint, g, jsonify, request

from ..constants import ROLE_CLIENT
from ..security import role_required
from ..services import claims_service


bp = Blueprint("claims", __name__, url_prefix="/me/claims")


@bp.post("")
@role_required(ROLE_CLIENT)
def create_claim():
    """Registra un reclamo para un servicio contratado."""

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Se esperaba un objeto JSON."}), 400

    result = claims_service.create_claim(
        user_id=g.current_user["id"],
        service_id=data.get("service_id"),
        category=data.get("category"),
        description=data.get("description"),
    )

    return jsonify(result), 201