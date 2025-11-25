from datetime import datetime, timedelta
from typing import Annotated
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from dotenv import load_dotenv

from database.connection.SQLConection import get_session
from database.models.admin import Admin, AdminRole, TokenData

load_dotenv()

# Configuración de seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-cambiar-en-produccion")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 horas por defecto

# Contexto de encriptación para passwords - usar bcrypt
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
except Exception:
    # Si hay error con bcrypt, usar argon2
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    # Limitar a 72 bytes para bcrypt
    password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_admin_by_username(session: Session, username: str) -> Admin | None:
    """Obtiene un admin por su username."""
    statement = select(Admin).where(Admin.username == username)
    return session.exec(statement).first()


def authenticate_admin(session: Session, username: str, password: str) -> Admin | None:
    """Autentica un admin con username y password."""
    admin = get_admin_by_username(session, username)
    if not admin:
        return None
    if not verify_password(password, admin.hashed_password):
        return None
    return admin


async def get_current_admin(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)]
) -> Admin:
    """Obtiene el admin actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=payload.get("role"))
    except JWTError:
        raise credentials_exception
    
    admin = get_admin_by_username(session, token_data.username)
    if admin is None:
        raise credentials_exception
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin desactivado"
        )
    return admin


async def get_current_active_admin(
    current_admin: Annotated[Admin, Depends(get_current_admin)]
) -> Admin:
    """Verifica que el admin esté activo."""
    if not current_admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin inactivo"
        )
    return current_admin


def require_role(allowed_roles: list[AdminRole]):
    """Decorator para requerir ciertos roles."""
    async def role_checker(
        current_admin: Annotated[Admin, Depends(get_current_active_admin)]
    ) -> Admin:
        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de estos roles: {[r.value for r in allowed_roles]}"
            )
        return current_admin
    return role_checker


# Dependencias pre-configuradas para usar en los endpoints
RequireAdmin = Annotated[Admin, Depends(get_current_active_admin)]
RequireSuperAdmin = Annotated[Admin, Depends(require_role([AdminRole.SUPER_ADMIN]))]
RequireEditorOrHigher = Annotated[Admin, Depends(require_role([AdminRole.SUPER_ADMIN, AdminRole.ADMIN, AdminRole.EDITOR]))]
RequireAdminOrHigher = Annotated[Admin, Depends(require_role([AdminRole.SUPER_ADMIN, AdminRole.ADMIN]))]
