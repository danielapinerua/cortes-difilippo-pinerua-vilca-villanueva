"""Login, registro y logout (US16 y US17)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .. import api_client
from ..api_client import ApiError
from ..auth import home_for, start_session, current_user, token

bp = Blueprint("auth", __name__)

REGISTER_FIELDS = ("name", "email", "phone", "dni")  # se vuelven a mostrar si hay error (la contraseña NO)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if token():
        return redirect(home_for(current_user()))

    error = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            data = api_client.login(email, password)
        except ApiError as err:
            if err.status in (401, 422):
                # Mismo mensaje para email o contraseña mal (US16: no revelar cuál falló).
                error = err.message if err.status == 401 else "Completá el email y la contraseña."
            else:
                raise
        else:
            start_session(data)
            return redirect(home_for(data["user"]))
    return render_template("login.html", error=error, email=email)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if token():
        return redirect(home_for(current_user()))

    errors, values = {}, {}
    if request.method == "POST":
        values = {f: request.form.get(f, "").strip() for f in REGISTER_FIELDS}
        payload = dict(values)
        payload["password"] = request.form.get("password", "")
        payload["password_confirm"] = request.form.get("password_confirm", "")
        # Teléfono y DNI son opcionales: vacío → null para el API.
        for optional in ("phone", "dni"):
            payload[optional] = payload[optional] or None
        try:
            api_client.register(payload)
        except ApiError as err:
            if err.status in (409, 422):
                errors = err.details or {}
                if not errors:  # 409 sin detalle: mostramos el mensaje general
                    errors = {"_general": err.message}
            else:
                raise
        else:
            flash("¡Cuenta creada! Ahora iniciá sesión.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", errors=errors, values=values)


@bp.post("/logout")
def logout():
    # POST y no GET: así un link/imagen en otra página no puede cerrarte la sesión.
    session.clear()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("auth.login"))
