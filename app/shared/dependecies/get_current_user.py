"""
TODOS:
- Crear un diccionario que guarde las claves publicas de cada instancia de Keycloak
- Pasar el institute como parametro a get_current_user para usar la clave publica correcta
- Usar el Enum InstitutesEnum para definir las diferentes instancias de Keycloak
"""

# import httpx
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer
# from jose import jwt

# KEYCLOAK_URL = "https://tu-keycloak.com/realms/mi-realm"
# JWKS_URL = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"
# AUDIENCE = "tu-client-id"
# ALGORITHM = "RS256"

# security = HTTPBearer()

# # Cache para las llaves públicas de KC
# JWKS = None


# async def get_jwks():
#     global JWKS
#     if JWKS is None:
#         async with httpx.AsyncClient() as client:
#             JWKS = (await client.get(JWKS_URL)).json()
#     return JWKS


# def get_signing_key(jwks, kid):
#     keys = jwks.get("keys", [])
#     for key in keys:
#         if key.get("kid") == kid:
#             return key
#     return None


# async def get_current_user(credentials=Depends(security)):
#     token = credentials.credentials

#     jwks = await get_jwks()

#     # Obtener encabezado del token
#     try:
#         unverified_header = jwt.get_unverified_header(token)
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token header",
#         ) from Exception

#     signing_key = get_signing_key(jwks, unverified_header["kid"])
#     if signing_key is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid signing key",
#         )

#     # Verificar token
#     try:
#         payload = jwt.decode(
#             token,
#             signing_key,
#             algorithms=[ALGORITHM],
#             audience=AUDIENCE,
#             issuer=f"{KEYCLOAK_URL}",
#         )
#     except Exception:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid or expired token",
#         ) from Exception

#     return payload
