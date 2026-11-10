from flask import Blueprint, redirect, url_for

from ..auth import current_user, home_for, token

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    """La raíz no tiene pantalla propia: manda a cada rol a su inicio."""
    if not token():
        return redirect(url_for("auth.login"))
    return redirect(home_for(current_user()))
