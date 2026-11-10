"""Fábrica de la aplicación (mismo patrón que el API: create_app)."""
import secrets
from datetime import datetime
from email.utils import parsedate_to_datetime

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from . import constants
from .api_client import ApiError, ApiUnavailable
from .config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    _register_template_helpers(app)
    _register_csrf(app)
    _register_error_handlers(app)

    from .routes import admin, auth, client, main
    for module in (main, auth, client, admin):
        app.register_blueprint(module.bp)

    return app


# ---- Ayudas para las plantillas ---------------------------------------------

def _parse_api_date(value):
    """El API manda fechas como 'Sat, 31 Oct 2026 10:00:00 GMT' (formato por defecto
    de Flask). Dice GMT pero en realidad es la hora del servidor SIN conversión,
    así que NO convertimos zona horaria: mostramos tal cual el reloj."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except (TypeError, ValueError):
        pass
    try:  # por si algún día el API pasa a ISO 8601
        return datetime.fromisoformat(str(value)).replace(tzinfo=None)
    except ValueError:
        return None


def _register_template_helpers(app):
    @app.template_filter("fecha")
    def fecha(value, with_time=True):
        dt = _parse_api_date(value)
        if dt is None:
            return "—"
        return dt.strftime("%d/%m/%Y %H:%M" if with_time else "%d/%m/%Y")

    # Globals: visibles en TODAS las plantillas, incluidas las macros importadas
    # (los context_processor, en cambio, no llegan a las macros).
    app.jinja_env.globals["C"] = constants      # {{ C.STATUS_PENDING }}
    app.jinja_env.globals["csrf_token"] = _csrf_token

    @app.context_processor
    def inject_user():
        from .auth import current_user
        return {"current_user": current_user()}


# ---- CSRF ---------------------------------------------------------------------
# Ataque: una página maliciosa hace que TU navegador mande un POST a nuestro sitio
# (y el navegador adjunta tu cookie de sesión). Defensa: cada formulario lleva un
# código secreto que solo conoce nuestra página; el atacante no puede adivinarlo.

def _csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def _register_csrf(app):
    @app.before_request
    def check_csrf():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            sent = request.form.get("csrf_token", "")
            expected = session.get("csrf", "")
            if not expected or not secrets.compare_digest(sent, expected):
                abort(400, description="El formulario venció. Volvé a intentarlo.")


# ---- Errores -------------------------------------------------------------------
# Un solo lugar decide qué ve la persona cuando algo sale mal. Las vistas solo
# atrapan los errores que pueden resolver ellas (p. ej. 422 → mostrar el formulario).

def _error_page(status, title, message):
    return render_template("error.html", status=status, title=title, message=message), status


def _register_error_handlers(app):
    @app.errorhandler(ApiError)
    def api_error(err):
        if err.status == 401:
            # Token vencido o inválido: limpiamos y mandamos a loguearse.
            session.clear()
            flash("Tu sesión venció. Iniciá sesión de nuevo.", "warning")
            return redirect(url_for("auth.login"))
        if err.status == 403:
            # OJO: acá NO se redirige. Si el rol guardado en la sesión no coincide con el
            # del API, redirigir a "/" te manda de vuelta a la misma página prohibida y
            # queda un bucle infinito. Se muestra la página 403 y listo.
            return _error_page(403, "Sin permiso", "No tenés permiso para hacer eso.")
        if err.status == 404:
            return _error_page(404, "No encontrado", err.message)
        if err.status in (409, 422):
            flash(err.message, "danger")
            return redirect(request.referrer or url_for("main.index"))
        return _error_page(502, "Algo salió mal", "El servidor no pudo completar la operación.")

    @app.errorhandler(ApiUnavailable)
    def api_unavailable(_err):
        return _error_page(503, "Servicio no disponible",
                           "No pudimos conectarnos con el servidor. Probá de nuevo en unos minutos.")

    @app.errorhandler(400)
    def bad_request(err):
        return _error_page(400, "Solicitud inválida", getattr(err, "description", "Pedido inválido."))

    @app.errorhandler(404)
    def not_found(_err):
        return _error_page(404, "Página no encontrada", "La página que buscás no existe.")

    @app.errorhandler(405)
    def not_allowed(_err):
        return _error_page(405, "Método no permitido", "Esa acción no está permitida en esta página.")

    @app.errorhandler(500)
    def server_error(_err):
        return _error_page(500, "Error interno", "Ocurrió un error inesperado. Ya quedó registrado.")
