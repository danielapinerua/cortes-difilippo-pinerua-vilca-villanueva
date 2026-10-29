"""Rutas de /api/v1/auth  (US16 - Iniciar sesión)."""
from flask import Blueprint, g, jsonify

from ..security import login_required
from ..services import auth_service
from ._helpers import json_body

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
def login():
    return jsonify(auth_service.login(json_body()))


@bp.get("/me")
@login_required
def me():
    """Devuelve el usuario del token. El frontend lo usa para saber qué pantalla mostrar."""
    return jsonify(auth_service.current_user(g.current_user["id"]))
