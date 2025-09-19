from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default="Pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AccountRequest(Base):
    __tablename__ = "account_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    teacher = Column(String, nullable=False)
    course_id = Column(Integer, nullable=False)
    status = Column(String, default="Pending")
    kc_id = Column(String, nullable=True)
    moodle_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())