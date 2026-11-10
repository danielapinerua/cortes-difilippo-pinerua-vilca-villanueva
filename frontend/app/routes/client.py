"""Pantallas del cliente: sus servicios, nueva solicitud y seguimiento (US02, US05, US14)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import api_client
from ..api_client import ApiError
from ..auth import client_required, token
from ..constants import STATUS_CHOICES
from ..helpers import optional_int

bp = Blueprint("client", __name__)


@bp.get("/services")
@client_required
def services():
    return render_template("client/services.html", services=api_client.my_services(token()))


@bp.route("/requests/new", methods=["GET", "POST"])
@client_required
def new_request():
    services = api_client.my_services(token())
    errors, values = {}, {"service_id": request.args.get("service_id", "")}

    if request.method == "POST":
        values = {
            "service_id": request.form.get("service_id", ""),
            "modification_type": request.form.get("modification_type", "").strip(),
            "description": request.form.get("description", "").strip(),
        }
        service_id = optional_int(values["service_id"])
        if service_id is None:
            errors["service_id"] = "Elegí un servicio."
        else:
            try:
                created = api_client.create_request(
                    token(), service_id, values["modification_type"], values["description"] or None
                )
            except ApiError as err:
                if err.status == 422:
                    errors = err.details or {"_general": err.message}
                elif err.status == 404:
                    errors = {"service_id": err.message}
                else:
                    raise
            else:
                flash(f"Solicitud #{created['id']} enviada. Te avisamos cuando se resuelva.", "success")
                return redirect(url_for("client.my_requests"))
    return render_template("client/new_request.html", services=services, errors=errors, values=values)


@bp.get("/requests")
@client_required
def my_requests():
    status_id = optional_int(request.args.get("status_id"))
    items = api_client.my_requests(token(), status_id=status_id)
    return render_template("client/requests.html", items=items, status_id=status_id,
                           status_choices=STATUS_CHOICES)
