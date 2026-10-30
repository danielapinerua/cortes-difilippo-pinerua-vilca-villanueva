"""Conexión a MySQL.

Patrón: UNA conexión por pedido HTTP.
- get_db() abre la conexión la primera vez que se la pide dentro de un pedido
  y la guarda en `g` (el "bolsillo" de Flask para datos de un solo pedido).
- Al terminar el pedido, close_db() la cierra: si todo salió bien hace
  commit, y si hubo una excepción hace rollback (se deshace todo).

Así, si un endpoint hace 3 INSERT y el tercero falla, no queda nada a medias.
"""
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor
from flask import current_app, g


def get_db():
    if "db" not in g:
        cfg = current_app.config
        g.db = pymysql.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            database=cfg["DB_NAME"],
            charset="utf8mb4",
            cursorclass=DictCursor,  # las filas vuelven como diccionarios
            autocommit=False,
        )
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is None:
        return
    try:
        if exception is None:
            db.commit()
        else:
            db.rollback()
    finally:
        db.close()


@contextmanager
def transaction():
    """Agrupa varias escrituras en una sola transacción.

    Uso:
        with db.transaction():
            repo_a.create(...)
            repo_b.create(...)

    Si algo falla, se deshace TODO lo escrito hasta ahí.

    ¿Por qué no alcanza con el commit/rollback de close_db()? Porque cuando un
    errorhandler de Flask atrapa la excepción, Flask llama al teardown con
    `None` y close_db() haría commit igual: un flujo de dos INSERT podría
    dejar la primera fila guardada y la segunda no. Este context manager
    revierte explícitamente antes de que el error siga viaje.
    """
    try:
        yield
    except Exception:
        if "db" in g:
            g.db.rollback()
        raise


def init_app(app):
    app.teardown_appcontext(close_db)
