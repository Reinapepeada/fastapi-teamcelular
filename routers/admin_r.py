from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import text

from database.connection.SQLConection import get_session
from database.models.admin import (
    Admin, AdminCreate, AdminLogin, AdminOut, AdminUpdate, 
    PasswordChange, Token, AdminRole
)
from services.auth_s import (
    authenticate_admin, create_access_token, get_password_hash,
    get_admin_by_username, ACCESS_TOKEN_EXPIRE_MINUTES,
    RequireAdmin, RequireSuperAdmin, RequireAdminOrHigher,
    verify_password
)

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    login_data: AdminLogin,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Login de administrador.
    Acepta username o email en el campo 'identifier'.
    Retorna un token JWT para autenticación.
    
    Body:
    - identifier: username o email
    - password: contraseña
    """
    admin = authenticate_admin(session, login_data.identifier, login_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario/email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.username, "role": admin.role.value},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def register_admin(
    admin_data: AdminCreate,
    session: Annotated[Session, Depends(get_session)],
    current_admin: RequireSuperAdmin  # Solo SUPER_ADMIN puede crear admins
):
    """
    Registra un nuevo administrador.
    Solo accesible por SUPER_ADMIN.
    """
    # Verificar si el username ya existe
    existing = get_admin_by_username(session, admin_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está en uso"
        )
    
    # Verificar si el email ya existe
    stmt = select(Admin).where(Admin.email == admin_data.email)
    if session.exec(stmt).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está en uso"
        )
    
    # Crear el admin
    new_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        role=admin_data.role
    )
    session.add(new_admin)
    session.commit()
    session.refresh(new_admin)
    
    return new_admin


@router.post("/setup", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def setup_first_admin(
    admin_data: AdminCreate,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Crea el primer SUPER_ADMIN.
    Solo funciona si no hay admins en el sistema.
    """
    # Verificar si ya existe algún admin
    stmt = select(Admin)
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un administrador. Use /register con un SUPER_ADMIN."
        )
    
    # Crear el primer SUPER_ADMIN
    first_admin = Admin(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=get_password_hash(admin_data.password),
        role=AdminRole.SUPER_ADMIN  # Siempre SUPER_ADMIN
    )
    session.add(first_admin)
    session.commit()
    session.refresh(first_admin)
    
    return first_admin


@router.get("/me", response_model=AdminOut)
def get_current_admin_info(current_admin: RequireAdmin):
    """
    Obtiene información del admin autenticado.
    """
    return current_admin


@router.put("/me/password")
def change_password(
    password_data: PasswordChange,
    current_admin: RequireAdmin,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Cambia la contraseña del admin autenticado.
    """
    if not verify_password(password_data.current_password, current_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    current_admin.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_admin)
    session.commit()
    
    return {"msg": "Contraseña actualizada correctamente"}


@router.get("/list", response_model=list[AdminOut])
def list_admins(
    current_admin: RequireSuperAdmin,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Lista todos los administradores.
    Solo accesible por SUPER_ADMIN.
    """
    stmt = select(Admin)
    admins = session.exec(stmt).all()
    return admins


@router.put("/update/{admin_id}", response_model=AdminOut)
def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    current_admin: RequireSuperAdmin,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Actualiza un administrador.
    Solo accesible por SUPER_ADMIN.
    """
    admin = session.get(Admin, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin no encontrado"
        )
    
    if admin_data.email:
        admin.email = admin_data.email
    if admin_data.role:
        admin.role = admin_data.role
    if admin_data.is_active is not None:
        admin.is_active = admin_data.is_active
    
    session.add(admin)
    session.commit()
    session.refresh(admin)
    
    return admin


@router.delete("/delete/{admin_id}")
def delete_admin(
    admin_id: int,
    current_admin: RequireSuperAdmin,
    session: Annotated[Session, Depends(get_session)]
):
    """
    Elimina un administrador.
    Solo accesible por SUPER_ADMIN.
    No puede eliminarse a sí mismo.
    """
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminarte a ti mismo"
        )
    
    admin = session.get(Admin, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin no encontrado"
        )
    
    session.delete(admin)
    session.commit()
    
    return {"msg": "Admin eliminado correctamente"}


@router.get("/debug/schema")
def debug_schema(current_admin: RequireSuperAdmin, session: Annotated[Session, Depends(get_session)]):
    """
    Endpoint de depuración (SUPER_ADMIN): retorna el udt_name de la columna `productvariant.color`.
    """
    try:
            udt = session.exec(text("SELECT udt_name, column_default FROM information_schema.columns WHERE table_name = 'productvariant' AND column_name = 'color' ")).first()
            if udt:
                udt_name = udt[0]
                column_default = udt[1]
            else:
                udt_name = None
                column_default = None
            return {"udt_name": udt_name, "column_default": column_default}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el schema: {e}")


@router.get("/debug/invalid-colors")
def debug_invalid_colors(current_admin: RequireSuperAdmin, session: Annotated[Session, Depends(get_session)]):
    """
    Endpoint de depuración (SUPER_ADMIN): retorna los valores invalidos en la columna color.
    """
    allowed = [
        'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA','ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
    ]
    # Construir params para la query
    placeholders = ", ".join([f":val{i}" for i in range(len(allowed))])
    q = text(f"SELECT DISTINCT color FROM productvariant WHERE color IS NOT NULL AND color::text NOT IN ({placeholders})")
    params = {f"val{i}": v for i, v in enumerate(allowed)}
    try:
        rows = session.exec(q, params).all()
        invalids = [r[0] for r in rows]
        return {"invalid_colors": invalids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar valores invalidos: {e}")


@router.post("/debug/fix-color")
def debug_fix_color(current_admin: RequireSuperAdmin, session: Annotated[Session, Depends(get_session)]):
    """
    Endpoint de depuración (SUPER_ADMIN): limpia valores inválidos y, si es necesario, convierte la columna a enum `color`.
    """
    allowed = [
        'ROJO','AZUL','VERDE','AMARILLO','NARANJA','VIOLETA','ROSADO','MARRON','GRIS','BLANCO','NEGRO','BORDO'
    ]
    placeholders = ", ".join([f":val{i}" for i in range(len(allowed))])
    try:
        # 1) Limpiar valores inválidos
        u = text(f"UPDATE productvariant SET color = NULL WHERE color IS NOT NULL AND color::text NOT IN ({placeholders})")
        params = {f"val{i}": v for i, v in enumerate(allowed)}
        res = session.exec(u, params)
        session.commit()

        # 2) Verificar udt_name y alterar tipo si es necesario
        udt = session.exec(text("SELECT udt_name FROM information_schema.columns WHERE table_name = 'productvariant' AND column_name = 'color'")).first()
        udt_name = udt and udt[0] or None
        if udt_name != 'color':
            session.exec(text("ALTER TABLE productvariant ALTER COLUMN color TYPE color USING (color::text::color);"))
            session.exec(text("ALTER TABLE productvariant ALTER COLUMN color DROP NOT NULL;"))
            session.commit()

        new_udt = session.exec(text("SELECT udt_name FROM information_schema.columns WHERE table_name = 'productvariant' AND column_name = 'color' ")).first()
        return {"ok": True, "udt_name_after": new_udt and new_udt[0] or None}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error aplicando fix: {e}")
