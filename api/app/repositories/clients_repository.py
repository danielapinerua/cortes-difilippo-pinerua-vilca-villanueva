"""Capa de ACCESO A DATOS para clientes (tabla `clients`).

Tabla real (fuente de verdad: database/migrations/1_setup_database.sql):
    clients(id, user_id, plan_id, name, email, phone, dni, created_at, updated_at)

Igual que el resto de los repositorios: solo SQL parametrizado, sin reglas de
negocio. Las validaciones viven en `app/validators.py`.
"""
from ..db import get_db

TABLE = "clients"
SELECT_COLUMNS = "id, user_id, plan_id, name, email, phone, dni"


def create(user_id, plan_id, name, email, phone=None, dni=None):
    with get_db().cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABLE} (user_id, plan_id, name, email, phone, dni) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, plan_id, name, email, phone, dni),
        )
        return cur.lastrowid


def get_by_id(client_id):
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} WHERE id = %s", (client_id,))
        return cur.fetchone()


def get_by_user_id(user_id):
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} WHERE user_id = %s", (user_id,))
        return cur.fetchone()


def get_by_email(email):
    """Sirve para detectar emails ya usados por clientes sin cuenta de login."""
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} WHERE email = %s", (email,))
        return cur.fetchone()


def get_by_dni(dni):
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} WHERE dni = %s", (dni,))
        return cur.fetchone()

def get_client_id_by_user_id(user_id):
    """Devuelve el id del cliente a partir del user_id, o None si no existe."""
    with get_db().cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
        return row["id"] if row else None