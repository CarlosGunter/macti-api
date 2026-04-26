# MACTI API - Punto de Entrada Principal
#
# Este módulo inicializa la aplicación FastAPI, configura los middlewares de
# seguridad (CORS), gestiona la creación automática del esquema de base de datos
# y orquesta la inclusión de los diferentes módulos de negocio (Register, Courses, Temp).

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.environment import environment
from app.modules.register.routes import router as register_router
from app.modules.temp.routes import router as temp_router
from app.shared import models as _models  # noqa: F401

# Inicialización de la persistencia: Crea las tablas si no existen al arrancar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MACTI API",
    description="Backend para la gestión de identidades y recursos académicos UNAM",
    version="1.0.0",
)

# Configuración de CORS
frontend_origin = (
    "https://macti-frontend.vercel.app" if environment.APP_ENV != "development" else "*"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def read_root():
    """Endpoint de verificación de salud (Health Check)."""
    return {"Inicio": "MACTI API - Sistema en línea"}


# Registro de rutas modulares
app.include_router(register_router)
# app.include_router(courses_router)

if environment.APP_ENV == "development":
    app.include_router(temp_router)
