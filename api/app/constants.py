"""Constantes que reflejan los datos fijos del script SQL.

El script carga los catálogos con IDs fijos (decisión documentada en
documentacion/base_datos/base_datos.md, sección 8.1). Por eso el código puede
comparar por ID sin consultar la base. Si el script cambia, se cambia ACÁ.

Regla: en el código comparar por ID (STATUS_PENDING), nunca por nombre
('pendiente'), porque los nombres pueden cambiar y los IDs no.
"""

# users.role
ROLE_CLIENT = "client"
ROLE_ADMIN = "admin"

# plans.id — plan que recibe un visitante al registrarse (US17).
# Debe coincidir con el plan "Gratuito" del script SQL.
DEFAULT_PLAN_ID = 4

# users.password_hash — política de contraseñas (US17).
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# request_statuses.id
STATUS_PENDING = 1      # pendiente
STATUS_IN_REVIEW = 2    # en_revision
STATUS_APPROVED = 3     # aprobado
STATUS_REJECTED = 4     # rechazado
STATUS_COMPLETED = 5    # realizado

# priorities.id
PRIORITY_HIGH = 1       # alta
PRIORITY_MEDIUM = 2     # media
PRIORITY_LOW = 3        # baja
