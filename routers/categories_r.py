from fastapi import APIRouter
from typing import List
from controllers.product_c import create_category, delete_category, get_categories, update_category
from database.connection.SQLConection import SessionDep
from database.models.product import CategoryCreate, CategoryOut
from services.auth_s import RequireEditorOrHigher, RequireAdminOrHigher

router = APIRouter()


# =============================================
# ENDPOINTS PÚBLICOS
# =============================================

@router.get("/get/all")
def get_category_endp(
    session: SessionDep = SessionDep
) -> List[CategoryOut]:
    """Obtener todas las categorías - PÚBLICO"""
    return get_categories(session)


# =============================================
# ENDPOINTS PROTEGIDOS
# =============================================

@router.post("/create")
def create_category_endp(
    category: CategoryCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Crear categoría - REQUIERE AUTH (Editor+)"""
    return create_category(category, session)


@router.put("/update")
def update_category_endp(
    category_id: int,
    category: CategoryCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Actualizar categoría - REQUIERE AUTH (Editor+)"""
    return update_category(category_id, category, session)


@router.delete("/delete")
def delete_category_endp(
    category_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher
):
    """Eliminar categoría - REQUIERE AUTH (Admin+)"""
    return delete_category(category_id, session)