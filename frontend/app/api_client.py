"""Único módulo del front que le habla al API.

Por qué un módulo aparte:
  * Si cambia una URL del API, se toca UN solo archivo.
  * Las vistas (routes/) no saben nada de HTTP: piden "dame mis solicitudes".
  * Los errores del API se convierten en excepciones de Python, y el resto de
    la app las maneja en un solo lugar (ver app/__init__.py).
"""
import requests
from flask import current_app

# Una sesión HTTP reutiliza conexiones (más rápido que abrir una por pedido).
# Los tests la reemplazan por una falsa para no necesitar el API real.
_http = requests.Session()


class ApiError(Exception):
    """El API respondió con un error (4xx/5xx) en su formato estándar:
    {"error": {"code", "message", "details"?}}"""

    def __init__(self, status, code, message, details=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details or {}


class ApiUnavailable(Exception):
    """No se pudo hablar con el API (apagado, red caída, tardó demasiado)."""


def _send(method, path, token=None, json=None, params=None):
    url = current_app.config["API_BASE_URL"] + path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    # Los filtros vacíos no se mandan: ?status_id= y nada es lo mismo para el API.
    if params:
        params = {k: v for k, v in params.items() if v not in (None, "")}
    try:
        resp = _http.request(
            method, url, headers=headers, json=json, params=params,
            timeout=current_app.config["API_TIMEOUT"],
        )
    except requests.RequestException as exc:  # ConnectionError, Timeout, etc.
        current_app.logger.error("API inalcanzable (%s %s): %s", method, url, exc)
        raise ApiUnavailable(str(exc)) from exc

    if resp.status_code == 204 or not resp.content:
        return None

    try:
        body = resp.json()
    except ValueError:
        # El API respondió algo que no es JSON (p. ej. una página de error de un proxy).
        current_app.logger.error("Respuesta no JSON del API (%s): %s", resp.status_code, resp.text[:200])
        raise ApiError(502, "bad_gateway", "El servidor respondió de forma inesperada.")

    if resp.status_code >= 400:
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            raise ApiError(resp.status_code, err.get("code", "error"),
                           err.get("message", "Ocurrió un error."), err.get("details"))
        # US02 usa a veces otro formato de error: lo toleramos en vez de romper.
        raise ApiError(resp.status_code, "error", "Ocurrió un error.")
    return body


# ---- Autenticación -----------------------------------------------------------

def login(email, password):
    return _send("POST", "/auth/login", json={"email": email, "password": password})


def register(data):
    return _send("POST", "/auth/register", json=data)


# ---- Cliente -----------------------------------------------------------------

def my_services(token):
    return _send("GET", "/me/services", token)


def my_requests(token, status_id=None):
    return _send("GET", "/me/service-requests", token, params={"status_id": status_id})


def create_request(token, service_id, modification_type, description):
    return _send("POST", "/me/service-requests", token, json={
        "service_id": service_id,
        "modification_type": modification_type,
        "description": description,
    })


# ---- Administrador -----------------------------------------------------------

def admin_requests(token, status_id=None, priority_id=None):
    return _send("GET", "/service-requests", token,
                 params={"status_id": status_id, "priority_id": priority_id})


def admin_request_detail(token, request_id):
    return _send("GET", f"/service-requests/{request_id}", token)


def resolve_request(token, request_id, decision, rejection_reason=None):
    body = {"decision": decision}
    if rejection_reason is not None:
        body["rejection_reason"] = rejection_reason
    return _send("PUT", f"/service-requests/{request_id}/resolution", token, json=body)
