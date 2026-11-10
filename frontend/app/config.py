"""Configuración del frontend. Todo lo que cambia entre tu PC y producción
vive en variables de entorno, no escrito en el código."""
import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-solo-para-desarrollo-no-usar-en-produccion")
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:5000/api/v1").rstrip("/")
    API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "8"))

    # La sesión (cookie) guarda el token del API. Estas banderas la protegen:
    SESSION_COOKIE_HTTPONLY = True      # JavaScript de la página NO puede leerla (frena robo por XSS)
    SESSION_COOKIE_SAMESITE = "Lax"     # el navegador no la manda en POST que vienen de otros sitios
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # igual que el token del API


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test"
    API_BASE_URL = "http://api.test/api/v1"
