"""
Servicio de productos - Operaciones de base de datos
"""
from typing import List
import uuid
from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from database.models.product import (
    Branch,
    Brand,
    Category,
    Product,
    ProductImage,
    ProductUpdate,
    ProductVariant,
    ProductVariantUpdate,
)
from services.branch_s import ensure_branch_exists
from services.brand_s import ensure_brand_exists


# =============================================
# VALIDACIONES
# =============================================

def ensure_category_exists(category_id: int, session):
    """Verifica que la categoría exista"""
    if category_id is None:
        return None
    category = session.exec(select(Category).where(Category.id == category_id)).scalar()
    if not category:
        raise ValueError(f"Categoría con id {category_id} no existe")
    return category


def ensure_product_exists_serial(product_serial: str, session):
    """Verifica que el producto exista por serial"""
    product = session.exec(
        select(Product).where(Product.serial_number == product_serial)
    ).scalar()
    if not product:
        raise ValueError(f"Producto con serial {product_serial} no existe")
    return product


def ensure_product_exists_id(product_id: int, session):
    """Verifica que el producto exista por ID"""
    product = session.exec(select(Product).where(Product.id == product_id)).scalar()
    if not product:
        raise ValueError(f"Producto con id {product_id} no existe")
    return product


def product_exists_serial(product_serial: str, session) -> bool:
    """Retorna True si el producto existe por serial"""
    product = session.exec(
        select(Product).where(Product.serial_number == product_serial)
    ).scalar()
    return product is not None


def ensure_product_variant_exists(variant_id: int, session):
    """Verifica que la variante de producto exista"""
    variant = session.exec(
        select(ProductVariant).where(ProductVariant.id == variant_id)
    ).scalar()
    if not variant:
        raise ValueError(f"Variante de producto con id {variant_id} no existe")
    return variant


def find_existing_variant(product_id, color, size, size_unit, unit, session):
    """Busca una variante existente con las mismas características.
    Maneja correctamente comparaciones con NULL en SQL.
    """
    from sqlalchemy import and_, or_
    
    # Construir condiciones dinámicamente para manejar NULL correctamente
    conditions = [ProductVariant.product_id == product_id]
    
    # Para cada campo opcional, usar IS NULL si es None, o == si tiene valor
    if color is None:
        conditions.append(ProductVariant.color.is_(None))
    else:
        conditions.append(ProductVariant.color == color)
    
    if size is None:
        conditions.append(ProductVariant.size.is_(None))
    else:
        conditions.append(ProductVariant.size == size)
    
    if size_unit is None:
        conditions.append(ProductVariant.size_unit.is_(None))
    else:
        conditions.append(ProductVariant.size_unit == size_unit)
    
    if unit is None:
        conditions.append(ProductVariant.unit.is_(None))
    else:
        conditions.append(ProductVariant.unit == unit)
    
    variant = session.exec(
        select(ProductVariant).where(and_(*conditions))
    ).first()
    return variant


def ensure_unique_constraints_product_variant(product_id, color, size, size_unit, unit, session):
    """Verifica unicidad de variante"""
    variant = find_existing_variant(product_id, color, size, size_unit, unit, session)
    if variant:
        raise ValueError("Ya existe una variante con las mismas características de color, tamaño y unidad.")
    return variant


# =============================================
# GENERADORES
# =============================================

def generate_sku(product_name: str, category_id: int, brand_id: int) -> str:
    """Genera un SKU único para la variante"""
    unique_id = uuid.uuid4().hex[:8].upper()
    cat_id = category_id if category_id else 0
    brand = brand_id if brand_id else 0
    name_part = product_name[:4].upper() if len(product_name) >= 4 else product_name.upper()
    return f"{name_part}-{cat_id:02d}-{brand:02d}-{unique_id}"


# =============================================
# CRUD PRODUCTOS
# =============================================

def create_product_db(product, session):
    """Crea un nuevo producto"""
    try:
        # Validar existencia de categoría y marca si se proporcionan
        if product.category_id:
            ensure_category_exists(product.category_id, session)
        if product.brand_id:
            ensure_brand_exists(product.brand_id, session)

        # Verificar si el producto ya existe
        if product_exists_serial(product.serial_number, session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto con serial {product.serial_number} ya existe.",
            )

        # Crear producto
        db_product = Product(
            serial_number=product.serial_number,
            name=product.name,
            description=product.description,
            brand_id=product.brand_id,
            warranty_unit=product.warranty_unit,
            warranty_time=product.warranty_time,
            cost=product.cost,
            retail_price=product.retail_price,
            status=product.status,
            category_id=product.category_id,
        )
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear producto: {str(e)}"
        )


def get_products_all_db(session):
    """Obtiene todos los productos"""
    try:
        products = session.exec(select(Product)).scalars().all()
        return products
    except Exception as e:
        session.rollback()
        raise e


def get_product_by_id_db(session, product_id: int):
    """Obtiene un producto por ID"""
    try:
        db_product = ensure_product_exists_id(product_id, session)
        return db_product
    except Exception as e:
        session.rollback()
        raise e


def update_product_db(product_id: int, product: ProductUpdate, session):
    """Actualiza un producto"""
    try:
        db_product = ensure_product_exists_id(product_id, session)
        for key, value in product.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)
        session.commit()
        session.refresh(db_product)
        return db_product
    except Exception as e:
        session.rollback()
        raise e


def delete_product_db(product_id: int, session):
    """Elimina un producto"""
    try:
        db_product = ensure_product_exists_id(product_id, session)
        session.delete(db_product)
        session.commit()
        return {"msg": "Producto eliminado correctamente"}
    except Exception as e:
        session.rollback()
        raise e


def fetch_products_with_filters(session, page: int, size: int, filters: dict):
    """Obtiene productos con filtros y paginación"""
    query = select(Product).options(
        selectinload(Product.category),
        selectinload(Product.brand),
        selectinload(Product.variants)
    )

    # Aplicar filtros
    if filters.get("categories"):
        category_names = [str(name) for name in filters["categories"].split(",")]
        query = query.join(Product.category).where(Category.name.in_(category_names))

    if filters.get("brands"):
        brand_names = [str(name) for name in filters["brands"].split(",")]
        query = query.join(Product.brand).where(Brand.name.in_(brand_names))

    if filters.get("min_price") is not None or filters.get("max_price") is not None:
        min_price = filters.get("min_price", 0)
        max_price = filters.get("max_price", float('inf'))
        query = query.where(Product.retail_price.between(min_price, max_price))

    # Contar total
    total_query = select(func.count()).select_from(query.subquery())
    total = session.execute(total_query).scalar()

    # Obtener productos paginados
    result = session.execute(
        query.offset((page - 1) * size).limit(size)
    )
    products = result.scalars().all()

    return products, total


def get_max_min_price_db(session):
    """Obtiene precio máximo y mínimo"""
    try:
        result = session.exec(
            select(func.max(Product.retail_price), func.min(Product.retail_price))
        ).one()
        max_price, min_price = result
        return max_price, min_price
    except Exception as e:
        session.rollback()
        raise e


# =============================================
# CRUD VARIANTES
# =============================================

def create_product_variant_db(product_variants, session):
    """Crea variantes para un producto existente (falla si ya existe)"""
    try:
        db_variants = []
        for variant in product_variants.variants:
            # Validar existencia de producto
            db_product = ensure_product_exists_id(variant.product_id, session)
            
            # Validar sucursal (es obligatoria)
            ensure_branch_exists(variant.branch_id, session)

            # Validar que NO exista (solo crear, no actualizar)
            ensure_unique_constraints_product_variant(
                variant.product_id,
                variant.color,
                variant.size,
                variant.size_unit,
                variant.unit,
                session,
            )

            # Generar SKU
            sku = generate_sku(
                product_name=db_product.name,
                category_id=db_product.category_id,
                brand_id=db_product.brand_id,
            )

            # Crear variante nueva
            db_variant = ProductVariant(
                product_id=variant.product_id,
                sku=sku,
                color=variant.color,
                size=variant.size,
                size_unit=variant.size_unit,
                unit=variant.unit,
                branch_id=variant.branch_id,
                stock=variant.stock,
                min_stock=variant.min_stock,
            )
            session.add(db_variant)
            session.commit()
            session.refresh(db_variant)

            # Agregar imágenes si existen
            if variant.images:
                persist_product_images(variant.images, db_variant.id, session)
            
            db_variants.append(db_variant)

        return db_variants

    except ValueError as e:
        session.rollback()
        raise ValueError(str(e))
    except Exception as e:
        session.rollback()
        # No exponer detalles internos de la BD en producción
        error_msg = str(e)
        if "ForeignKeyViolation" in error_msg or "foreign key" in error_msg.lower():
            raise ValueError("Error de referencia: Verifica que el producto, sucursal y otros IDs existan")
        raise ValueError(f"Error al crear variantes de producto")


def upsert_product_variant_db(product_variants, session):
    """Crea o actualiza variantes (upsert) - Si existe, actualiza; si no, crea"""
    try:
        db_variants = []
        for variant in product_variants.variants:
            # Validar existencia de producto
            db_product = ensure_product_exists_id(variant.product_id, session)
            
            # Validar sucursal (es obligatoria)
            ensure_branch_exists(variant.branch_id, session)

            # Buscar si ya existe una variante con las mismas características
            existing_variant = find_existing_variant(
                variant.product_id,
                variant.color,
                variant.size,
                variant.size_unit,
                variant.unit,
                session,
            )

            if existing_variant:
                # ACTUALIZAR variante existente
                existing_variant.branch_id = variant.branch_id
                existing_variant.stock = variant.stock
                existing_variant.min_stock = variant.min_stock
                session.commit()
                session.refresh(existing_variant)
                
                # Agregar imágenes si existen
                if variant.images:
                    persist_product_images(variant.images, existing_variant.id, session)
                
                db_variants.append(existing_variant)
            else:
                # CREAR variante nueva
                sku = generate_sku(
                    product_name=db_product.name,
                    category_id=db_product.category_id,
                    brand_id=db_product.brand_id,
                )

                db_variant = ProductVariant(
                    product_id=variant.product_id,
                    sku=sku,
                    color=variant.color,
                    size=variant.size,
                    size_unit=variant.size_unit,
                    unit=variant.unit,
                    branch_id=variant.branch_id,
                    stock=variant.stock,
                    min_stock=variant.min_stock,
                )
                session.add(db_variant)
                session.commit()
                session.refresh(db_variant)

                # Agregar imágenes si existen
                if variant.images:
                    persist_product_images(variant.images, db_variant.id, session)
                
                db_variants.append(db_variant)

        return db_variants

    except ValueError as e:
        session.rollback()
        raise ValueError(str(e))
    except Exception as e:
        session.rollback()
        error_msg = str(e)
        if "ForeignKeyViolation" in error_msg or "foreign key" in error_msg.lower():
            raise ValueError("Error de referencia: Verifica que el producto, sucursal y otros IDs existan")
        raise ValueError(f"Error en upsert de variantes de producto")


def get_product_variants_by_product_id_db(product_id: int, session):
    """Obtiene variantes por ID de producto"""
    try:
        db_variants = session.exec(
            select(ProductVariant).where(ProductVariant.product_id == product_id)
        ).all()
        return db_variants
    except Exception as e:
        session.rollback()
        raise e


def update_product_variant_db(variant_id: int, variant: ProductVariantUpdate, session):
    """Actualiza una variante"""
    try:
        db_variant = ensure_product_variant_exists(variant_id, session)
        for key, value in variant.model_dump(exclude_unset=True).items():
            if key != "images":  # Manejar imágenes por separado
                setattr(db_variant, key, value)
        session.commit()
        session.refresh(db_variant)
        return db_variant
    except Exception as e:
        session.rollback()
        raise e


def delete_product_variant_db(variant_id: int, session):
    """Elimina una variante"""
    try:
        db_variant = ensure_product_variant_exists(variant_id, session)
        session.delete(db_variant)
        session.commit()
        return {"msg": "Variante eliminada correctamente"}
    except Exception as e:
        session.rollback()
        raise e


# =============================================
# IMÁGENES Y STOCK
# =============================================

def persist_product_images(images: List[str], variant_id: int, session):
    """Guarda imágenes de una variante"""
    try:
        ensure_product_variant_exists(variant_id, session)
        for url_img in images:
            session.add(ProductImage(image_url=str(url_img), variant_id=variant_id))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def add_stock_product_variant(variant_id: int, quantity: int, session):
    """Añade stock a una variante"""
    try:
        db_variant = ensure_product_variant_exists(variant_id, session)
        db_variant.stock += quantity
        session.commit()
        return db_variant
    except Exception as e:
        session.rollback()
        raise e


def reduce_stock_product_variant(variant_id: int, quantity: int, session):
    """Reduce stock de una variante"""
    try:
        db_variant = ensure_product_variant_exists(variant_id, session)
        if db_variant.stock < quantity:
            raise ValueError("No hay suficiente stock")
        db_variant.stock -= quantity
        session.commit()
        return db_variant
    except Exception as e:
        session.rollback()
        raise e
