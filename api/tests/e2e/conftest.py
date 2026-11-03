"""Fixtures de los tests E2E (MySQL real).

Se excluyen de la corrida normal: `pytest.ini` agrega `-m "not e2e"`.
Para correrlos hace falta la base `tech_solutions_test`, creada con el mismo
script de migración:

    sed 's/tech_solutions/tech_solutions_test/g' \\
        database/migrations/1_setup_database.sql | mysql -uroot

    cd api && pytest tests/e2e -m e2e
"""
import os

import pytest
from dotenv import load_dotenv

# Cargar .env ANTES de importar app.config: `Config` lee las variables de
# entorno al definirse la clase, y desde acá el import ocurre fuera de
# create_app() (que es quien normalmente llama a load_dotenv).
load_dotenv()

from app import create_app
from app.config import Config
from app.constants import DEFAULT_PLAN_ID, DEFAULT_PLAN_PRICE
from app.db import get_db
from app.security import hash_password

ADMIN_EMAIL = "e2e.admin@ejemplo.com"
ADMIN_PASSWORD = "E2eClave123"
# Prefijo de todo dato creado por los e2e: se borra antes y después de cada test.
PREFIX = "e2e.%"


class E2EConfig(Config):
    DB_NAME = os.environ.get("DB_NAME_TEST", "tech_solutions_test")


def _db_available(app):
    try:
        with app.app_context():
            get_db().ping(reconnect=False)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def app():
    app = create_app(E2EConfig)
    if not _db_available(app):
        pytest.skip("MySQL no disponible o falta la base tech_solutions_test")
    return app


def _cleanup(app):
    """Borra los datos de prueba. El orden respeta las FK."""
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute("DELETE FROM clients WHERE email LIKE %s", (PREFIX,))
            cur.execute(
                "DELETE FROM administrators WHERE user_id IN "
                "(SELECT id FROM users WHERE email LIKE %s)",
                (PREFIX,),
            )
            cur.execute("DELETE FROM users WHERE email LIKE %s", (PREFIX,))
            cur.execute(
                "DELETE FROM plans WHERE name LIKE %s AND id <> %s",
                ("E2E %", DEFAULT_PLAN_ID),
            )
            # Restaurar el plan por defecto: algún test puede cambiarle el nombre.
            cur.execute(
                "UPDATE plans SET name = %s, description = %s, price = %s "
                "WHERE id = %s",
                (
                    "Gratuito",
                    "Plan de bienvenida: acceso al sistema y al catálogo",
                    DEFAULT_PLAN_PRICE,
                    DEFAULT_PLAN_ID,
                ),
            )
        db.commit()


@pytest.fixture
def http(app):
    """Cliente HTTP con un administrador de prueba creado y limpiado."""
    _cleanup(app)
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'admin')",
                (ADMIN_EMAIL, hash_password(ADMIN_PASSWORD)),
            )
            user_id = cur.lastrowid
            cur.execute(
                "INSERT INTO administrators (user_id, name) VALUES (%s, %s)",
                (user_id, "E2E Admin"),
            )
        db.commit()

    yield app.test_client()

    _cleanup(app)


@pytest.fixture
def admin(http):
    r = http.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}
