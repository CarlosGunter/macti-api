# MACTI API - Punto de Entrada Principal
#
# Este módulo inicializa la aplicación FastAPI, configura los middlewares de
# seguridad (CORS), gestiona la creación automática del esquema de base de datos
# y orquesta la inclusión de los diferentes módulos de negocio (Auth, Courses, Temp).

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.environment import environment
from app.modules.auth.routes import router as auth_router
from app.modules.courses.routes import router as courses_router
from app.modules.temp.routes import router as temp_router

# Inicialización de la persistencia: Crea las tablas si no existen al arrancar
# Nota: En entornos de producción avanzados se recomienda usar Alembic para migraciones.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MACTI API",
    description="Backend para la gestión de identidades y recursos académicos UNAM",
    version="1.0.0",
)


# Configuración de CORS (Cross-Origin Resource Sharing)
# Permite la comunicación con el Front-end de Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restringir a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def read_root():
    """Endpoint de verificación de salud (Health Check)."""
    return {"Inicio": "MACTI API - Sistema en línea"}


# Registro de rutas modulares (Routing)
app.include_router(auth_router)
app.include_router(courses_router)

# Rutas temporales para desarrollo: Solo se incluyen si APP_ENV=development
if environment.APP_ENV == "development":
    app.include_router(temp_router)
