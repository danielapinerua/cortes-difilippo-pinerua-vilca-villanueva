"""Rutas de /api/v1/plans  (US07 - Gestionar planes).

Esta capa es DELIBERADAMENTE finita. Solo hace tres cosas:
  1. leer lo que llega en el pedido HTTP,
  2. llamar al service,
  3. devolver la respuesta con el código HTTP correcto.

Nada de SQL ni de reglas de negocio acá.

Permisos: cualquier usuario logueado puede VER los planes; solo un
administrador puede crearlos, modificarlos o borrarlos.
"""
from flask import Blueprint, jsonify

from ..constants import ROLE_ADMIN
from ..security import login_required, role_required
from ..services import plans_service
from ._helpers import json_body

bp = Blueprint("plans", __name__, url_prefix="/plans")


@bp.get("")
@login_required
def list_plans():
    return jsonify(plans_service.list_plans())


@bp.get("/<int:plan_id>")
@login_required
def get_plan(plan_id):
    return jsonify(plans_service.get_plan(plan_id))


@bp.post("")
@role_required(ROLE_ADMIN)
def create_plan():
    return jsonify(plans_service.create_plan(json_body())), 201


@bp.put("/<int:plan_id>")
@role_required(ROLE_ADMIN)
def update_plan(plan_id):
    return jsonify(plans_service.update_plan(plan_id, json_body()))


@bp.delete("/<int:plan_id>")
@role_required(ROLE_ADMIN)
def delete_plan(plan_id):
    plans_service.delete_plan(plan_id)
    return "", 204
