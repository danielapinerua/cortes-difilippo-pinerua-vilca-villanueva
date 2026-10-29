"""Configuración de la API.

Todo lo que cambia según la máquina (contraseñas, host de la base, etc.)
se lee de variables de entorno, así nunca queda escrito en el código.
Las variables se cargan desde el archivo .env (ver .env.example).
"""
import os


class Config:
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "tech_solutions")

    # Clave con la que se firman los tokens de login. En producción tiene que ser
    # larga y secreta; quien la conozca puede fabricar sesiones de administrador.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-cambiar-en-.env")
    TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", str(8 * 3600)))

    # Lista separada por comas de los orígenes del frontend permitidos.
    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:5500").split(",")
        if o.strip()
    ]

    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "clave-de-tests"
