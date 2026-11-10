"""API FALSO en memoria, para probar el front sin MySQL ni el backend real.

Imita lo importante del API verdadero:
  * mismas rutas, mismos roles (401/403) y mismo formato de error;
  * mismas validaciones que importan para las pantallas (422 con `details`);
  * fechas serializadas por Flask (formato RFC-822 "… GMT"), igual que el real.
Si el API real cambia un contrato, este archivo es lo que hay que actualizar.
"""
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request

PASSWORD = "Clave-de-prueba-1"


def build_state():
    return {
        "users": {
            1: {"id": 1, "email": "admin@test.com", "role": "admin", "password": PASSWORD},
            2: {"id": 2, "email": "cliente@test.com", "role": "client", "password": PASSWORD},
            3: {"id": 3, "email": "otro@test.com", "role": "client", "password": PASSWORD},
        },
        "client_of_user": {2: 7, 3: 8},
        "client_names": {7: "Mariana Gómez", 8: "Pablo Ruiz"},
        "services": {
            3: {"id": 3, "name": "Consultoría en Marketing Digital",
                "description": "Estrategia y campañas.", "contracted_at": datetime(2026, 9, 1, 9, 0)},
            4: {"id": 4, "name": "Soporte Técnico Mensual",
                "description": None, "contracted_at": datetime(2026, 9, 15, 9, 0)},
        },
        "contracted": {7: [3, 4], 8: [3]},
        "requests": [],
        "next_id": 1,
        "calls": [],   # (método, ruta) de cada pedido recibido, para que los tests lo inspeccionen
    }


STATUS = {1: "pendiente", 2: "en_revision", 3: "aprobado", 4: "rechazado", 5: "realizado"}
PRIORITY = {1: "alta", 2: "media", 3: "baja"}


def error(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def create_fake_api(state=None):
    state = state if state is not None else build_state()
    app = Flask("fake_api")
    app.state = state
    B = "/api/v1"

    @app.before_request
    def log_call():
        state["calls"].append((request.method, request.path))

    def auth(role=None):
        def deco(view):
            @wraps(view)
            def wrapper(*a, **kw):
                header = request.headers.get("Authorization", "")
                if not header.startswith("Bearer token-"):
                    return error(401, "unauthorized", "Token inválido.")
                user = state["users"].get(int(header.split("-")[-1]))
                if user is None:
                    return error(401, "unauthorized", "Token inválido.")
                if role and user["role"] != role:
                    return error(403, "forbidden", "No tenés permiso para esta acción.")
                request.fake_user = user
                return view(*a, **kw)
            return wrapper
        return deco

    def row(r):
        out = dict(r)
        out["client_name"] = state["client_names"][r["client_id"]]
        out["service_name"] = state["services"][r["service_id"]]["name"]
        out["status_name"] = STATUS[r["status_id"]]
        out["priority_name"] = PRIORITY.get(r["priority_id"])
        out["priority_level"] = r["priority_id"]
        return out

    # ---- auth ----
    @app.post(f"{B}/auth/login")
    def login():
        d = request.get_json(silent=True) or {}
        missing = {k: "Es obligatorio." for k in ("email", "password") if not d.get(k)}
        if missing:
            return error(422, "validation_error", "Hay datos inválidos.", missing)
        u = next((u for u in state["users"].values() if u["email"] == d["email"]), None)
        if not u or u["password"] != d["password"]:
            return error(401, "unauthorized", "Email o contraseña incorrectos.")
        return jsonify({"token": f"token-{u['id']}", "token_type": "Bearer",
                        "user": {"id": u["id"], "email": u["email"], "role": u["role"]}})

    @app.post(f"{B}/auth/register")
    def register():
        d = request.get_json(silent=True) or {}
        errs = {}
        if not (d.get("name") or "").strip():
            errs["name"] = "Es obligatorio."
        if "@" not in (d.get("email") or ""):
            errs["email"] = "Email inválido."
        pw = d.get("password") or ""
        if len(pw) < 8:
            errs["password"] = "Debe tener al menos 8 caracteres."
        if d.get("password_confirm") != pw:
            errs["password_confirm"] = "Las contraseñas no coinciden."
        if errs:
            return error(422, "validation_error", "Hay datos inválidos.", errs)
        if any(u["email"] == d["email"] for u in state["users"].values()):
            return error(409, "duplicate_entry", "Ya existe una cuenta con ese email.",
                         {"email": "Ya existe una cuenta con ese email."})
        uid = max(state["users"]) + 1
        state["users"][uid] = {"id": uid, "email": d["email"], "role": "client", "password": pw}
        return jsonify({"message": "Cuenta creada.", "user": {"id": uid, "email": d["email"], "role": "client"}}), 201

    # ---- cliente ----
    @app.get(f"{B}/me/services")
    @auth("client")
    def my_services():
        cid = state["client_of_user"][request.fake_user["id"]]
        return jsonify([state["services"][s] for s in state["contracted"].get(cid, [])])

    @app.get(f"{B}/me/service-requests")
    @auth("client")
    def my_requests():
        cid = state["client_of_user"][request.fake_user["id"]]
        sid = request.args.get("status_id")
        if sid is not None and not sid.isdigit():
            return error(422, "validation_error", "Hay datos inválidos.", {"status_id": "Debe ser un entero."})
        rows = [row(r) for r in state["requests"] if r["client_id"] == cid
                and (sid is None or r["status_id"] == int(sid))]
        return jsonify(rows)

    @app.post(f"{B}/me/service-requests")
    @auth("client")
    def create_request():
        cid = state["client_of_user"][request.fake_user["id"]]
        d = request.get_json(silent=True) or {}
        errs = {}
        mt = d.get("modification_type")
        if not isinstance(mt, str) or not mt.strip():
            errs["modification_type"] = "Es obligatorio y debe ser texto."
        elif len(mt.strip()) > 100:
            errs["modification_type"] = "Máximo 100 caracteres."
        if errs:
            return error(422, "validation_error", "Hay datos inválidos.", errs)
        if d.get("service_id") not in state["contracted"].get(cid, []):
            return error(404, "not_found", "El cliente no tiene contratado ese servicio.")
        r = {"id": state["next_id"], "client_id": cid, "service_id": d["service_id"],
             "status_id": 1, "priority_id": None, "modification_type": mt.strip(),
             "description": d.get("description"), "rejection_reason": None,
             "created_at": datetime(2026, 11, 10, 12, 0), "resolved_at": None}
        state["next_id"] += 1
        state["requests"].append(r)
        return jsonify(row(r)), 201

    # ---- administrador ----
    @app.get(f"{B}/service-requests")
    @auth("admin")
    def admin_list():
        rows = state["requests"]
        for arg, key in (("status_id", "status_id"), ("priority_id", "priority_id")):
            v = request.args.get(arg)
            if v is not None:
                if not v.isdigit():
                    return error(422, "validation_error", "Hay datos inválidos.", {arg: "Debe ser un entero."})
                rows = [r for r in rows if r[key] == int(v)]
        rows = sorted(rows, key=lambda r: (r["priority_id"] is None, r["priority_id"] or 0, r["created_at"], r["id"]))
        return jsonify([row(r) for r in rows])

    def find(rid):
        return next((r for r in state["requests"] if r["id"] == rid), None)

    @app.get(f"{B}/service-requests/<int:rid>")
    @auth("admin")
    def admin_detail(rid):
        r = find(rid)
        return jsonify(row(r)) if r else error(404, "not_found", "La solicitud no existe.")

    @app.put(f"{B}/service-requests/<int:rid>/resolution")
    @auth("admin")
    def resolve(rid):
        d = request.get_json(silent=True) or {}
        decision = d.get("decision")
        if decision not in ("approve", "reject"):
            return error(422, "validation_error", "La decisión debe ser 'approve' o 'reject'.",
                         {"decision": "Debe ser 'approve' o 'reject'."})
        reason = (d.get("rejection_reason") or "").strip() if decision == "reject" else None
        if decision == "reject" and not reason:
            return error(422, "validation_error", "El motivo del rechazo es obligatorio.",
                         {"rejection_reason": "El motivo del rechazo es obligatorio."})
        r = find(rid)
        if r is None:
            return error(404, "not_found", "La solicitud no existe.")
        if r["status_id"] != 1:
            return error(409, "conflict", "La solicitud ya no está pendiente.")
        r["status_id"] = 5 if decision == "approve" else 4
        r["rejection_reason"] = reason
        r["resolved_at"] = datetime(2026, 11, 10, 15, 30)
        return jsonify(row(r))

    @app.errorhandler(404)
    def nf(_):
        return error(404, "not_found", "El recurso no existe.")

    return app


def add_request(state, client_id=7, service_id=3, status_id=1, priority_id=None, **extra):
    """Atajo para que los tests carguen solicitudes ya armadas."""
    r = {"id": state["next_id"], "client_id": client_id, "service_id": service_id,
         "status_id": status_id, "priority_id": priority_id, "modification_type": "Cambio de horario",
         "description": "Mover la reunión al viernes", "rejection_reason": None,
         "created_at": datetime(2026, 10, 31, 10, 0), "resolved_at": None}
    r.update(extra)
    state["next_id"] += 1
    state["requests"].append(r)
    return r


if __name__ == "__main__":  # python -m tests.fake_api  -> API falso en el puerto 5000 (para ver el front)
    fake = create_fake_api()
    add_request(fake.state, priority_id=1)
    add_request(fake.state, priority_id=2, modification_type="Ampliar alcance", description=None)
    add_request(fake.state, status_id=4, rejection_reason="Servicio fuera del plan",
                resolved_at=datetime(2026, 11, 1, 9, 30), modification_type="Cambio de logo")
    add_request(fake.state, status_id=5, resolved_at=datetime(2026, 11, 2, 11, 0),
                priority_id=3, modification_type="Actualizar banner")
    fake.run(port=5000)
