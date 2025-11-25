from fastapi import APIRouter
from typing import List
from controllers.product_c import create_branch, delete_branch, get_branches, update_branch
from database.connection.SQLConection import SessionDep
from database.models.product import BranchCreate, BranchOut
from services.auth_s import RequireEditorOrHigher, RequireAdminOrHigher

router = APIRouter()


# =============================================
# ENDPOINTS PÚBLICOS
# =============================================

@router.get("/get/all")
def get_branch_endp(
    session: SessionDep = SessionDep
) -> List[BranchOut]:
    """Obtener todas las sucursales - PÚBLICO"""
    return get_branches(session)


# =============================================
# ENDPOINTS PROTEGIDOS
# =============================================

@router.post("/create")
def create_branch_endp(
    branch: BranchCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Crear sucursal - REQUIERE AUTH (Editor+)"""
    return create_branch(branch, session)


@router.put("/update")
def update_branch_endp(
    branch_id: int,
    branch: BranchCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Actualizar sucursal - REQUIERE AUTH (Editor+)"""
    return update_branch(branch_id, branch, session)


@router.delete("/delete")
def delete_branch_endp(
    branch_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher
):
    """Eliminar sucursal - REQUIERE AUTH (Admin+)"""
    return delete_branch(branch_id, session)