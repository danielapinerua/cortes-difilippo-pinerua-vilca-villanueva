"""Pantallas del administrador: bandeja, detalle y resolución (US14, US09)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from .. import api_client
from ..api_client import ApiError
from ..auth import admin_required, token
from ..constants import PRIORITY_CHOICES, STATUS_CHOICES
from ..helpers import optional_int

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/requests")
@admin_required
def inbox():
    status_id = optional_int(request.args.get("status_id"))
    priority_id = optional_int(request.args.get("priority_id"))
    items = api_client.admin_requests(token(), status_id=status_id, priority_id=priority_id)
    return render_template("admin/inbox.html", items=items, status_id=status_id,
                           priority_id=priority_id, status_choices=STATUS_CHOICES,
                           priority_choices=PRIORITY_CHOICES)


@bp.get("/requests/<int:request_id>")
@admin_required
def detail(request_id):
    item = api_client.admin_request_detail(token(), request_id)
    return render_template("admin/detail.html", item=item, errors={}, reason="")


@bp.post("/requests/<int:request_id>/resolution")
@admin_required
def resolve(request_id):
    decision = request.form.get("decision", "")
    reason = request.form.get("rejection_reason", "").strip()
    try:
        api_client.resolve_request(token(), request_id, decision,
                                   reason if decision == "reject" else None)
    except ApiError as err:
        if err.status == 422:
            # Mostramos el detalle de nuevo, con el error al lado del campo.
            item = api_client.admin_request_detail(token(), request_id)
            return render_template("admin/detail.html", item=item,
                                   errors=err.details or {"_general": err.message},
                                   reason=reason), 422
        if err.status == 409:
            flash("Esa solicitud ya no está pendiente (otra persona la resolvió).", "warning")
            return redirect(url_for("admin.detail", request_id=request_id))
        raise
    flash("Solicitud aprobada." if decision == "approve" else "Solicitud rechazada.", "success")
    return redirect(url_for("admin.inbox"))
