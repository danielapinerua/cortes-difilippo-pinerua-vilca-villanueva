"""Errores de la API.

Regla: toda respuesta de error tiene el mismo formato, así el frontend
siempre sabe cómo leerla:

    {"error": {"code": "not_found", "message": "No existe el plan 7"}}

Desde services/ se lanza un ApiError (o una subclase) y el manejador de
abajo lo convierte en la respuesta HTTP correcta. Las rutas no necesitan
try/except.
"""
import pymysql
from flask import jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(ApiError):
    """Datos inválidos o faltantes (HTTP 422)."""
    status_code = 422
    code = "validation_error"


class UnauthorizedError(ApiError):
    """No hay sesión válida: falta el token, venció o las credenciales son malas (HTTP 401)."""
    status_code = 401
    code = "unauthorized"


class ForbiddenError(ApiError):
    """Hay sesión, pero el rol no alcanza para esta acción (HTTP 403)."""
    status_code = 403
    code = "forbidden"


class NotFoundError(ApiError):
    """El recurso pedido no existe (HTTP 404)."""
    status_code = 404
    code = "not_found"


class ConflictError(ApiError):
    """El pedido choca con el estado actual de los datos (HTTP 409)."""
    status_code = 409
    code = "conflict"


class DuplicateError(ConflictError):
    """El valor ya existe y una restricción UNIQUE lo impide (HTTP 409)."""
    code = "duplicate_entry"


class InvalidReferenceError(ConflictError):
    """Se referencia un registro que no existe (HTTP 409)."""
    code = "invalid_reference"


def _error_response(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


# Cuando MySQL rechaza un duplicado (error 1062) informa qué índice UNIQUE
# falló. Esto traduce ese índice al campo del formulario que hay que marcar.
_DUPLICATE_FIELDS = {
    "uq_users_email": ("email", "Ya existe una cuenta con ese email."),
    "uq_clients_email": ("email", "Ya existe una cuenta con ese email."),
    "uq_clients_dni": ("dni", "Ya existe una cuenta con ese DNI."),
    "uq_plans_name": ("name", "Ya existe un plan con ese nombre."),
}


def _duplicate_response(err):
    detail = " ".join(str(arg) for arg in err.args)
    for constraint, (field, message) in _DUPLICATE_FIELDS.items():
        if constraint in detail:
            return _error_response(409, "duplicate_entry", message, details={field: "Ya existe."})
    return _error_response(409, "duplicate_entry", "Ya existe un registro con ese valor.")


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return _error_response(err.status_code, err.code, err.message, err.details)

    @app.errorhandler(pymysql.err.IntegrityError)
    def handle_integrity_error(err):
        # MySQL avisa qué restricción falló con un número en args[0].
        mysql_code = err.args[0] if err.args else None
        if mysql_code == 1062:  # UNIQUE: ej. un plan con nombre repetido, un email ya registrado
            return _duplicate_response(err)
        if mysql_code == 1451:  # FK al borrar/modificar: ej. borrar un plan que tiene clientes
            return _error_response(409, "in_use", "No se puede completar: hay otros registros que dependen de este.")
        if mysql_code == 1452:  # FK al insertar: ej. un service_id que no existe
            return _error_response(409, "invalid_reference", "Se hace referencia a un registro que no existe.")
        return _error_response(409, "integrity_error", "La operación viola una restricción de la base de datos.")

    @app.errorhandler(pymysql.err.OperationalError)
    def handle_db_down(err):
        app.logger.exception("No se pudo operar con la base de datos")
        return _error_response(503, "db_unavailable", "La base de datos no está disponible.")

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        # 404 de ruta inexistente, 405 método no permitido, etc.
        return _error_response(err.code, err.name.lower().replace(" ", "_"), err.description)

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        app.logger.exception("Error no controlado")
        return _error_response(500, "internal_error", "Error interno del servidor.")
