from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel
from datetime import datetime
from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"  # Solo puede editar productos, no eliminar


class Admin(SQLModel, table=True):
    """Administradores del sistema"""
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role: AdminRole = Field(default=AdminRole.ADMIN)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# =============================================
# SCHEMAS PYDANTIC - ADMIN
# =============================================

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: AdminRole = AdminRole.ADMIN


class AdminLogin(BaseModel):
    username: str
    password: str


class AdminOut(BaseModel):
    id: int
    username: str
    email: str
    role: AdminRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUpdate(BaseModel):
    email: EmailStr | None = None
    role: AdminRole | None = None
    is_active: bool | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    role: AdminRole | None = None
