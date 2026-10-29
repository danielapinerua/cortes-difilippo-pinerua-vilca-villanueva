"""Capa de ACCESO A DATOS para planes. Es la ÚNICA que escribe SQL.

Tabla real (fuente de verdad: database/migrations/1_setup_database.sql):
    plans(id, name, description, price, created_at, updated_at)

Reglas de oro:
  - SIEMPRE consultas parametrizadas (%s + valores). Nunca armar el SQL
    pegando strings con f"..." o "+": eso abre la puerta a inyección SQL.
  - Acá no hay reglas de negocio ni validaciones: solo leer y escribir.
  - Los nombres de columna que se interpolan en el SQL (f-string) salen de una
    lista blanca definida acá, jamás de lo que manda el usuario.
"""
from ..db import get_db

TABLE = "plans"
SELECT_COLUMNS = "id, name, description, price"
EDITABLE_COLUMNS = ("name", "description", "price")


def list_all():
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} ORDER BY id")
        return cur.fetchall()


def get(plan_id):
    with get_db().cursor() as cur:
        cur.execute(f"SELECT {SELECT_COLUMNS} FROM {TABLE} WHERE id = %s", (plan_id,))
        return cur.fetchone()  # None si no existe


def create(data):
    columns = [c for c in EDITABLE_COLUMNS if c in data]
    placeholders = ", ".join(["%s"] * len(columns))
    with get_db().cursor() as cur:
        cur.execute(
            f"INSERT INTO {TABLE} ({', '.join(columns)}) VALUES ({placeholders})",
            [data[c] for c in columns],
        )
        return cur.lastrowid


def update(plan_id, data):
    columns = [c for c in EDITABLE_COLUMNS if c in data]
    assignments = ", ".join(f"{c} = %s" for c in columns)
    with get_db().cursor() as cur:
        cur.execute(
            f"UPDATE {TABLE} SET {assignments} WHERE id = %s",
            [data[c] for c in columns] + [plan_id],
        )


def delete(plan_id):
    with get_db().cursor() as cur:
        cur.execute(f"DELETE FROM {TABLE} WHERE id = %s", (plan_id,))
