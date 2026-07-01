# app/core/logging/COMO_USAR_LOGS.py
"""
═══════════════════════════════════════════════════════════════════════════════
GUÍA DE USO DE LOGS EN MACTI API
═══════════════════════════════════════════════════════════════════════════════

Este archivo es SOLO una guía de referencia. No se importa, no se ejecuta.
Muestra cómo implementar los logs en cada capa de la arquitectura.

IMPORTS DISPONIBLES:
  from app.core.logging.macti_logger import (
      log_service_error,   # Errores de API externas (Moodle, Keycloak, Jupyter)
      log_db_error,        # Errores de BD en try-catch de repositorios
      log_macti_error,     # Errores de lógica de negocio en funciones privadas
      log_security_event,  # Eventos de seguridad (login, acceso denegado, etc.)
      log_info,            # Información general
  )

REGLA DE ORO:
  - Errores de API externa  → log_service_error()
  - Errores de BD           → log_db_error() DENTRO del try-catch del repositorio
  - Errores de Macti        → log_macti_error() en funciones PRIVADAS del controlador
  - Función principal del controlador → SOLO ejecuta funciones privadas, sin lógica
═══════════════════════════════════════════════════════════════════════════════
"""

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  1. SERVICIOS - Para errores de respuesta de API externas               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Archivos donde se usa:
#   app/shared/services/moodle_service.py
#   app/modules/register/services/kc_service.py
#   app/modules/register/services/moodle_service.py
#
# ───────────────────────────────────────────────────────────────────────────

# from app.core.logging.macti_logger import log_service_error

# # Cuando una llamada a Moodle/Keycloak falle:
# if not result["success"]:
#     log_service_error(
#         logger_name="moodle_service",              # Nombre del módulo
#         service="Moodle",                           # Servicio externo
#         endpoint="core_user_get_users_by_field",    # Endpoint llamado
#         error_message=result["error_message"],      # Mensaje del error
#         extra={                                     # Info adicional (opcional)
#             "institute": institute.value,
#             "email": user_email,
#         },
#     )
#     return SimpleNamespace(error=result["error_message"])


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  2. REPOSITORIOS - Errores de BD en try-catch                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Archivos donde se usa:
#   app/modules/register/repositories/create_account_repository.py
#   app/modules/register/repositories/authenticated_student_request_repository.py
#   app/modules/register/repositories/authenticated_teacher_request_repository.py
#   app/modules/register/repositories/request_account_repository.py
#
# ───────────────────────────────────────────────────────────────────────────

# from sqlalchemy.exc import SQLAlchemyError
# from app.core.logging.macti_logger import log_db_error

# # En CUALQUIER método del repositorio que haga operaciones de BD:
# def commit(self):
#     try:
#         self.db.commit()
#     except SQLAlchemyError as exc:
#         # ✅ Log ANTES del rollback
#         log_db_error(
#             logger_name="create_account_repository",  # Nombre del repo
#             operation="commit",                       # Operación que falló
#             error_message=str(exc),                   # Mensaje del error
#         )
#         self.db.rollback()
#         raise

# # Con info extra:
# def save_jids(self, auth_id, kc_id, moodle_id):
#     try:
#         jids = JIDs(auth_id=auth_id, kc_id=kc_id, moodle_id=moodle_id)
#         self.db.add(jids)
#         self.db.flush()
#         return jids
#     except SQLAlchemyError as exc:
#         log_db_error(
#             logger_name="create_account_repository",
#             operation="save_jids",
#             error_message=str(exc),
#             extra={                               # Info adicional útil
#                 "auth_id": auth_id,
#                 "kc_id": str(kc_id),
#                 "moodle_id": moodle_id,
#             },
#         )
#         self.db.rollback()
#         raise


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  3. CONTROLADORES - Errores de Macti en funciones PRIVADAS             ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# Archivos donde se usa:
#   app/modules/register/controllers/create_account_controller.py
#   app/modules/register/controllers/authenticated_student_request_controller.py
#   app/modules/register/controllers/authenticated_teacher_request_controller.py
#
# ───────────────────────────────────────────────────────────────────────────

# from app.core.logging.macti_logger import log_macti_error

# # La función PRINCIPAL del controlador SOLO ejecuta funciones privadas:
# @staticmethod
# async def create_account(data, db):
#     """✅ Función principal: solo llama funciones privadas."""
#     repo = CreateAccountRepository(db)
#     auth = CreateAccountController._get_auth_or_raise(repo, data)
#     CreateAccountController._validate_verification_tokens(auth, data.token)
#     CreateAccountController._validate_request_approved(auth)
#     # ... resto del flujo ...

# # Los logs van en las funciones PRIVADAS:
# @staticmethod
# def _validate_verification_tokens(auth, token):
#     """✅ Función PRIVADA: aquí se loguean errores de negocio."""
#     if auth.verification_token is None:
#         log_macti_error(
#             logger_name="create_account_controller",
#             error_code="TOKEN_NO_ENCONTRADO",
#             message="No se encontró token de verificación",
#             extra={"auth_id": auth.id},
#         )
#         raise HTTPException(status_code=400, detail={...})

#     if auth.verification_token.token != token:
#         log_macti_error(
#             logger_name="create_account_controller",
#             error_code="TOKEN_INVALIDO",
#             message="Token no coincide con el esperado",
#             extra={
#                 "auth_id": auth.id,
#                 "expected": str(auth.verification_token.token),
#                 "received": str(token),
#             },
#         )
#         raise HTTPException(status_code=400, detail={...})

# @staticmethod
# def _validate_request_approved(auth):
#     """✅ Función PRIVADA."""
#     if not approved:
#         log_macti_error(
#             logger_name="create_account_controller",
#             error_code="SOLICITUD_NO_APROBADA",
#             message=f"Status actual: {status.value}",
#             extra={"auth_id": auth.id, "current_status": status.value},
#         )
#         raise HTTPException(status_code=400, detail={...})


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  4. SEGURIDAD - Eventos de seguridad (opcional)                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
#
# ───────────────────────────────────────────────────────────────────────────

# from app.core.logging.macti_logger import log_security_event

# # Login exitoso:
# log_security_event(
#     logger_name="auth_middleware",
#     event="login_exitoso",
#     user_id=user.id,
#     ip=request.client.host,
# )

# # Token inválido:
# log_security_event(
#     logger_name="auth_middleware",
#     event="token_invalido",
#     user_id=None,
#     ip=request.client.host,
#     extra={"reason": "Token expirado"},
# )

# # Acceso denegado:
# log_security_event(
#     logger_name="auth_middleware",
#     event="acceso_denegado",
#     user_id=user.id,
#     ip=request.client.host,
#     extra={"recurso": "/admin", "rol_requerido": "admin"},
# )


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  RESUMEN                                                               ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║                                                                         ║
# ║  CAPA           → FUNCIÓN               → DÓNDE                        ║
# ║  ─────────────    ────────────────────    ────────────────────────────  ║
# ║  Servicio       → log_service_error()   → Cuando falla API externa     ║
# ║  Repositorio    → log_db_error()        → DENTRO del except            ║
# ║  Controlador    → log_macti_error()     → En funciones PRIVADAS        ║
# ║  Seguridad      → log_security_event()  → Login, logout, accesos       ║
# ║  General        → log_info()            → Info relevante               ║
# ║                                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
