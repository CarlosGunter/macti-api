from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    KEYCLOAK_SERVER_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "master"
    KEYCLOAK_ADMIN_CLIENT_ID: str = "fastapi-auth-service"         
    KEYCLOAK_ADMIN_CLIENT_SECRET: str = "rxUpWxdEs19uezEcT3yLbSJG2vMbF1Ld"
    
    class Config:
        env_file = ".env" 
        extra='ignore' 
settings = Settings()