"""Crea un usuario (con su perfil) directamente en la base.

La tabla `users` arranca vacía, así que sin esto no hay con quién iniciar sesión.
Se usa desde la carpeta api/ (con la base creada y el .env completo):

    python -m scripts.create_user --email admin@techsolutions.com --password MiClave123 --role admin --name "Samantha"
    python -m scripts.create_user --email cliente@ejemplo.com --password MiClave123 --role client --name "Mariana" --plan-id 1

- role admin  -> inserta en `users` y en `administrators`.
- role client -> inserta en `users` y en `clients` (clients.plan_id es NOT NULL, por eso --plan-id es obligatorio).

La contraseña se guarda hasheada, nunca en texto plano.
"""
import argparse
import sys

import pymysql

from app import create_app
from app.constants import ROLE_ADMIN, ROLE_CLIENT
from app.db import get_db
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Crear un usuario de prueba.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--role", required=True, choices=[ROLE_ADMIN, ROLE_CLIENT])
    parser.add_argument("--name", required=True, help="Nombre que se guarda en el perfil")
    parser.add_argument("--plan-id", type=int, help="Obligatorio si el rol es client")
    args = parser.parse_args()

    if args.role == ROLE_CLIENT and args.plan_id is None:
        parser.error("--plan-id es obligatorio para el rol client")

    app = create_app()
    try:
        # Al salir del `with`, Flask cierra la conexión: commit si todo salió bien, rollback si no.
        with app.app_context():
            with get_db().cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
                    (args.email, hash_password(args.password), args.role),
                )
                user_id = cur.lastrowid
                if args.role == ROLE_ADMIN:
                    cur.execute(
                        "INSERT INTO administrators (user_id, name) VALUES (%s, %s)",
                        (user_id, args.name),
                    )
                else:
                    cur.execute(
                        "INSERT INTO clients (user_id, plan_id, name, email) VALUES (%s, %s, %s, %s)",
                        (user_id, args.plan_id, args.name, args.email),
                    )
    except pymysql.err.IntegrityError as err:
        sys.exit(f"No se pudo crear el usuario (¿email repetido o plan inexistente?): {err}")
    except pymysql.err.OperationalError as err:
        sys.exit(f"No se pudo conectar a la base: {err}")

    print(f"Listo: usuario #{user_id} ({args.role}) creado.")


if __name__ == "__main__":
    main()
