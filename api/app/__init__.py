"""Fábrica de la aplicación (patrón "application factory").

En vez de crear `app = Flask(...)` suelto en un archivo, usamos una función
create_app(). Ventajas:
  - los tests pueden crear una app limpia con otra configuración;
  - no hay variables globales que se pisen entre módulos;
  - es el patrón que recomienda la documentación oficial de Flask.
"""
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from . import db
from .errors import register_error_handlers


def create_app(config_object=None):
    # Carga las variables del archivo .env (si existe) ANTES de leer la config.
    load_dotenv()

    if config_object is None:
        from .config import Config as config_object

    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    db.init_app(app)
    register_error_handlers(app)

    from .api import api_bp
    app.register_blueprint(api_bp)

    return app
