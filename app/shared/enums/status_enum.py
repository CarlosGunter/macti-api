from enum import Enum


class AccountStatusEnum(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CREATED = "created"
