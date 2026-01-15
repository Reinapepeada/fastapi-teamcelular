from fastapi import APIRouter, status, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List, Optional
from fastapi import Query
import os
import pandas as pd
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
    delete_product,
    delete_product_variant,
    get_filtered_paginated_products_controller,
    get_product_variants_by_product_id,
    get_products_all,
    get_products_by_id,
    update_product,
    update_product_variant,
    upsert_product_variant,
    get_min_max_price,
)
from services.auth_s import RequireEditorOrHigher, RequireAdminOrHigher

router = APIRouter()

# =============================================
# ENDPOINTS PÚBLICOS (Sin autenticación)
# =============================================


@router.get("/get/{product_id}")
def get_product_by_id_endp(product_id: int, session: SessionDep) -> ProductOut:
    """Obtener producto por ID - PÚBLICO"""
    return get_products_by_id(product_id, session)


@router.get("/all")
def get_products_all_endp(session: SessionDep) -> List[ProductOut]:
    """Obtener todos los productos - PÚBLICO"""
    return get_products_all(session)


@router.get("/")
def get_filtered_paginated_products(
    session: SessionDep,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    categories: Optional[str] = Query(None, description="Comma-separated category names"),
    brands: Optional[str] = Query(None, description="Comma-separated brand names"),
    min_price: Optional[float] = Query(None, alias="minPrice", ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, alias="maxPrice", ge=0, description="Maximum price"),
    search: Optional[str] = Query(None, description="Texto a buscar en nombre o descripción"),
) -> ProductOutPaginated:
    """Obtener productos paginados con filtros - PÚBLICO"""
    filters = {
        "categories": categories,
        "brands": brands,
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
    }
    return get_filtered_paginated_products_controller(session, page, size, filters)


@router.get("/min-max-price")
def get_max_min_price_endp(session: SessionDep):
    """Obtener rango de precios - PÚBLICO"""
    return get_min_max_price(session)


@router.get("/get/variant")
def get_product_variants_by_product_id_endp(
    product_id: int, session: SessionDep
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
    admin: RequireEditorOrHigher,  # Editor, Admin o SuperAdmin
):
    """Crear producto - REQUIERE AUTH (Editor+)"""
    return create_product(product, session)


@router.put("/update")
def update_product_endp(
    product_id: int,
    product: ProductUpdate,
    session: SessionDep,
    admin: RequireEditorOrHigher,  # Editor, Admin o SuperAdmin
) -> ProductOut:
    """Actualizar producto - REQUIERE AUTH (Editor+)"""
    return update_product(product_id, product, session)


@router.delete("/delete")
def delete_product_endp(
    product_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher,  # Solo Admin o SuperAdmin pueden eliminar
):
    """Eliminar producto - REQUIERE AUTH (Admin+)"""
    return delete_product(product_id, session)


# Endpoints protegidos para variantes
@router.post("/create/variant")
def create_product_variant_endp(
    variant: ProductVariantCreateList, session: SessionDep, admin: RequireEditorOrHigher
):
    """Crear variantes - REQUIERE AUTH (Editor+). Falla si ya existe."""
    return create_product_variant(variant, session)


@router.put("/upsert/variant")
def upsert_product_variant_endp(
    variant: ProductVariantCreateList, session: SessionDep, admin: RequireEditorOrHigher
):
    """Crear o actualizar variantes - REQUIERE AUTH (Editor+). Si existe, actualiza; si no, crea."""
    return upsert_product_variant(variant, session)


@router.put("/update/variant")
def update_product_variant_endp(
    variant_id: int,
    variant: ProductVariantUpdate,
    session: SessionDep,
    admin: RequireEditorOrHigher,
) -> ProductVariantOut:
    """Actualizar variante - REQUIERE AUTH (Editor+)"""
    return update_product_variant(variant_id, variant, session)


@router.delete("/delete/variant")
def delete_product_variant_endp(
    variant_id: int,
    session: SessionDep,
    admin: RequireAdminOrHigher,  # Solo Admin o SuperAdmin pueden eliminar
):
    """Eliminar variante - REQUIERE AUTH (Admin+)"""
    return delete_product_variant(variant_id, session)


# =============================================
# ENDPOINT DE CARGA MASIVA
# =============================================


@router.post("/bulk-upload", status_code=status.HTTP_201_CREATED)
async def bulk_upload_products_endp(
    file: UploadFile = File(..., description="Archivo Excel (.xlsx) con productos"),
    skip_errors: bool = Query(
        True, 
        description="Si es True, continúa procesando aunque haya errores en algunas filas"
    ),
    session: SessionDep = None,
    admin: RequireEditorOrHigher = None,
):
    """
    Carga masiva de productos desde un archivo Excel - REQUIERE AUTH (Editor+)
    
    El archivo debe tener las siguientes columnas:
    - serial_number (requerido): Número de serie único
    - name (requerido): Nombre del producto
    - cost (requerido): Costo
    - retail_price (requerido): Precio de venta
    - description (opcional): Descripción
    - brand_id (opcional): ID de marca
    - category_id (opcional): ID de categoría
    - warranty_time (opcional): Tiempo de garantía
    - warranty_unit (opcional): Unidad de garantía (DAYS, MONTHS, YEARS)
    - status (opcional): Estado (ACTIVE, INACTIVE, DISCONTINUED)
    - variant_branch_id (requerido para variante): ID de sucursal
    - variant_color (opcional): Color
    - variant_size (opcional): Talla/Tamaño
    - variant_size_unit (opcional): Tipo de tamaño
    - variant_unit (opcional): Unidad
    - variant_stock (opcional): Stock inicial
    - variant_min_stock (opcional): Stock mínimo
    - image_paths (opcional): Rutas de imágenes separadas por ; (ej: C:\\imgs\\1.jpg;C:\\imgs\\2.jpg)
    
    Retorna un resumen con productos creados, errores y advertencias.
    """
    from services.bulk_upload_s import process_bulk_upload
    
    # Validar tipo de archivo
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un Excel (.xlsx o .xls)"
        )
    
    # Procesar archivo
    result = await process_bulk_upload(file, session, skip_errors)
    
    return result.to_dict()


@router.get("/bulk-upload/template")
def download_bulk_upload_template():
    """
    Descarga el template Excel para carga masiva de productos - PÚBLICO
    
    Retorna un archivo Excel con:
    - Encabezados y descripciones de todas las columnas
    - Ejemplos de datos
    - Hoja de referencia con valores válidos para enums
    """
    template_path = "template_carga_productos.xlsx"
    
    # Si no existe, crear el template
    if not os.path.exists(template_path):
        from scripts.create_template_excel import create_product_template
        create_product_template()
    
    return FileResponse(
        path=template_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="template_carga_productos.xlsx"
    )


@router.get("/bulk-upload/export")
def export_existing_products(
    session: SessionDep,
    admin: RequireEditorOrHigher = None,
):
    """
    Exporta todos los productos existentes a un archivo Excel - REQUIERE AUTH (Editor+)
    
    Descarga un archivo Excel con todos los productos actuales de la base de datos.
    Este archivo tiene el mismo formato que el template y puede ser usado para:
    - Agregar nuevos productos al final
    - Modificar productos existentes (cambios en descripción, costo, etc.)
    - Actualizar stock de variantes
    
    Al volver a subir este archivo:
    - Productos sin cambios: se omiten
    - Productos con cambios: se actualizan
    - Productos nuevos: se crean
    - Variantes sin cambios: se omiten
    - Variantes con cambios: se actualizan
    - Variantes nuevas: se crean
    """
    from services.export_products_s import export_products_to_excel
    
    filename = export_products_to_excel(session, "productos_exportados.xlsx")
    
    return FileResponse(
        path=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"productos_exportados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

