from sqlalchemy import Boolean, Column, Integer, String

from .session import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_contributor = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    can_sync = Column(Boolean, default=False)
