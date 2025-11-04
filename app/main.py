from fastapi import FastAPI
from app.modules.auth.routes import router as auth_router
from app.core.database import engine, Base
from fastapi.middleware.cors import CORSMiddleware

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"Inicio": "MACTI API"}


# Include the auth router
app.include_router(auth_router)
