from fastapi import FastAPI
from app.modules.auth.routes import router as auth_router
from app.core.database import engine, Base

from dotenv import load_dotenv
load_dotenv()

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Inicio": "MACTI API"}

# Include the auth router
app.include_router(auth_router)
