# 🚀 MACTI API

> Una API desarrollada con FastAPI para la gestión de cuentas de usuario y autenticación integrada con Keycloak y Moodle.

---

## 🛠️ Tecnologías Utilizadas

- **Framework**: FastAPI
- **Base de Datos**: SQLite con SQLAlchemy 2
- **Validación**: Pydantic 2
- **Servidor**: Uvicorn
- **Autenticación**: Integración con Keycloak
- **Documentación**: Swagger UI y ReDoc (automática con FastAPI)
- **Gestión de Dependencias**: uv
- **Linter y Formateo**: Ruff
- **Control de Calidad**: Pre-commit 4

---

## 🚀 Instalación y Configuración Local

### Prerrequisitos

- Python 3.8+
- UV (gestor de paquetes de Python)

### 1. Clonar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/CarlosGunter/macti-api
cd macti-api
```

### 2. Instalar uv

Para linux/macOS, ejecuta:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Para Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Puedes encontrar más detalles en la [documentación oficial de uv](https://docs.astral.sh/uv/getting-started/installation/).

> [!TIP]
> uv se encarga de crear y gestionar entornos virtuales automáticamente. Por lo tanto, no es necesario crear uno manualmente.

### 3. Ejecutar el proyecto
```bash
uv run uvicorn app.main:app --reload
```

Éste comando hará lo siguiente:
- Instalar las dependencias listadas en `pyproject.toml` si no están instaladas.
- Crear un entorno virtual aislado para el proyecto si no existe.
- Iniciar el servidor de desarrollo de FastAPI con recarga automática.
- Iniciará la BD SQLite si no existe.
- Ejecutar las migraciones de la base de datos si es necesario.

### 4. Configurar Hooks de Pre-Commit

```bash
# Instalar hooks de pre-commit
uv run pre-commit install
```

### 5. Acceder a la API
Por defecto, FastAPI corre en el puerto 8000. Por lo tanto, los endpoints estarán disponibles en:

- **API Base**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

Si deseas cambiar el puerto o la dirección, puedes modificar los parámetros en el comando `uvicorn` de la siguiente manera:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Estructura del Proyecto

```
backend-py/
│
├── 📄 README.md                   # Este archivo
├── 📄 pyproject.toml              # Configuración del proyecto
│
└── app/                           # Código fuente principal
    ├── 📄 main.py                 # Punto de entrada de la aplicación
    │
    ├── core/                      # Núcleo de la aplicación
    │   └── 📄 database.py         # Configuración de base de datos
    │   └── 📄 config.py           # Centralización de las variables de entorno
    │
    ├── modules/                   # Módulos de funcionalidad
    │   ├── auth/                  # Módulo de autenticación
    │   │   ├── 📄 controllers    # Lógica de negocio
    │   │   ├── 📄 models         # Modelos de base de datos
    │   │   ├── 📄 routes         # Definición de endpoints
    │   │   ├── 📄 schemas        # Esquemas de validación
    │   │   └── 📄 services       # Servicios externos como llamadas a APIs
    │   │
    │   └── recomendations/        # Módulo de recomendaciones a usuarios
    │
    └── shared/                     # Modulo general compartido
```

---

## 🔌 Endpoints Disponibles

### 🏠 Endpoint Principal

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Página de inicio de la API |

**Respuesta:**
```json
{
  "Inicio": "MACTI API"
}
```

---

### 🔐 Módulo de Autenticación (`/auth`)

#### 1. Solicitar Cuenta de Usuario

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/auth/request-account` | Crear una nueva solicitud de cuenta |

**Payload:**
```json
{
  "name": "Juan",
  "last_name": "Pérez",
  "email": "juan.perez@ejemplo.com",
  "teacher": "Prof. García",
  "course_id": 123
}
```

**Respuesta:**
```json
{
  "name": "Juan",
  "last_name": "Pérez",
  "email": "juan.perez@ejemplo.com",
  "teacher": "Prof. García",
  "course_id": 123
}
```

#### 2. Listar Solicitudes de Cuenta

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/auth/list-accounts-requests?course_id={id}` | Obtener solicitudes filtradas por curso |

**Parámetros:**
- `course_id` (query): ID del curso para filtrar

**Respuesta:**
```json
[
  {
    "name": "Juan",
    "last_name": "Pérez", 
    "email": "juan.perez@ejemplo.com",
    "teacher": "Prof. García",
    "course_id": 123
  }
]
```

#### 3. Confirmar Solicitud de Cuenta

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `PATCH` | `/auth/confirm-account` | Aprobar o rechazar una solicitud |

**Payload:**
```json
{
  "id": 1,
  "status": "approved"
}
```

**Estados válidos:** `pending`, `approved`, `rejected`

#### 4. Crear Cuenta de Usuario

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/auth/create-account` | Crear cuenta en Keycloak y Moodle |

**Payload:**
```json
{
  "id": 1,
  "password": "contraseña_segura"
}
```

**Nota:** La solicitud debe estar en estado `approved` antes de crear la cuenta.

---

## 📊 Modelos de Base de Datos

### 📝 AccountRequest
```sql
- id: Integer (Primary Key)
- name: String
- last_name: String
- email: String
- teacher: String
- course_id: Integer
- status: String (Default: "Pending")
- kc_id: String (Keycloak ID)
- moodle_id: String (Moodle ID)
- created_at: DateTime
```

### ▶️ MCT_Validacion
```sql
- id: Integer (Primary Key)
- email: String
- token: String
- fecha_solicitud: DateTime
- fecha_expiracion: DateTime
- bandera: String
```

---

## 🔧 Desarrollo

### Entorno y rutas temporales

- Define `APP_ENV` en tu `.env` con uno de estos valores: `development`, `testing`, `production`.
- Las rutas del módulo temporal (`/temp/*`) solo se registran cuando `APP_ENV=development`.

### Agregar Nuevos Endpoints

1. Crear el modelo en `models.py`
2. Definir el schema en `schema.py`
3. Implementar la lógica en `controllers.py`
4. Definir las rutas en `routes.py`
5. Registrar el router en `main.py`

### Flujo de Trabajo

Puedes seguir el flujo de trabajo descrito en el archivo `CONTRIBUTING.md` para contribuir al proyecto.

No olvides ejecutar el paso 4 de configuración de hooks de pre-commit después de clonar el repositorio.

---