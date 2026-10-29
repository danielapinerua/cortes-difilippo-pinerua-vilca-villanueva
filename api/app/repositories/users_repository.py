"""Capa de ACCESO A DATOS para usuarios (tabla `users`).

    users(id, email, password_hash, role ENUM('client','admin'), is_active,
          last_login_at, created_at, updated_at)
"""
from ..db import get_db


def get_by_email(email):
    """Incluye password_hash: solo debe usarse para verificar el login, nunca devolverse al cliente."""
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT id, email, password_hash, role, is_active FROM users WHERE email = %s",
            (email,),
        )
        return cur.fetchone()


def get_by_id(user_id):
    with get_db().cursor() as cur:
        cur.execute(
            "SELECT id, email, role, is_active FROM users WHERE id = %s",
            (user_id,),
        )
        return cur.fetchone()


def touch_last_login(user_id):
    with get_db().cursor() as cur:
        cur.execute("UPDATE users SET last_login_at = NOW() WHERE id = %s", (user_id,))
