# MACTI API - Punto de Entrada Principal
#
# Este módulo inicializa la aplicación FastAPI, configura los middlewares de
# seguridad (CORS), gestiona la creación automática del esquema de base de datos
# y orquesta la inclusión de los diferentes módulos de negocio (Register, Courses, Temp).
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.environment import environment
from app.modules.courses.routes import router as courses_router
from app.modules.nbgrader.routes import router as nbgrader_router
from app.modules.register.routes import router as register_router
from app.modules.temp.routes import router as temp_router
from app.shared import models as _models  # noqa: F401
from app.shared.services.redis_client import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la app: conecta y desconecta Redis."""
    # Al arrancar
    await redis_client.connect()
    print("✅ Redis conectado")
    yield
    # Al apagar
    await redis_client.disconnect()
    print("🔌 Redis desconectado")


# Inicialización de la persistencia
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MACTI API",
    description="Backend para la gestión de identidades y recursos académicos UNAM",
    version="1.0.0",
    lifespan=lifespan,  # ← NUEVO
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
app.include_router(courses_router)
app.include_router(nbgrader_router)

if environment.APP_ENV == "development":
    app.include_router(temp_router)
