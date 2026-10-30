# Arquitectura de la API — Consultora Tech Solutions

Documento vivo: se actualiza a medida que el proyecto avanza.
Stack: **Python + Flask**, **MySQL** (acceso con **PyMySQL**), frontend HTML/CSS/JS aparte.
Fuente de verdad de la base: [`database/migrations/1_setup_database.sql`](../database/migrations/1_setup_database.sql) y [`documentacion/base_datos/base_datos.md`](../documentacion/base_datos/base_datos.md).

---

## 1. Idea general: tres capas

Flask no impone ninguna estructura, así que la definimos nosotros. Cada pedido pasa por tres capas y **cada capa tiene una sola responsabilidad**:

```
 Frontend (fetch)
      │  HTTP + JSON
      ▼
┌───────────────┐
│  RUTAS        │  app/api/            Recibe el pedido, llama al service, devuelve la respuesta HTTP.
├───────────────┤
│  SERVICES     │  app/services/       Reglas de negocio y validaciones. No sabe de HTTP ni de SQL.
├───────────────┤
│  REPOSITORIOS │  app/repositories/   Único lugar donde se escribe SQL.
└───────┬───────┘
        ▼
     MySQL
```

**Regla para saber dónde va cada cosa:**

| Si el código... | va en... |
|---|---|
| usa `request`, `jsonify` o decide el código HTTP | rutas |
| valida datos, decide "si no existe → 404", combina varias operaciones | services |
| tiene un `SELECT`, `INSERT`, `UPDATE` o `DELETE` | repositorios |

**Por qué así:** si cambia una tabla se toca un archivo (el repositorio); si cambia una regla, el service; si cambia una URL, la ruta. Además el service se puede probar sin servidor ni base de datos (sección 7), y varios integrantes pueden trabajar a la vez sin pisarse, porque cada recurso tiene sus propios archivos.

## 2. Estructura de carpetas

```
api/
├── run.py                     Punto de entrada (python run.py)
├── requirements.txt           Dependencias
├── .env.example               Plantilla de configuración (copiar a .env)
├── ARQUITECTURA.md            Este documento
├── app/
│   ├── __init__.py            create_app(): arma la aplicación (patrón "application factory")
│   ├── config.py              Configuración leída de variables de entorno
│   ├── constants.py           IDs fijos de los catálogos (estados, prioridades) y roles
│   ├── db.py                  Conexión a MySQL: una por pedido, commit/rollback automático
│   ├── errors.py              Errores propios + formato único de respuesta de error
│   ├── security.py            Contraseñas, token de sesión y decoradores de permisos
│   ├── validators.py          Validaciones del alta de cliente (US17)
│   ├── api/                   CAPA DE RUTAS
│   │   ├── __init__.py        Blueprint /api/v1 y registro de recursos
│   │   ├── _helpers.py        json_body() y otras utilidades de rutas
│   │   ├── health.py          GET /api/v1/health
│   │   ├── auth.py            POST /auth/login · POST /auth/register · GET /auth/me   (US16/US17)
│   │   └── plans.py           CRUD de planes (ejemplo de referencia)   (US07)
│   ├── services/              CAPA DE NEGOCIO
│   │   ├── auth_service.py
│   │   └── plans_service.py
│   └── repositories/          CAPA DE DATOS (SQL)
│       ├── users_repository.py
│       ├── clients_repository.py
│       └── plans_repository.py
├── scripts/
│   └── create_user.py         Crea un admin o cliente de prueba (la tabla users arranca vacía)
└── tests/
    ├── conftest.py            Repositorios falsos en memoria + logins de prueba
    ├── test_auth.py
    ├── test_register.py
    └── test_plans.py
```

Convención de nombres: un recurso = tres archivos con el mismo nombre base (`clients.py`, `clients_service.py`, `clients_repository.py`).

## 3. Cómo viaja un pedido (ejemplo: `POST /api/v1/plans`)

1. `app/api/plans.py → create_plan()`: antes de entrar, `@role_required("admin")` lee el header `Authorization`, verifica el token y el rol. Si falla, responde 401 o 403 y la función ni se ejecuta.
2. Lee el JSON del cuerpo y llama a `plans_service.create_plan(data)`.
3. El service valida (`name` obligatorio y ≤ 100 caracteres, `price ≥ 0`). Si algo está mal, lanza `ValidationError`.
4. Si está bien, llama a `plans_repository.create(data)`, que ejecuta el `INSERT`.
5. El service vuelve a leer el plan creado y lo devuelve; la ruta responde `201` con el plan en JSON.
6. Al terminar el pedido, `db.close_db()` hace **commit** (o **rollback** si hubo una excepción) y cierra la conexión.

## 4. Convenciones de la API

**Idioma:** URLs y campos JSON **en inglés y `snake_case`, idénticos a las tablas y columnas del script SQL** (`/plans`, `name`, `price`, `client_id`). Es la decisión de la base ("esquema en inglés, datos en español"): así el nombre es el mismo en SQL, API y frontend, y no hay que traducir en ningún lado. Los *valores* que ve el usuario siguen en español (ej. el estado `pendiente`).

**URLs**
- Prefijo `/api/v1`. Recursos en plural: `/plans`, `/clients`, `/service-requests`.
- Un recurso en particular: `/plans/3`. Un sub-recurso: `/service-requests/7/attachments`.
- `/me/...` = "lo mío": recursos del usuario logueado. El id sale del token, no de la URL, así un cliente no puede pedir datos de otro cambiando un número.

**Métodos y códigos HTTP**

| Acción | Método | Éxito |
|---|---|---|
| Listar | `GET /recurso` | 200 |
| Ver uno | `GET /recurso/{id}` | 200 |
| Crear | `POST /recurso` | 201 + el objeto creado |
| Modificar | `PUT /recurso/{id}` (acepta campos parciales) | 200 + el objeto actualizado |
| Borrar | `DELETE /recurso/{id}` | 204 sin cuerpo |

**Autenticación** — el login devuelve un token y el frontend lo manda en cada pedido:

```
POST /api/v1/auth/login   {"email": "...", "password": "..."}
  →  200 {"token": "...", "token_type": "Bearer", "user": {"id": 1, "email": "...", "role": "admin"}}

GET /api/v1/plans
Authorization: Bearer <token>
```

- Los tokens están firmados con `SECRET_KEY` y vencen a las 8 horas. Nadie puede fabricar o modificar uno sin esa clave.
- Las contraseñas se guardan **hasheadas** (`pbkdf2:sha256`), nunca en texto plano.
- Un login fallido responde siempre el mismo mensaje, sea el email o la contraseña lo incorrecto (lo exige US16).
- Para proteger una ruta: `@login_required` (cualquier usuario) o `@role_required("admin")` (solo ese rol), debajo del `@bp.get(...)`.
- Limitación conocida: el rol viaja dentro del token; si se desactiva una cuenta o se le cambia el rol, el token viejo sigue valiendo hasta que venza.

**Errores** — siempre el mismo formato, así el frontend los lee de una sola manera:

```json
{ "error": { "code": "validation_error", "message": "Hay datos inválidos.",
             "details": { "price": "Es obligatorio y debe ser un número mayor o igual a 0." } } }
```

| HTTP | `code` | Cuándo |
|---|---|---|
| 401 | `unauthorized` | Falta el token, es inválido, venció, o el login es incorrecto |
| 403 | `forbidden` | Está logueado pero su rol no alcanza |
| 404 | `not_found` | El recurso no existe |
| 405 | `method_not_allowed` | Método no permitido en esa ruta |
| 409 | `duplicate_entry` | Choca con un valor único (ej. nombre de plan o email repetido) |
| 409 | `in_use` | No se puede borrar: hay registros que dependen de este |
| 409 | `invalid_reference` | Referencia algo que no existe (ej. un servicio que el cliente no contrató) |
| 422 | `validation_error` | Datos faltantes o inválidos (`details` dice cuáles) |
| 503 | `db_unavailable` | MySQL no responde |
| 500 | `internal_error` | Error no previsto (se registra en el log) |

Los services **lanzan** `ValidationError`, `NotFoundError`, `ConflictError`, `UnauthorizedError` o `ForbiddenError` (de `app/errors.py`); nunca arman la respuesta HTTP a mano. Los errores de MySQL (clave duplicada, FK) se traducen solos a 409.

**Otras reglas**
- En el código, comparar estados por **ID** (`STATUS_PENDING` de `app/constants.py`), nunca por nombre: los IDs son estables, los nombres pueden cambiar.
- Consultas **siempre parametrizadas** (`%s` + valores). Jamás armar SQL concatenando texto del usuario.
- Contraseñas, `SECRET_KEY` y datos de la base **solo en `.env`** (está en `.gitignore`).
- CORS: solo se aceptan pedidos de los orígenes listados en `CORS_ORIGINS`.

## 5. Cómo agregar un recurso nuevo (receta para el equipo)

Ejemplo con `services`:

1. **Repositorio** — copiar `plans_repository.py` a `services_repository.py`. Cambiar `TABLE`, `SELECT_COLUMNS` y `EDITABLE_COLUMNS` según la tabla en el script SQL.
2. **Service** — copiar `plans_service.py` a `services_service.py`. Ajustar `_validate()` a los campos y largos del recurso, y el import del repositorio.
3. **Ruta** — copiar `plans.py` a `services.py`. Cambiar el nombre del Blueprint, `url_prefix` y el service. Decidir qué decorador lleva cada ruta (`@login_required` / `@role_required(...)`).
4. **Registrar** — en `app/api/__init__.py` agregar el módulo al `import` y un `api_bp.register_blueprint(...)`.
5. **Test** — copiar `tests/test_plans.py`, adaptarlo, y sumar el repositorio falso en `conftest.py`.
6. Correr `python -m pytest` antes de subir cambios.

Si una historia necesita varias tablas o reglas especiales (ej. cambio de plan que valida identidad con VeriCheck y luego avisa por NotiSys), esa lógica va **en el service**, que puede llamar a varios repositorios.

## 6. Mapa de user stories → endpoints (propuesta a acordar con el grupo)

Estado: ✅ hecho · 🔲 pendiente · ❓ requiere decisión (sección 8). Las consultas SQL de referencia están en `base_datos.md`, sección 7.

### Sprint 1 — Demo MVP (US24)

| US | Historia | Endpoint | Rol | Estado |
|---|---|---|---|---|
| US16 | Iniciar sesión | `POST /auth/login`, `GET /auth/me` | público / logueado | ✅ backend (falta pantalla) |
| US17 | Registrar un nuevo usuario | `POST /auth/register` · body `{name, email, password, password_confirm, phone?, dni?}` · asigna el plan Gratuito (id 4) · no devuelve token | público | ✅ backend (falta pantalla) |
| US01 | Consultar servicios contratados | `GET /me/services` | client | 🔲 |
| US02 | Solicitar modificación de servicio | `POST /service-requests` · body `{service_id, modification_type, description?}` · el `client_id` sale del token | client | 🔲 |
| US14 | Consultar solicitudes y estados | `GET /service-requests?status_id=` (bandeja del admin) · `GET /me/service-requests` (las del cliente, cubre US05) | admin / client | 🔲 |
| US09 | Atender solicitud | `PUT /service-requests/{id}/resolution` · body `{decision: "approve"\|"reject", rejection_reason}` | admin | 🔲 |

Reglas de US09 para el Sprint 1 (según `base_datos.md` 5.1): solo se atiende una solicitud en estado `pendiente`; aprobar → `realizado` (5); rechazar → `rechazado` (4) y el motivo es obligatorio (422 si falta); se guardan `administrator_id` y `resolved_at`. Atender una que ya no está pendiente → 409.

### Después del Sprint 1

| US | Historia | Endpoint propuesto | Estado |
|---|---|---|---|
| US07 | Gestionar planes | `/plans` CRUD | ✅ (ejemplo de referencia) |
| US06 | Gestionar clientes | `/clients` CRUD | 🔲 |
| US08 | Gestionar servicios | `/services` CRUD | 🔲 |
| US03 | Adjuntar documentación | `POST /service-requests/{id}/attachments` | ❓ ver 8.2-d |
| US04 | Realizar un reclamo | `POST /claims` | 🔲 |
| US13 | Solicitar cambio de plan | `POST /plan-change-requests` | 🔲 |
| US18 | Validar identidad del cliente | interno (VeriCheck), lo usa el service de US13 | 🔲 |
| US19 | Aprobar o rechazar cambio de plan | `PUT /plan-change-requests/{id}/resolution` | 🔲 |
| US10 | Asignar prioridad | `PUT /service-requests/{id}/priority` | 🔲 |
| US11/US12 | Notificar nueva solicitud / cambio de estado | `GET /me/notifications`, `PUT /me/notifications/read` (bandeja interna) | 🔲 |
| US21 | Integrar notificaciones con NotiSys | cliente HTTP en `app/integrations/` | 🔲 |
| US15 | Consultar info del cliente vía API | `GET /clients/{id}` para sistema externo | ❓ ver 8.2-b |
| US20 | Enviar facturación a PagoNet | interno, al aprobar un cambio de plan | 🔲 |
| US22 | Enviar métricas a AnalytixPro | tarea diaria programada | 🔲 |
| US23 | Auditoría de integraciones | se escribe en `integration_audit_logs` desde cada integración | 🔲 |

**Crecimiento previsto:** las integraciones externas (VeriCheck, PagoNet, NotiSys, AnalytixPro, CRMMax) van en una cuarta carpeta `app/integrations/`, con un archivo por sistema. Los services las usan igual que a un repositorio, y cada llamada se anota en `integration_audit_logs`. Así, si una integración cambia, no se toca la lógica de negocio.

## 7. Cómo probarlo

**1. Crear la base** — correr `database/migrations/1_setup_database.sql` completo en DBeaver (Alt+X) y revisar el log final.

**2. Levantar la API** (desde la carpeta `api/`)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
```
Completar en `.env` al menos `DB_PASSWORD` y `SECRET_KEY`. Después:
```bash
python run.py
```
Probar en el navegador: <http://localhost:5000/api/v1/health> → `{"status":"ok"}`

**3. Crear un usuario para entrar** (la tabla `users` arranca vacía)
```bash
python -m scripts.create_user --email admin@techsolutions.com --password MiClave123 --role admin --name "Samantha"
python -m scripts.create_user --email cliente@ejemplo.com --password MiClave123 --role client --name "Mariana" --plan-id 1
```

**4. Crear una cuenta desde la API (US17)**
```bash
curl -X POST localhost:5000/api/v1/auth/register -H "Content-Type: application/json" -d '{"name":"Mariana Diaz","email":"mariana@ejemplo.com","password":"ClaveSegura123","password_confirm":"ClaveSegura123","phone":"+5491122223333","dni":"28456321"}'
```
Responde `201` con el usuario, el cliente y su plan (Gratuito). No devuelve token: hay que iniciar sesión.

**5. Iniciar sesión y consultar** (con Thunder Client, Postman, o curl):
```bash
curl -X POST localhost:5000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"admin@techsolutions.com","password":"MiClave123"}'
curl localhost:5000/api/v1/plans -H "Authorization: Bearer <el token que devolvió el login>"
```
Debería devolver los 4 planes cargados por el script (Básico, Profesional, Premium y Gratuito).

**Tests automáticos** (no necesitan MySQL):
```bash
python -m pytest
```
Funcionan porque `tests/conftest.py` reemplaza los repositorios por versiones en memoria. Es la ventaja concreta de separar en capas.

> **Qué está verificado:** 68 tests automáticos con repositorios en memoria. Además, el registro (US17) se probó contra el MySQL real: alta con `201`, email/DNI duplicado con `409`, login posterior con `200` y rollback de la transacción cuando falla el segundo `INSERT` (sin dejar usuarios huérfanos).

## 8. Decisiones y puntos abiertos

### 8.1 Resuelto por el script SQL (antes eran dudas de la API)

| Duda | Cómo quedó |
|---|---|
| Nombres de tablas y columnas | Inglés, definidos en el script. El repositorio ya los usa. |
| Login y registro (US16/US17) | Tabla `users` (`email`, `password_hash`, `role`, `is_active`). Los perfiles viven en `clients` y `administrators`, enlazados por `user_id`. |
| Relación N:N Cliente–Servicio | Tabla `client_services`; es la que usa US01. |
| Solicitud con `client_id` | Existe, con FK compuesta `(client_id, service_id)`: un cliente solo puede pedir cambios sobre un servicio que contrató. |
| Auditoría de integraciones (US23) | Tabla `integration_audit_logs`. |
| Documentación adjunta | Tabla `attachments` (guarda `file_path`, `file_type`). |

### 8.2 Pendientes que afectan a la API

a. **`clients.plan_id` es `NOT NULL`** → resuelto con el plan **Gratuito (id 4)**, que el script SQL carga con precio `0.00`. Al registrarse, el cliente nace con ese plan y sin servicios contratados. La constante vive en `constants.py` (`DEFAULT_PLAN_ID`).
b. **US15 (sistema externo)** no tiene tabla de credenciales. Opción simple: una API key fija en `.env` que el sistema externo manda en un header.
c. **Idioma de los estados:** `request_statuses` está en español y `claims.status`/`category` en inglés. El frontend va a recibir ambos; hay que unificar o mapear.
d. **Archivos adjuntos (US03):** el script guarda la ruta, pero falta decidir dónde se guardan los archivos (carpeta `uploads/` fuera de git), formatos y tamaño máximo.
e. **`invoices` vs. el parcial:** el parcial dice que la factura no se persiste y la tabla existe. Decidir una versión (ya figura en `base_datos.md`).
f. **Dónde vive la API en el repo:** esta carpeta se pensó como `api/`. El `app.py` de demo de la raíz se puede borrar cuando se integre.
g. **Verificación de email:** `users` no tiene columna para eso, así que la cuenta queda activa apenas se registra. Si se quiere exigir confirmación, hay que agregar `email_verified_at` al script.

### 8.3 Decisiones tomadas en la API

| Decisión | Motivo |
|---|---|
| 3 capas (rutas / services / repositorios) | Una responsabilidad por capa, testeable sin base de datos |
| PyMySQL con SQL directo (sin ORM) | El script SQL es la única fuente de verdad; es lo que se vio en Base de Datos III; menos piezas |
| Token firmado (`itsdangerous`) en el header `Authorization` | Funciona con el frontend en otro origen, sin sumar dependencias |
| URLs y JSON en inglés, igual que las columnas | Un solo nombre para cada cosa en SQL, API y frontend |
| IDs de catálogo como constantes en `constants.py` | La base los fija; el código no consulta la tabla para saber qué es "pendiente" |
| Plan Gratuito (id 4) por defecto al registrarse | `clients.plan_id` es `NOT NULL`; el visitante arranca con un plan real, sin servicios y sin facturación |
| El registro no devuelve token | Se obliga a pasar por el login: una sola forma de iniciar sesión y menos código duplicado |
| `db.transaction()` para flujos de varios `INSERT` | El commit del teardown también corre cuando un errorhandler atrapa la excepción; sin rollback explícito quedarían filas a medias |

## 9. Registro de cambios

| Fecha | Cambio |
|---|---|
| 2026-10-29 | Estructura base en 3 capas, manejo de errores, conexión MySQL, CORS, recurso de ejemplo con tests. |
| 2026-10-29 | Adaptado al script SQL real (tablas en inglés). Autenticación: login, token firmado, roles, `create_user`. Mapa de endpoints ordenado por Sprint 1. 26 tests. |
| 2026-10-29 | US17 implementada: `POST /auth/register` con validaciones, plan Gratuito por defecto y transacción explícita. 68 tests. |
