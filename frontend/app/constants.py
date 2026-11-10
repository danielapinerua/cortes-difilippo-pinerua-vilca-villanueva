"""IDs fijos del catálogo. Son los MISMOS que en api/app/constants.py y en el script SQL.
Regla: se compara por ID, nunca por el nombre."""

ROLE_CLIENT = "client"
ROLE_ADMIN = "admin"

STATUS_PENDING = 1      # pendiente
STATUS_IN_REVIEW = 2    # en_revision
STATUS_APPROVED = 3     # aprobado
STATUS_REJECTED = 4     # rechazado
STATUS_COMPLETED = 5    # realizado

# Para los desplegables de filtro: (id, texto que ve la persona)
STATUS_CHOICES = [
    (STATUS_PENDING, "Pendiente"),
    (STATUS_IN_REVIEW, "En revisión"),
    (STATUS_APPROVED, "Aprobada"),
    (STATUS_REJECTED, "Rechazada"),
    (STATUS_COMPLETED, "Realizada"),
]
PRIORITY_CHOICES = [(1, "Alta"), (2, "Media"), (3, "Baja")]

# Color de Bootstrap de cada estado / prioridad (solo presentación)
STATUS_COLORS = {1: "warning", 2: "info", 3: "primary", 4: "danger", 5: "success"}
PRIORITY_COLORS = {1: "danger", 2: "warning", 3: "secondary"}

# Límites que valida el API (el front los repite en los formularios para avisar antes)
MODIFICATION_TYPE_MAX = 100
DESCRIPTION_MAX = 2000
REJECTION_REASON_MAX = 500
