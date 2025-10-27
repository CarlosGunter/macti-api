# 🚀 MACTI API

> Una API desarrollada con FastAPI para la gestión de cuentas de usuario y autenticación integrada con Keycloak y Moodle.

---

## 🛠️ Tecnologías Utilizadas

- **Framework**: FastAPI 0.116.1
- **Base de Datos**: SQLite con SQLAlchemy 2.0.43
- **Validación**: Pydantic 2.11.7
- **Servidor**: Uvicorn 0.35.0
- **Autenticación**: Integración con Keycloak y Moodle
- **Documentación**: Swagger UI y ReDoc (automática con FastAPI)

---

## 🚀 Instalación y Configuración Local

### Prerrequisitos

- Python 3.8+
- pip (gestor de paquetes de Python)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/CarlosGunter/macti-api
cd macti-api
```

### 2. Crear y Activar Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requeriments.txt
```

### 4. Inicializar la Base de Datos

La base de datos SQLite se creará automáticamente en la raíz del proyecto (`macti.db`) al ejecutar la aplicación por primera vez.

### 5. Ejecutar el Servidor

```bash
# Desde la raíz del proyecto
uvicorn app.main:app --reload
```

### 6. Acceder a la API
Por defecto, FastAPI corre en el puerto 8000. Por lo tanto, los endpoints estarán disponibles en:

- **API Base**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc

Si deseas cambiar el puerto o la dirección, puedes modificar los parámetros en el comando `uvicorn` de la siguiente manera:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📁 Estructura del Proyecto

```
backend-py/
│
├── 📄 macti.db                    # Base de datos SQLite
├── 📄 README.md                   # Este archivo
├── 📄 requeriments.txt            # Dependencias del proyecto
│
└── app/                           # Código fuente principal
    ├── 📄 main.py                 # Punto de entrada de la aplicación
    │
    ├── core/                      # Núcleo de la aplicación
    │   └── 📄 database.py         # Configuración de base de datos
    │
    ├── modules/                   # Módulos de funcionalidad
    │   ├── auth/                  # Módulo de autenticación
    │   │   ├── 📄 controllers.py  # Lógica de negocio
    │   │   ├── 📄 models.py       # Modelos de base de datos
    │   │   ├── 📄 routes.py       # Definición de endpoints
    │   │   ├── 📄 schema.py       # Esquemas de validación
    │   │   └── 📄 services.py     # Servicios externos
    │   │
    │   └── recomendations/        # Módulo de recomendaciones a usuarios
    │
    └── utils/                     # Utilidades generales
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

### 👤 User
```sql
- id: Integer (Primary Key)
- name: String
- last_name: String  
- email: String (Unique)
- status: String (Default: "Pending")
- created_at: DateTime
- updated_at: DateTime
```

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

---

## 🔧 Desarrollo

### Agregar Nuevos Endpoints

1. Crear el modelo en `models.py`
2. Definir el schema en `schema.py`
3. Implementar la lógica en `controllers.py`
4. Definir las rutas en `routes.py`
5. Registrar el router en `main.py`

---