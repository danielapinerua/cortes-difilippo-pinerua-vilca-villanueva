"""Capa de ACCESO A DATOS para clientes (tabla `clients`).

Tabla real (fuente de verdad: database/migrations/1_setup_database.sql):
    clients(id, user_id, plan_id, name, email, phone, dni, created_at, updated_at)

Igual que el resto de los repositorios: solo SQL parametrizado, sin reglas de
negocio. Las validaciones viven en `app/validators.py`.

`create` y los `get_by_*` los usa el registro (US17); `search`, `get_detail` y
`update` los usa la gestión de clientes (US06).
"""
from ..db import get_db

TABLE = "clients"
SELECT_COLUMNS = "id, user_id, plan_id, name, email, phone, dni"
EDITABLE_COLUMNS = ("user_id", "plan_id", "name", "email", "phone", "dni")

# El listado y el detalle traen el plan ya resuelto (un solo SELECT con JOIN),
# igual que las consultas de solicitudes de US14.
_DETAIL_SELECT = """
    SELECT c.id, c.user_id, c.plan_id, c.name, c.email, c.phone, c.dni,
           c.created_at, c.updated_at,
           p.name AS plan_name, p.price AS plan_price
    FROM clients c
    JOIN plans p ON p.id = c.plan_id
"""


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


# ---- Gestión de clientes (US06 / CU5) ---------------------------------------

def _escape_like(text):
    """Neutraliza los comodines de LIKE para que el usuario busque texto literal."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search(search=None, plan_id=None):
    """Lista clientes con su plan. Cada filtro es opcional y se combina con AND.

    Las condiciones son textos FIJOS escritos acá y los valores van por %s,
    así que no hay forma de inyectar SQL desde la URL.
    """
    conditions, params = [], []
    if plan_id is not None:
        conditions.append("c.plan_id = %s")
        params.append(plan_id)
    if search:
        term = f"%{_escape_like(search)}%"
        conditions.append("(c.name LIKE %s OR c.email LIKE %s OR c.dni LIKE %s)")
        params.extend([term, term, term])

    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db().cursor() as cur:
        cur.execute(_DETAIL_SELECT + where + " ORDER BY c.name, c.id", params)
        return cur.fetchall()


def get_detail(client_id):
    """Un cliente con el nombre y el precio de su plan, o None si no existe."""
    with get_db().cursor() as cur:
        cur.execute(_DETAIL_SELECT + " WHERE c.id = %s", (client_id,))
        return cur.fetchone()


def update(client_id, data):
    """Actualiza solo las columnas permitidas que vengan en `data`.

    `updated_at` lo mantiene MySQL solo (ON UPDATE CURRENT_TIMESTAMP).
    """
    columns = [c for c in EDITABLE_COLUMNS if c in data]
    if not columns:
        return 0
    assignments = ", ".join(f"{c} = %s" for c in columns)
    with get_db().cursor() as cur:
        cur.execute(
            f"UPDATE {TABLE} SET {assignments} WHERE id = %s",
            [data[c] for c in columns] + [client_id],
        )
        return cur.rowcount


def email_exists(email, exclude_id=None):
    """¿Otro cliente usa ese email? `exclude_id` permite guardar el propio."""
    return _exists("email", email, exclude_id)


def dni_exists(dni, exclude_id=None):
    return _exists("dni", dni, exclude_id)


def user_id_exists(user_id, exclude_id=None):
    return _exists("user_id", user_id, exclude_id)


def _exists(column, value, exclude_id):
    # `column` sale de una lista blanca fija (nunca de lo que manda el usuario).
    sql = f"SELECT 1 FROM {TABLE} WHERE {column} = %s"
    params = [value]
    if exclude_id is not None:
        sql += " AND id <> %s"
        params.append(exclude_id)
    sql += " LIMIT 1"
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() is not None
