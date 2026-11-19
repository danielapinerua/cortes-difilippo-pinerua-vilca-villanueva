# Tech Solutions — Guía para levantar el proyecto completo

Sistema de gestión para una consultora: clientes, servicios contratados, solicitudes de modificación y resolución por parte de los administradores.

El proyecto se compone de **tres procesos independientes** que tienen que estar corriendo a la vez:

```text
Navegador
   │  HTML
   ▼
FRONTEND (Flask)  http://localhost:5001
   │  JSON + Bearer token
   ▼
API (Flask)  http://localhost:5000
   │  SQL
   ▼
MySQL  :3306
```

- El **frontend no accede a la base de datos**: solo le habla a la API por HTTP.
- La **API** concentra las reglas de negocio y el acceso a MySQL.
- La **base de datos** se crea y se carga con un único script SQL.

> **Resumen rápido:** WAMP encendido → importar el SQL → `python run.py` en `api/` → `python run.py` en `frontend/` → abrir http://localhost:5001

---

## Índice

1. [Qué es este proyecto](#1-qué-es-este-proyecto)
2. [Arquitectura](#2-arquitectura)
3. [Stack y dependencias](#3-stack-y-dependencias)
4. [Requisitos previos](#4-requisitos-previos)
5. [Estructura del repositorio](#5-estructura-del-repositorio)
6. [Puesta en marcha](#6-puesta-en-marcha)
   - [Paso 1 — Base de datos](#paso-1--base-de-datos-mysql)
   - [Paso 2 — API](#paso-2--api-puerto-5000)
   - [Paso 3 — Frontend](#paso-3--frontend-puerto-5001)
   - [Paso 4 — Ingresar al sistema](#paso-4--ingresar-al-sistema)
7. [Verificación rápida](#7-verificación-rápida)
8. [Usuarios de prueba y recorrido para la demo](#8-usuarios-de-prueba-y-recorrido-para-la-demo)
9. [Tests automáticos](#9-tests-automáticos)
10. [Alternativa sin MySQL: API falsa](#10-alternativa-sin-mysql-api-falsa)
11. [Problemas frecuentes](#11-problemas-frecuentes)
12. [Reiniciar todo o resetear la base](#12-reiniciar-todo-o-resetear-la-base)
13. [Notas de seguridad](#13-notas-de-seguridad)
14. [Documentación relacionada](#14-documentación-relacionada)

---

## 1. Qué es este proyecto

Tech Solutions es un sistema para administrar los servicios de una consultora:

- Un **cliente** inicia sesión, ve los servicios que tiene contratados y crea solicitudes de modificación.
- Un **administrador** ve una bandeja con todas las solicitudes, las filtra por estado y prioridad, y las resuelve (aprobar o rechazar con un motivo).
- El cliente puede consultar el estado y el motivo de rechazo de cada solicitud.

El proyecto está dividido en dos aplicaciones Flask independientes (`api/` y `frontend/`) más la base de datos MySQL (`database/`).

> ⚠️ El archivo `app.py` de la raíz es una **demo vieja** (`"Demo Tech Solutions"`). No forma parte del sistema y **no se usa** para levantarlo.

---

## 2. Arquitectura

```
 Navegador ──HTML──▶ FRONTEND (Flask, :5001) ──JSON + Bearer token──▶ API (Flask, :5000) ──SQL──▶ MySQL (:3306)
           ◀──HTML──                        ◀──JSON──
```

### API: tres capas

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Rutas | `api/app/api/` | Recibe el pedido HTTP, valida permisos y devuelve la respuesta |
| Services | `api/app/services/` | Reglas de negocio y validaciones |
| Repositorios | `api/app/repositories/` | Único lugar donde se escribe SQL |

### Frontend: renderizado en el servidor

- Usa **Flask + plantillas Jinja + Bootstrap 5.3.3** (incluido localmente, sin CDN).
- El token del API se guarda en una **cookie de sesión firmada** (`HttpOnly`), nunca en JavaScript.
- Los formularios usan **CSRF token** propio.

---

## 3. Stack y dependencias

| Componente | Tecnología | Dependencias principales |
|---|---|---|
| Base de datos | MySQL 8.0.16+ / MariaDB 10.2+ | Script `database/migrations/1_setup_database.sql` |
| API | Python + Flask | Flask, PyMySQL, flask-cors, python-dotenv, pytest |
| Frontend | Python + Flask + Jinja2 + Bootstrap 5.3.3 | Flask, requests, python-dotenv, pytest |
| Entorno local | WAMP | MySQL en el puerto 3306 (MariaDB opcional en 3307) |

Versiones declaradas en los `requirements.txt`:

**`api/requirements.txt`**

```text
Flask>=3.0
PyMySQL>=1.1
flask-cors>=4.0
python-dotenv>=1.0
pytest>=8.0
```

**`frontend/requirements.txt`**

```text
Flask>=3.0,<4
requests>=2.31,<3
python-dotenv>=1.0,<2
pytest>=8.0,<9
```

---

## 4. Requisitos previos

- **Windows** con PowerShell (los comandos de esta guía están escritos para PowerShell).
- **Python 3.10 o superior** (en la PC de desarrollo se usó Python 3.15).
- **WAMP** instalado (incluye MySQL y phpMyAdmin).
- **Git** (opcional, solo para clonar el repositorio).
- Puertos libres: **3306** (MySQL), **5000** (API) y **5001** (frontend).

> En Linux/Mac, reemplazá `.\venv\Scripts\Activate.ps1` por `source venv/bin/activate` y `Copy-Item` por `cp`. El resto de los comandos es igual.

---

## 5. Estructura del repositorio

```text
.
├── api/                                  Backend Flask (puerto 5000)
│   ├── app/
│   │   ├── api/                          Rutas HTTP
│   │   ├── services/                     Reglas de negocio
│   │   ├── repositories/                 Consultas SQL
│   │   ├── config.py                     Configuración desde variables de entorno
│   │   └── db.py                         Conexión a MySQL
│   ├── scripts/create_user.py            Crea usuarios de prueba (opcional)
│   ├── tests/
│   ├── .env.example                      Plantilla de configuración
│   ├── ARQUITECTURA.md                   Documentación técnica de la API
│   ├── requirements.txt
│   └── run.py                            Punto de entrada de la API
│
├── frontend/                             Interfaz web Flask + Jinja (puerto 5001)
│   ├── app/
│   │   ├── routes/                       Vistas por pantalla
│   │   ├── templates/                    HTML con Jinja
│   │   ├── static/                       CSS, JS y Bootstrap local
│   │   └── api_client.py                 Único módulo que habla con la API
│   ├── tests/
│   ├── .env.example
│   ├── ARQUITECTURA_FRONT.md             Documentación técnica del frontend
│   ├── requirements.txt
│   └── run.py                            Punto de entrada del frontend
│
├── database/migrations/1_setup_database.sql   Crea la base, tablas y datos demo
├── documentacion/                        Documentación académica del proyecto
├── app.py                                Demo antigua (no se usa)
└── README.md                             Este archivo
```

---

## 6. Puesta en marcha

Todos los comandos se ejecutan **desde la raíz del repositorio** salvo que se indique otra cosa. Abrí una terminal en la carpeta del proyecto:

```powershell
cd <ruta-donde-clonaste-el-repo>
```

Vas a necesitar **dos terminales** (una para la API y otra para el frontend) y **WAMP** corriendo en segundo plano.

### Paso 1 — Base de datos (MySQL)

**Qué hace este paso:** enciende MySQL, crea la base `tech_solutions`, todas las tablas, los catálogos (planes, estados, prioridades, servicios) y los usuarios/datos de demostración.

#### 1.1 Iniciar MySQL

- Abrí **WAMP** y hacé clic en el ícono de la bandeja del sistema → **Start All Services**. El ícono tiene que quedar **verde**.
- Alternativa por consola (PowerShell **como administrador**):

```powershell
net start wampmysqld64
```

> Si el servicio ya estaba corriendo, el comando avisa que no se puede iniciar dos veces. No es un error.

#### 1.2 Importar el script SQL

1. Abrí **phpMyAdmin**: http://localhost/phpmyadmin
2. Ingresá con:
   - **Usuario:** `root`
   - **Contraseña:** vacía (configuración por defecto de WAMP)
3. Pestaña **Importar**.
4. Archivo a importar: `database/migrations/1_setup_database.sql`
5. Clic en **Importar** y esperar el mensaje de éxito.

> El script es **idempotente**: si lo volvés a ejecutar, elimina y vuelve a crear todas las tablas. **Se pierden los datos** que hayas cargado a mano.

**Alternativa por consola MySQL:**

```powershell
cd C:\wamp64\bin\mysql\mysql9.1.0\bin
.\mysql.exe -u root
```

Dentro del prompt de MySQL:

```sql
source C:/Users/marco/Desktop/cortes-difilippo-pinerua-vilca-villanueva/database/migrations/1_setup_database.sql
```

> La ruta y la versión de MySQL pueden variar según la instalación de WAMP. Ajustá `mysql9.1.0` y la ruta del repositorio.

#### 1.3 Verificar que se creó todo

En phpMyAdmin, seleccioná la base `tech_solutions` y ejecutá en la pestaña **SQL**:

```sql
USE tech_solutions;

SHOW TABLES;

SELECT 'services' AS tabla, COUNT(*) AS filas FROM services
UNION ALL SELECT 'plans', COUNT(*) FROM plans
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'clients', COUNT(*) FROM clients
UNION ALL SELECT 'client_services', COUNT(*) FROM client_services
UNION ALL SELECT 'service_requests', COUNT(*) FROM service_requests;
```

Conteos esperados:

| Tabla | Filas |
|---|---|
| `services` | 8 |
| `plans` | 4 |
| `users` | 6 (1 admin + 5 clientes) |
| `clients` | 5 |
| `client_services` | 15 |
| `service_requests` | 22 |

✅ **Checkpoint:** la base `tech_solutions` existe y tiene las tablas y los datos demo.

---

### Paso 2 — API (puerto 5000)

**Qué hace este paso:** inicia el backend Flask que valida usuarios, aplica las reglas de negocio y consulta MySQL.

#### 2.1 Entrar a la carpeta de la API

```powershell
cd api
```

#### 2.2 Crear y activar el entorno virtual

> Si ya existe la carpeta `venv` (como en el entorno de desarrollo), saltá la creación y solo activá el entorno.

```powershell
# Solo si NO existe la carpeta venv:
python -m venv venv

# Activar el entorno virtual (Windows PowerShell):
.\venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script de activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

> En `cmd` el comando es `venv\Scripts\activate.bat`.

#### 2.3 Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

#### 2.4 Configurar el archivo `.env`

Si el archivo `api/.env` no existe, copiá la plantilla:

```powershell
Copy-Item .env.example .env
```

Contenido esperado para un MySQL local de WAMP:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=tech_solutions

# Clave para firmar los tokens de login. Larga y secreta.
SECRET_KEY=cambiame-por-un-texto-largo-y-secreto

# Orígenes permitidos por CORS (no es necesario para el frontend Flask,
# que llama a la API desde el servidor).
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

FLASK_DEBUG=1
```

Para generar una clave segura:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

> Si tu usuario `root` de MySQL tiene contraseña, completá `DB_PASSWORD`. Con WAMP por defecto va vacía.
>
> El archivo `.env` **no se sube a git** (está en `.gitignore`).

#### 2.5 Iniciar la API

```powershell
python run.py
```

Dejá esta terminal abierta. La API queda escuchando en http://localhost:5000.

#### 2.6 Verificar que responde

En el navegador o en otra terminal:

```powershell
Invoke-RestMethod http://localhost:5000/api/v1/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

También podés probar el login directamente contra la API:

```powershell
$body = @{ email = "admin@techsolutions.com"; password = "admin123" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/v1/auth/login" -ContentType "application/json" -Body $body
```

Debe devolver un `token`, el `token_type` y los datos del usuario.

> El health check no consulta MySQL: solo confirma que la API está viva. Para probar la conexión a la base, usá el login de administrador del punto anterior.

✅ **Checkpoint:** `http://localhost:5000/api/v1/health` devuelve `{"status":"ok"}`.

---

### Paso 3 — Frontend (puerto 5001)

**Qué hace este paso:** inicia la interfaz web que usa el navegador. El frontend consume la API por HTTP y arma el HTML con Jinja.

Abrí una **segunda terminal** y volvé a la raíz del repositorio:

```powershell
cd <ruta-donde-clonaste-el-repo>
cd frontend
```

#### 3.1 Crear y activar el entorno virtual

```powershell
# Solo si NO existe la carpeta venv:
python -m venv venv

# Activar el entorno virtual:
.\venv\Scripts\Activate.ps1
```

#### 3.2 Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

#### 3.3 Configurar el archivo `.env`

Si el archivo `frontend/.env` no existe:

```powershell
Copy-Item .env.example .env
```

Contenido esperado:

```env
# Dónde está corriendo la API.
API_BASE_URL=http://localhost:5000/api/v1

# Clave para firmar la cookie de sesión del frontend.
# Es independiente de la SECRET_KEY de la API.
SECRET_KEY=cambiame-por-una-clave-larga-y-secreta

# Segundos máximos de espera al API.
API_TIMEOUT=8

# Poner en 1 solo si el frontend se sirve por HTTPS.
SESSION_COOKIE_SECURE=0
```

Para generar la clave:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 3.4 Iniciar el frontend

```powershell
python run.py
```

Dejá esta terminal abierta. El frontend queda escuchando en http://localhost:5001.

#### 3.5 Verificar que abre

En el navegador:

```
http://localhost:5001
```

Debe redirigir a la pantalla de **Iniciar sesión**.

✅ **Checkpoint:** el frontend abre en http://localhost:5001 y muestra el login.

---

### Paso 4 — Ingresar al sistema

Usá los usuarios de demostración que creó el script SQL:

| Rol | Email | Contraseña | Qué puede hacer |
|---|---|---|---|
| Administrador | `admin@techsolutions.com` | `admin123` | Ver la bandeja, filtrar y resolver solicitudes |
| Cliente 1 | `cliente1@techsolutions.com` | `cliente123` | Ver servicios, crear solicitudes, consultar estados |
| Cliente 2 | `cliente2@techsolutions.com` | `cliente123` | Ídem |
| Cliente 3 | `cliente3@techsolutions.com` | `cliente123` | Ídem |
| Cliente 4 | `cliente4@techsolutions.com` | `cliente123` | Ídem |
| Cliente 5 | `cliente5@techsolutions.com` | `cliente123` | Ídem |

> Un usuario **nuevo** que se registra desde `/register` recibe el plan **Gratuito** y **no tiene servicios contratados**. Para la demo conviene usar los clientes de prueba, que ya tienen servicios y solicitudes.
>
> Las mismas credenciales están resumidas en el archivo `users.txt` de la raíz.

#### Pantallas principales

| Pantalla | Ruta | Rol |
|---|---|---|
| Iniciar sesión | `/login` | Público |
| Crear cuenta | `/register` | Público |
| Mis servicios | `/services` | Cliente |
| Nueva solicitud | `/requests/new` | Cliente |
| Mis solicitudes | `/requests` | Cliente |
| Bandeja de solicitudes | `/admin/requests` | Administrador |
| Detalle y resolución | `/admin/requests/<id>` | Administrador |

---

## 7. Verificación rápida

Marcá cada punto antes de grabar o de dar el proyecto por levantado:

- [ ] WAMP está corriendo y el ícono está verde.
- [ ] La base `tech_solutions` existe en phpMyAdmin.
- [ ] La API responde en http://localhost:5000/api/v1/health.
- [ ] El frontend abre en http://localhost:5001.
- [ ] Se puede iniciar sesión como administrador.
- [ ] Se puede iniciar sesión como cliente.
- [ ] El cliente ve sus servicios y sus solicitudes.
- [ ] El administrador ve la bandeja con las 22 solicitudes de demo.

### URLs del sistema

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5001 |
| API | http://localhost:5000 |
| Health check de la API | http://localhost:5000/api/v1/health |
| phpMyAdmin | http://localhost/phpmyadmin |

---

## 8. Usuarios de prueba y recorrido para la demo

Recorrido sugerido para mostrar el sistema completo en el video:

1. **Login como cliente** (`cliente1@techsolutions.com` / `cliente123`).
2. Abrir **Mis servicios**: se ven los servicios contratados.
3. Ir a **Nueva solicitud**: elegir un servicio, escribir el tipo de modificación y una descripción. Enviar.
4. Abrir **Mis solicitudes**: la nueva solicitud aparece en estado `pendiente`.
5. Cerrar sesión.
6. **Login como administrador** (`admin@techsolutions.com` / `admin123`).
7. Abrir la **Bandeja de solicitudes**: probar los filtros por estado y prioridad.
8. Entrar al detalle de una solicitud pendiente.
9. **Aprobar** o **rechazar con un motivo**.
10. Volver a entrar como cliente y mostrar la solicitud resuelta y, si corresponde, el motivo del rechazo.

### Sugerencia para grabar el video

1. Mostrar la arquitectura de la sección 2 (30 segundos).
2. Grabar el **Paso 1**: WAMP y la importación del SQL, mostrando la base creada.
3. Grabar el **Paso 2**: API y health check.
4. Grabar el **Paso 3**: frontend y pantalla de login.
5. Cerrar con el recorrido de esta sección, mostrando ambos roles.

---

## 9. Tests automáticos

Los tests unitarios **no necesitan MySQL ni la API corriendo**. Ejecutá cada bloque en una terminal nueva desde la raíz del repositorio (o volvé a la raíz antes del siguiente).

### API

```powershell
cd api
.\venv\Scripts\Activate.ps1
python -m pytest -q
```

Cubren autenticación, registro, planes, clientes, servicios, solicitudes, reclamos y notificaciones con repositorios en memoria.

### Frontend

```powershell
cd frontend
.\venv\Scripts\Activate.ps1
python -m pytest -q
```

Cubren login por rol, sesión, CSRF, permisos, errores del API, registro, XSS, filtros y resolución de solicitudes usando una API falsa en memoria.

### Tests E2E (opcional, requieren MySQL)

Los tests E2E usan una base aparte llamada `tech_solutions_test` y están excluidos de la corrida normal.

1. Abrí `database/migrations/1_setup_database.sql` con un editor de texto (VS Code, Notepad++).
2. Reemplazá todas las apariciones de `tech_solutions` por `tech_solutions_test`.
3. Guardá el archivo como `database/migrations/1_setup_database_test.sql` con codificación **UTF-8**.
4. Importá `database/migrations/1_setup_database_test.sql` en phpMyAdmin.
5. Ejecutá:

    ```powershell
    cd api
    python -m pytest tests/e2e -m e2e
    ```

6. Opcional: borrar el archivo temporal `database/migrations/1_setup_database_test.sql`.

> Más detalle en [`api/ARQUITECTURA.md`](api/ARQUITECTURA.md), sección 7.

---

## 10. Alternativa sin MySQL: API falsa

Si necesitás mostrar solo la interfaz y no querés depender de MySQL, el frontend incluye una **API falsa en memoria** con datos de ejemplo. Cada terminal se abre en la raíz del repositorio.

> La API real tiene que estar **detenida**, porque la API falsa también usa el puerto 5000.

**Terminal 1 — API falsa:**

```powershell
cd frontend
.\venv\Scripts\Activate.ps1
python -m tests.fake_api
```

**Terminal 2 — Frontend:**

```powershell
cd frontend
.\venv\Scripts\Activate.ps1
python run.py
```

Credenciales de la API falsa:

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@test.com` | `Clave-de-prueba-1` |
| Cliente | `cliente@test.com` | `Clave-de-prueba-1` |

> Esta alternativa sirve para ver pantallas, pero la demo completa (con los 5 clientes y las 22 solicitudes) requiere MySQL.

---

## 11. Problemas frecuentes

| Problema | Causa probable | Solución |
|---|---|---|
| `Activate.ps1 no se puede cargar` | Política de ejecución de PowerShell | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y reintentar |
| El frontend muestra **503 — Servicio no disponible** | La API o MySQL están apagados | Verificar WAMP y que `python run.py` siga corriendo en `api/` |
| `Access denied for user 'root'@'localhost'` | MySQL tiene contraseña | Completar `DB_PASSWORD` en `api/.env` |
| `Unknown database 'tech_solutions'` | No se importó el SQL | Volver al [Paso 1](#paso-1--base-de-datos-mysql) |
| No hay usuarios para iniciar sesión | No se importaron los datos demo | Reimportar `1_setup_database.sql` |
| `pip no se reconoce` | El `venv` no está activado | Activar el entorno o usar `python -m pip` |
| El puerto 5000 o 5001 está ocupado | Quedó otra instancia corriendo | `Get-NetTCPConnection -LocalPort 5000,5001 -ErrorAction SilentlyContinue` y cerrar el proceso con `taskkill /PID <PID> /F` |
| WAMP no arranca MySQL (ícono naranja/rojo) | Puerto 3306 ocupado o servicio detenido | Revisar el menú de WAMP → MySQL → Service; cerrar el proceso que use el puerto |
| `net start wampmysqld64` da acceso denegado | PowerShell sin permisos de administrador | Abrir PowerShell **como administrador** |
| phpMyAdmin no abre | Apache no está iniciado | WAMP → **Start All Services** |
| El cliente nuevo no tiene servicios | Es el comportamiento esperado | Usar un cliente de demo o contratar servicios por SQL |
| El frontend muestra una página de error del API | Respuesta inesperada o error interno | Revisar la terminal de la API; los detalles quedan en el log |

---

## 12. Reiniciar todo o resetear la base

### Reiniciar el sistema

1. Cerrar las dos terminales (API y frontend) con `Ctrl + C`.
2. Verificar que WAMP siga corriendo.
3. Volver a ejecutar `python run.py` en `api/` y en `frontend/`, con el `venv` activado en cada terminal.

### Resetear la base de datos

El script SQL elimina y vuelve a crear todas las tablas:

1. Detener la API (opcional, pero recomendado).
2. Volver a importar `database/migrations/1_setup_database.sql` en phpMyAdmin.
3. Verificar los conteos del [Paso 1.3](#13-verificar-que-se-creó-todo).
4. Volver a iniciar la API.

> ⚠️ Esto **borra todos los datos** cargados manualmente y deja la base como recién instalada.

---

## 13. Notas de seguridad

- Los archivos `.env` contienen contraseñas y claves: están en `.gitignore` y **nunca** deben subirse al repositorio.
- En producción, cambiar `SECRET_KEY` por una clave larga y aleatoria.
- Generar claves con:

  ```powershell
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- `SESSION_COOKIE_SECURE=1` solo debe activarse cuando el frontend se sirve por **HTTPS**.
- `python run.py` usa el servidor de desarrollo de Flask. Para producción se necesita un servidor WSGI (por ejemplo `waitress` o `gunicorn`).
- Las contraseñas se guardan hasheadas con `pbkdf2:sha256`; nunca en texto plano.
- La API usa tokens firmados que vencen a las 8 horas.

---

## 14. Documentación relacionada

- [`api/ARQUITECTURA.md`](api/ARQUITECTURA.md) — arquitectura, endpoints, reglas de negocio y tests de la API.
- [`frontend/ARQUITECTURA_FRONT.md`](frontend/ARQUITECTURA_FRONT.md) — arquitectura, pantallas, decisiones de diseño y tests del frontend.
- [`documentacion/base_datos/base_datos.md`](documentacion/base_datos/base_datos.md) — diseño de la base de datos.
- [`documentacion/user_stories/user_stories.md`](documentacion/user_stories/user_stories.md) — historias de usuario.
- [`documentacion/casos_de_uso/casos_de_uso.md`](documentacion/casos_de_uso/casos_de_uso.md) — casos de uso.
