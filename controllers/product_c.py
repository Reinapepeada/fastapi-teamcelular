
from fastapi import HTTPException
from sqlmodel import Session
# modelos de las tablas
from database.models.product import (
    BranchCreate, 
    BrandCreate, 
    CategoryCreate, 
    ProductCreate, 
    ProductUpdate, 
    ProductVariantCreateList, 
    ProductVariantUpdate
)

from services.product_s import (
    create_product_db,
    create_product_variant_db,
    delete_product_db,
    delete_product_variant_db,
    fetch_products_with_filters,
    get_max_min_price_db,
    get_product_by_id_db,
    get_product_variants_by_product_id_db,
    get_products_all_db,
    update_product_db,
    update_product_variant_db
)

# Crud operations for auxiliary tables
from services.branch_s import create_branch_db, delete_branch_db, get_branches_all, update_branch_db
from services.brand_s import create_brand_db, delete_brand_db, get_brands_all, update_brand_db
from services.category_s import delete_category_db, get_categories_all_db, update_category_db, create_category_db


def create_product(product: ProductCreate, session: Session):
    try:
        return create_product_db(product, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor al crear producto")

def get_products_all(session: Session):
    try:
        return get_products_all_db(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener productos")


def get_filtered_paginated_products_controller(
    session: Session, page: int, size: int, filters: dict
):
    """Obtiene productos filtrados y paginados."""
    products, total_count = fetch_products_with_filters(session, page, size, filters)
    return {
        "products": products,
        "total": total_count,
        "page": page,
        "size": size,
        "pages": (total_count + size - 1) // size,
    }

def get_min_max_price(session: Session):
    try:
        max_price, min_price = get_max_min_price_db(session)
        return {"max": str(max_price), "min": str(min_price)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener rango de precios")

def get_products_by_id(product_id: int, session: Session):
    try:
        prod = get_product_by_id_db(session, product_id)
        return prod
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener producto")
    
def update_product(product_id: int, product: ProductUpdate, session: Session):
    try:
        product_variants = update_product_db(product_id, product, session)
        return product_variants
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar producto")

def delete_product(product_id: int, session: Session):
    try:
        return delete_product_db(product_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar producto")
    
def create_product_variant(variant: ProductVariantCreateList, session: Session):
    try:
        return create_product_variant_db(variant, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # No exponer detalles internos en producción
        raise HTTPException(status_code=500, detail="Error interno del servidor al crear variantes")

def get_product_variants_by_product_id(product_id: int, session: Session):
    try:
        return get_product_variants_by_product_id_db(product_id, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener variantes")

def update_product_variant(variant_id: int, variant: ProductVariantUpdate, session: Session):
    try:
        product_variants = update_product_variant_db(variant_id, variant, session)
        return product_variants
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar variante")

def delete_product_variant(variant_id: int, session: Session):
    try:
        return delete_product_variant_db(variant_id, session) 
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar variante")



# branches controller
def create_branch(branch: BranchCreate, session: Session):
    try:
        branch = create_branch_db(branch, session)
        return branch
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear sucursal")

def get_branches(session: Session):
    try:
        return get_branches_all(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener sucursales")

def delete_branch(branch_id: int, session: Session):
    try:
        delete_branch_db(branch_id, session)
        return {"msg": "Branch deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar sucursal")

def update_branch(branch_id: int, branch: BranchCreate, session: Session):
    try:
        branch = update_branch_db(branch_id, branch, session)
        return branch
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar sucursal")
    
#  brand controller
def create_brand(brand: BrandCreate, session: Session):
    try:
        brand = create_brand_db(brand, session)
        return brand
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear marca")

def get_brands(session: Session):
    try:
        return get_brands_all(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener marcas")

def delete_brand(brand_id: int, session: Session):
    try:
        delete_brand_db(brand_id, session)
        return {"msg": "Brand deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar marca")

def update_brand(brand_id: int, brand: BrandCreate, session: Session):
    try:
        brand = update_brand_db(brand_id, brand, session)
        return brand
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar marca")


# category controller

def create_category(category: CategoryCreate, session: Session):
    try:
        category = create_category_db(category, session)
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al crear categoría")

def get_categories(session: Session):
    try:
        return get_categories_all_db(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener categorías")

def delete_category(category_id: int, session: Session):
    try:
        delete_category_db(category_id, session)
        return {"msg": "Category deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al eliminar categoría")

def update_category(category_id: int, category: CategoryCreate, session: Session):
    try:
        category = update_category_db(category_id, category, session)
        return category
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al actualizar categoría")