# Arquitectura del Frontend — Consultora Tech Solutions

Frontend hecho con **Flask + plantillas Jinja + Bootstrap**. Es una aplicación **independiente del API**:
no toca la base de datos; solo le habla al API por HTTP.

```
 Navegador ──HTML──▶  FRONT (Flask, :5001)  ──JSON + Bearer token──▶  API (Flask, :5000)  ──SQL──▶  MySQL
           ◀──HTML──                         ◀──JSON──
```

## 1. Cómo correrlo

Hacen falta **dos terminales**, una para el API y otra para el front.

```bash
# Terminal 1 — API (ver api/ARQUITECTURA.md)
cd api && python run.py                      # http://localhost:5000

# Terminal 2 — Frontend
cd frontend
python -m venv venv && venv\Scripts\activate   # Windows (en Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env                         # y editar SECRET_KEY
python run.py                                  # http://localhost:5001
```

Tests (no necesitan el API ni MySQL): `python -m pytest -q`

Para ver el front **sin** el API real, existe un API de mentira con datos de ejemplo:
`python -m tests.fake_api` (queda en el puerto 5000; usuarios `admin@test.com` / `cliente@test.com`, contraseña `Clave-de-prueba-1`).

## 2. Estructura

```
frontend/
├── run.py                    punto de entrada (puerto 5001)
├── requirements.txt          Flask, requests, python-dotenv, pytest
├── .env.example              API_BASE_URL, SECRET_KEY, API_TIMEOUT
├── app/
│   ├── __init__.py           create_app(): CSRF, manejo central de errores, filtro de fechas
│   ├── config.py             configuración (todo por variables de entorno)
│   ├── constants.py          IDs de estados/prioridades/roles (iguales a los del API)
│   ├── api_client.py         ÚNICO módulo que habla con el API
│   ├── auth.py               sesión + decoradores de permisos de página
│   ├── helpers.py            utilidades chicas (optional_int)
│   ├── routes/               una "vista" por pantalla, agrupadas en Blueprints
│   │   ├── main.py           "/" → redirige según el rol
│   │   ├── auth.py           /login  /register  /logout
│   │   ├── client.py         /services  /requests/new  /requests
│   │   └── admin.py          /admin/requests  /admin/requests/<id>  …/resolution
│   ├── templates/            HTML (Jinja): base.html, _macros.html, login, register, client/, admin/
│   └── static/               css/styles.css, js/resolve.js, vendor/ (Bootstrap 5.3.3 local)
└── tests/                    fake_api.py (API en memoria) + 60 tests
```

## 3. Cómo viaja un pedido (ejemplo: el cliente abre "Mis solicitudes")

1. El navegador pide `GET /requests`.
2. `routes/client.py` → el decorador `@client_required` (en `auth.py`) verifica que haya sesión y que el rol sea `client`.
3. La vista llama a `api_client.my_requests(token)`.
4. `api_client` hace `GET {API_BASE_URL}/me/service-requests` con `Authorization: Bearer <token>`.
5. El API valida el token, busca el cliente **a partir del token** (nunca de la URL) y devuelve el JSON.
6. La vista pasa la lista a `templates/client/requests.html`, que arma el HTML. Jinja **escapa** todo el texto (anti-XSS).

Las vistas no saben nada de HTTP ni de URLs del API: eso está solo en `api_client.py`. Si el API cambia una ruta, se toca un archivo.

## 4. Decisiones de diseño (y por qué)

| Decisión | Motivo |
|---|---|
| **Renderizado en el servidor** (Jinja) y no una SPA con `fetch` en JavaScript | Es el uso natural de Flask, el token nunca llega al JavaScript del navegador y hay mucho menos código que mantener. |
| **El token del API vive en la sesión de Flask** (cookie firmada, `HttpOnly`, `SameSite=Lax`) | JavaScript no puede leerla (frena el robo por XSS) y el navegador no la manda en POST que vienen de otros sitios. Limitación: la cookie va *firmada*, no *cifrada*: el usuario puede leer su propio token, pero no modificarlo. |
| **CSRF propio y simple**: cada formulario POST lleva un código secreto guardado en la sesión | Evita que otra página haga enviar un formulario con tu sesión (ej.: aprobar una solicitud sin que el admin lo sepa). Se verifica en `before_request`. |
| **Logout por POST** | Para que un link o imagen ajena no pueda cerrar la sesión con un GET. |
| **El front no decide permisos "de verdad"** | `@admin_required` solo evita mostrar páginas que no corresponden. La seguridad real es del API, que responde 403. Hay un test que lo prueba falseando el rol en la sesión. |
| **Comparar por ID, no por nombre** (`STATUS_PENDING = 1`) | Igual que en el API y el SQL: el nombre puede cambiar, el ID no. |
| **Los filtros inválidos se ignoran** (`?status_id=hola` → sin filtro) | La URL la puede escribir cualquiera; nunca debe romper la pantalla. |
| **Bootstrap local (`static/vendor`)** | Funciona sin internet y sin depender de un CDN. |

## 5. Manejo de errores (un solo lugar: `app/__init__.py`)

| Qué pasa | Qué ve la persona |
|---|---|
| El API responde **401** (token vencido o inválido) | Se limpia la sesión y vuelve al login con el aviso "Tu sesión venció". |
| El API responde **403** | Página "Sin permiso". *No se redirige*: un redirect podía formar un bucle infinito si el rol guardado en la sesión no coincidía con el real (lo encontró un test). |
| **404** | Página "No encontrado". |
| **422** (datos inválidos) | La vista lo atrapa y **vuelve a mostrar el formulario** con el error junto a cada campo, conservando lo escrito (nunca las contraseñas). |
| **409** (conflicto, ej. solicitud ya resuelta) | Aviso amarillo y vuelve a la pantalla. |
| API apagado / lento (sin respuesta) | Página 503 amable, **sin** mostrar IPs ni detalles técnicos (quedan en el log). |
| Respuesta rara del API (no JSON) | Página "Algo salió mal". |

## 6. Pantallas y casos de uso

| Pantalla | Ruta | Rol | Historia de usuario |
|---|---|---|---|
| Iniciar sesión | `/login` | público | US16 |
| Crear cuenta | `/register` | público | US17 |
| Mis servicios | `/services` | cliente | US01 |
| Nueva solicitud | `/requests/new` | cliente | US02 |
| Mis solicitudes (estado + motivo de rechazo, filtro por estado) | `/requests` | cliente | US05 / US14 |
| Bandeja (filtros por estado y prioridad; orden por urgencia) | `/admin/requests` | admin | US14 |
| Detalle y resolución (aprobar / rechazar con motivo) | `/admin/requests/<id>` | admin | US09 |

## 7. Contrato con el API (lo que el front da por cierto)

Si alguno de estos puntos cambia en el API, hay que actualizar `api_client.py` y `tests/fake_api.py`.

* Login → `{token, token_type, user:{id,email,role}}`. Errores: `{"error":{"code","message","details?"}}`.
* Registro → `name, email, phone?, dni?, password, password_confirm`. El rol siempre es `client`.
* `GET /me/services`, `GET|POST /me/service-requests`, `GET /service-requests[/<id>]`, `PUT /service-requests/<id>/resolution` con `{decision: approve|reject, rejection_reason?}`.
* **Fechas**: el API las manda como `Sat, 31 Oct 2026 10:00:00 GMT` pero son la hora local del servidor, sin convertir. El filtro `fecha` las muestra tal cual, **sin** corrimiento de zona horaria. Si el API pasa a ISO 8601, el filtro ya lo soporta.

## 8. Pruebas

* **60 tests** con `pytest` (sin MySQL ni API): el `requests.Session` se reemplaza por un adaptador que llama al API falso en memoria (`tests/fake_api.py`), que respeta rutas, roles y formato de error.
* Cubren: login por rol, sesión (token sin contraseña, cookie `HttpOnly`), CSRF, permisos por rol, token vencido, rol falseado, API caído, registro y validaciones, XSS, filtros, resolución (aprobar/rechazar/conflicto) y orden de la bandeja.
* Se comprobó que los tests **fallan** si se rompe a propósito el CSRF o el chequeo de rol.
* Además se corrió el front contra el **código real del API** (con los repositorios en memoria) y las 18 verificaciones dieron OK.
* Revisión visual con Chromium en escritorio y celular (390 px): sin scroll horizontal; en celular, "Mis solicitudes" pasa de tabla a tarjetas.
* **Pendiente:** correrlo contra el API con MySQL real, con datos del script SQL.

## 9. Cómo agregar una pantalla nueva

1. Si necesita datos del API: una función en `api_client.py` (una línea de `_send`).
2. Una vista en el Blueprint que corresponda en `routes/`, con `@client_required` o `@admin_required`.
3. Una plantilla en `templates/` que extienda `base.html` (y use `_macros.html` para badges y campos).
4. Si hay un formulario: `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` y, en la vista, atrapar `ApiError` con `status == 422` para volver a mostrarlo con `err.details`.
5. Agregar el endpoint al `fake_api.py` y tests en `tests/`.

## 10. Pendientes / próximos pasos

* Pantalla de **reclamos** (US04, el API ya tiene `POST /me/claims`).
* Pantallas de administración de **planes y clientes** (US06, US07, US08).
* **Notificaciones** del cliente (el API las crea al resolver una solicitud; falta un endpoint para listarlas).
* El front y el `app.py` de la raíz del repo (demo) son apps distintas: conviene acordar con el grupo cuál queda como punto de entrada.
* Para producción: `SECRET_KEY` real, `SESSION_COOKIE_SECURE=1` (HTTPS) y un servidor WSGI (gunicorn/waitress) en lugar de `app.run`.
