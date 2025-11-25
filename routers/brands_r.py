from fastapi import APIRouter
from typing import List
from controllers.product_c import create_brand, delete_brand, get_brands, update_brand
from database.connection.SQLConection import SessionDep
from database.models.product import BrandCreate, BrandOut
from services.auth_s import RequireEditorOrHigher, RequireAdminOrHigher

router = APIRouter()


# =============================================
# ENDPOINTS PÚBLICOS
# =============================================

@router.get("/get/all")
def get_brand_endp(
    session: SessionDep = SessionDep
) -> List[BrandOut]:
    """Obtener todas las marcas - PÚBLICO"""
    return get_brands(session)


# =============================================
# ENDPOINTS PROTEGIDOS
# =============================================

@router.post("/create")
def create_brand_endp(
    brand: BrandCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Crear marca - REQUIERE AUTH (Editor+)"""
    return create_brand(brand, session)


@router.put("/update")
def update_brand_endp(
    brand_id: int,
    brand: BrandCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Actualizar marca - REQUIERE AUTH (Editor+)"""
    return update_brand(brand_id, brand, session)


@router.delete("/delete")
def delete_brand_endp(
    brand_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher
):
    """Eliminar marca - REQUIERE AUTH (Admin+)"""
    return delete_brand(brand_id, session)