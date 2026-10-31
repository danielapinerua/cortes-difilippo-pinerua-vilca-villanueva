"""Capa de RUTAS (HTTP).

Todas las rutas cuelgan de /api/v1. Si algún día cambia el contrato de la API
de forma incompatible, se crea /api/v2 sin romper a los que usan la v1.

Para sumar un recurso nuevo (ej. "clients"):
  1. crear app/api/clients.py con su Blueprint,
  2. importarlo y registrarlo acá abajo.
"""
from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

from . import auth, health, plans, services, service_requests # noqa: E402  (se importan acá para evitar importaciones circulares)

api_bp.register_blueprint(health.bp)
api_bp.register_blueprint(auth.bp)
api_bp.register_blueprint(plans.bp)
api_bp.register_blueprint(services.bp)
api_bp.register_blueprint(service_requests.bp)
