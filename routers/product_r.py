from fastapi import APIRouter, status, HTTPException
from typing import Annotated, List, Optional
from fastapi import Query
from database.connection.SQLConection import SessionDep
from database.models.product import (
    ProductCreate,
    ProductOutPaginated, 
    ProductUpdate, 
    ProductOut,
    ProductVariantCreateList, 
    ProductVariantOut, 
    ProductVariantUpdate,
)
from controllers.product_c import (
    create_product,
    create_product_variant,
    delete_product, delete_product_variant,
    get_filtered_paginated_products_controller,
    get_product_variants_by_product_id,
    get_products_all,
    get_products_by_id, update_product, update_product_variant,
    upsert_product_variant,
    get_min_max_price
)
from services.auth_s import RequireEditorOrHigher, RequireAdminOrHigher

router = APIRouter()

# =============================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# =============================================

@router.get("/get/{product_id}")
def get_product_by_id_endp(
    product_id: int,
    session: SessionDep = SessionDep
) -> ProductOut:
    """Obtener producto por ID - PÚBLICO"""
    return get_products_by_id(product_id, session)


@router.get("/all")
def get_products_all_endp(
    session: SessionDep = SessionDep
) -> List[ProductOut]:
    """Obtener todos los productos - PÚBLICO"""
    return get_products_all(session)


@router.get("/")
def get_filtered_paginated_products(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    categories: Optional[str] = Query(None, description="Comma-separated category names"),
    brands: Optional[str] = Query(None, description="Comma-separated brand names"),
    minPrice: Optional[float] = Query(None, ge=0, description="Minimum price"),
    maxPrice: Optional[float] = Query(None, ge=0, description="Maximum price"),
    session: SessionDep = SessionDep,
) -> ProductOutPaginated:
    """Obtener productos paginados con filtros - PÚBLICO"""
    filters = {
        "categories": categories,
        "brands": brands,
        "min_price": minPrice,
        "max_price": maxPrice,
    }
    return get_filtered_paginated_products_controller(session, page, size, filters)


@router.get("/min-max-price")
def get_max_min_price_endp(
    session: SessionDep = SessionDep
):
    """Obtener rango de precios - PÚBLICO"""
    return get_min_max_price(session)


@router.get("/get/variant")
def get_product_variants_by_product_id_endp(
    product_id: int,
    session: SessionDep = SessionDep
) -> List[ProductVariantOut]:
    """Obtener variantes de un producto - PÚBLICO"""
    return get_product_variants_by_product_id(product_id, session)


# =============================================
# ENDPOINTS PROTEGIDOS (Requieren autenticación)
# =============================================

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_product_endp(
    product: ProductCreate,
    session: SessionDep,
    admin: RequireEditorOrHigher  # Editor, Admin o SuperAdmin
):
    """Crear producto - REQUIERE AUTH (Editor+)"""
    return create_product(product, session)


@router.put("/update")
def update_product_endp(
    product_id: int,
    product: ProductUpdate,
    session: SessionDep,
    admin: RequireEditorOrHigher  # Editor, Admin o SuperAdmin
) -> ProductOut:
    """Actualizar producto - REQUIERE AUTH (Editor+)"""
    return update_product(product_id, product, session)


@router.delete("/delete")
def delete_product_endp(
    product_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher  # Solo Admin o SuperAdmin pueden eliminar
):
    """Eliminar producto - REQUIERE AUTH (Admin+)"""
    return delete_product(product_id, session)


# Endpoints protegidos para variantes
@router.post("/create/variant")
def create_product_variant_endp(
    variant: ProductVariantCreateList,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Crear variantes - REQUIERE AUTH (Editor+). Falla si ya existe."""
    return create_product_variant(variant, session)


@router.put("/upsert/variant")
def upsert_product_variant_endp(
    variant: ProductVariantCreateList,
    session: SessionDep,
    admin: RequireEditorOrHigher
):
    """Crear o actualizar variantes - REQUIERE AUTH (Editor+). Si existe, actualiza; si no, crea."""
    return upsert_product_variant(variant, session)


@router.put("/update/variant")
def update_product_variant_endp(
    variant_id: int,
    variant: ProductVariantUpdate,
    session: SessionDep,
    admin: RequireEditorOrHigher
) -> ProductVariantOut:
    """Actualizar variante - REQUIERE AUTH (Editor+)"""
    return update_product_variant(variant_id, variant, session)


@router.delete("/delete/variant")
def delete_product_variant_endp(
    variant_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher  # Solo Admin o SuperAdmin pueden eliminar
):
    """Eliminar variante - REQUIERE AUTH (Admin+)"""
    return delete_product_variant(variant_id, session)
