from enum import Enum


class AccountStatusEnum(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CREATED = "created"


# Se agrego lo roles
class AccountRoleEnum(str, Enum):
    ALUMNO = "alumno"
    DOCENTE = "docente"
