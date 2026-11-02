"""Rutas de /api/v1/clients  (US06 - Gestionar clientes).

Todas son solo para administradores: el CU5 es una tarea de backoffice.
"""
from flask import Blueprint, jsonify, request

from ..constants import ROLE_ADMIN
from ..security import role_required
from ..services import clients_service
from ._helpers import int_query_args, json_body

bp = Blueprint("clients", __name__, url_prefix="/clients")


@bp.get("")
@role_required(ROLE_ADMIN)
def list_clients():
    """Listado de clientes. Filtros opcionales: ?search= y ?plan_id=."""
    filters = int_query_args("plan_id")
    search = request.args.get("search", "").strip() or None
    return jsonify(clients_service.list_clients(search=search, **filters))


@bp.get("/<int:client_id>")
@role_required(ROLE_ADMIN)
def get_client(client_id):
    """Detalle de un cliente (404 si no existe)."""
    return jsonify(clients_service.get_client(client_id))


@bp.post("")
@role_required(ROLE_ADMIN)
def create_client():
    """Alta de un cliente. Devuelve 201 con el perfil creado."""
    return jsonify(clients_service.create_client(json_body())), 201


@bp.put("/<int:client_id>")
@role_required(ROLE_ADMIN)
def update_client(client_id):
    """Modificación parcial. Devuelve 200 con el perfil actualizado."""
    return jsonify(clients_service.update_client(client_id, json_body())), 200
