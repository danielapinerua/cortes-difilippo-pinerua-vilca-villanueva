"""Validaciones del alta de un cliente (US17 - Registro).

Son funciones puras: reciben lo que mandó el visitante y devuelven el valor
limpio o un mensaje de error. No tocan la base ni HTTP, así se prueban solas.

Los límites salen del esquema SQL (fuente de verdad):
    users.email    VARCHAR(255) NOT NULL
    clients.name   VARCHAR(150) NOT NULL
    clients.email  VARCHAR(255) NOT NULL
    clients.phone  VARCHAR(30)  NULL
    clients.dni    VARCHAR(20)  NULL
"""
import re

from .constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

EMAIL_MAX = 255
NAME_MIN = 2
NAME_MAX = 150
PHONE_MAX = 30
DNI_MAX = 20

# Validaciones deliberadamente simples: alcanzan para el alta y no agregan
# dependencias. Si algún día hace falta validar emails con más rigor, se puede
# sumar la librería `email-validator`.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+$")
PHONE_RE = re.compile(r"^\+?\d{7,15}$")
DNI_RE = re.compile(r"^\d{7,8}$")

# Contraseñas tan comunes que se rechazan de entrada.
COMMON_PASSWORDS = {
    "12345678", "123456789", "1234567890", "password", "password1",
    "qwerty123", "abc12345", "admin123", "iloveyou", "contraseña",
}


def validate_registration(data):
    """Devuelve `(valores_limpios, errores)`.

    `data` es el cuerpo JSON ya validado como objeto. Solo se leen los campos
    conocidos: cualquier otro (`role`, `is_active`, `plan_id`…) se ignora.
    """
    errors = {}
    clean = {}

    name = _name(data.get("name"), errors)
    email = _email(data.get("email"), errors)
    password = _password(data.get("password"), email, name, errors)
    _password_confirm(data.get("password_confirm"), password, errors)

    if name is not None:
        clean["name"] = name
    if email is not None:
        clean["email"] = email
    if password is not None:
        clean["password"] = password
    clean["phone"] = _phone(data.get("phone"), errors)
    clean["dni"] = _dni(data.get("dni"), errors)

    return clean, errors


# ---- Campos ----------------------------------------------------------------

def _name(value, errors):
    if not isinstance(value, str) or not value.strip():
        errors["name"] = "Es obligatorio."
        return None

    name = " ".join(value.split())  # colapsa espacios repetidos
    if len(name) < NAME_MIN:
        errors["name"] = f"Debe tener al menos {NAME_MIN} caracteres."
    elif len(name) > NAME_MAX:
        errors["name"] = f"Máximo {NAME_MAX} caracteres."
    elif not NAME_RE.match(name) or sum(c.isalpha() for c in name) < NAME_MIN:
        errors["name"] = "Solo puede contener letras, espacios, apóstrofes, puntos y guiones."
    else:
        return name
    return None


def _email(value, errors):
    if not isinstance(value, str) or not value.strip():
        errors["email"] = "Es obligatorio."
        return None

    email = value.strip().lower()
    if len(email) > EMAIL_MAX:
        errors["email"] = f"Máximo {EMAIL_MAX} caracteres."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Ingresá un email válido."
    else:
        return email
    return None


def _password(value, email, name, errors):
    if not isinstance(value, str) or not value:
        errors["password"] = "Es obligatoria."
        return None

    # La contraseña NO se recorta: los espacios también son parte de ella.
    if len(value) < PASSWORD_MIN_LENGTH:
        errors["password"] = f"Debe tener al menos {PASSWORD_MIN_LENGTH} caracteres."
    elif len(value) > PASSWORD_MAX_LENGTH:
        errors["password"] = f"Máximo {PASSWORD_MAX_LENGTH} caracteres."
    elif not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        errors["password"] = "Debe combinar letras y números."
    elif value.lower() in COMMON_PASSWORDS:
        errors["password"] = "Es demasiado común. Elegí otra."
    elif email and value.lower() == email:
        errors["password"] = "No puede ser igual al email."
    elif name and value.lower() == name.lower():
        errors["password"] = "No puede ser igual al nombre."
    else:
        return value
    return None


def _password_confirm(value, password, errors):
    # Si la contraseña ya falló, no sumamos un segundo error que confunda.
    if password is None:
        return
    if not isinstance(value, str) or value != password:
        errors["password_confirm"] = "Las contraseñas no coinciden."


def _phone(value, errors):
    if value is None or value == "":
        return None

    text = _as_text(value)
    if text is None:
        errors["phone"] = "Debe ser texto."
        return None

    phone = re.sub(r"[\s().-]", "", text)  # "+54 911 2222-3333" -> "+5491122223333"
    if len(phone) > PHONE_MAX or not PHONE_RE.match(phone):
        errors["phone"] = "Ingresá un teléfono válido (7 a 15 dígitos, con + opcional)."
        return None
    return phone


def _dni(value, errors):
    if value is None or value == "":
        return None

    text = _as_text(value)
    if text is None:
        errors["dni"] = "Debe ser texto."
        return None

    dni = re.sub(r"[\s.]", "", text)  # "28.456.321" -> "28456321"
    if len(dni) > DNI_MAX or not DNI_RE.match(dni):
        errors["dni"] = "Ingresá un DNI válido (7 u 8 dígitos)."
        return None
    return dni


def _as_text(value):
    """Acepta strings y números (un teléfono puede venir como número en JSON)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    return None
