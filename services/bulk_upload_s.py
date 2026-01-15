"""
Servicio para carga masiva de productos desde Excel
"""
import os
import base64
from typing import List, Dict, Any, Tuple
import pandas as pd
from fastapi import UploadFile, HTTPException
from sqlmodel import Session
from database.models.product import (
    ProductCreate,
    ProductVariantCreate,
    ProductStatus,
    WarrantyUnit,
    Color,
    SizeUnit,
    Unit,
)
from services.product_s import (
    create_product_service,
    create_product_variant_service,
    product_exists_serial,
    ensure_product_exists_serial,
    find_existing_variant,
)
from services.brand_s import ensure_brand_exists
from services.category_s import ensure_category_exists
from services.branch_s import ensure_branch_exists
from database.models.product import Product, ProductImage


class BulkUploadResult:
    """Resultado de la carga masiva"""
    def __init__(self):
        self.total_rows = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.updated_products = 0
        self.updated_variants = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
        self.created_products: List[str] = []
        self.created_variants: List[str] = []
        self.skipped_products: List[str] = []
        self.updated_products_list: List[str] = []
        self.updated_variants_list: List[str] = []
    
    def to_dict(self):
        return {
            "total_rows": self.total_rows,
            "successful": self.successful,
            "failed": self.failed,
            "skipped": self.skipped,
            "updated_products": self.updated_products,
            "updated_variants": self.updated_variants,
            "errors": self.errors,
            "warnings": self.warnings,
            "created_products": self.created_products,
            "created_variants": self.created_variants,
            "skipped_products": self.skipped_products,
            "updated_products_list": self.updated_products_list,
            "updated_variants_list": self.updated_variants_list,
        }


def validate_excel_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Valida que el Excel tenga las columnas requeridas"""
    required_columns = [
        "serial_number",
        "name",
        "cost",
        "retail_price",
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, [f"Columnas faltantes: {', '.join(missing_columns)}"]
    
    return True, []


def parse_warranty_unit(value: Any) -> WarrantyUnit | None:
    """Parsea la unidad de garantía"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    value_str = str(value).strip().upper()
    
    try:
        return WarrantyUnit(value_str)
    except ValueError:
        return None


def parse_product_status(value: Any) -> ProductStatus:
    """Parsea el estado del producto"""
    if pd.isna(value) or value == "" or value is None:
        return ProductStatus.ACTIVE
    
    value_str = str(value).strip().upper()
    
    try:
        return ProductStatus(value_str)
    except ValueError:
        return ProductStatus.ACTIVE


def parse_color(value: Any) -> Color | None:
    """Parsea el color de la variante"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    value_str = str(value).strip().upper()
    
    try:
        return Color(value_str)
    except ValueError:
        return None


def parse_size_unit(value: Any) -> SizeUnit | None:
    """Parsea la unidad de tamaño"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    value_str = str(value).strip().upper()
    
    try:
        return SizeUnit(value_str)
    except ValueError:
        return None


def parse_unit(value: Any) -> Unit | None:
    """Parsea la unidad"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    value_str = str(value).strip().upper()
    
    try:
        return Unit(value_str)
    except ValueError:
        return None


def parse_int_or_none(value: Any) -> int | None:
    """Convierte a entero o None"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_float_or_none(value: Any, default: float | None = None) -> float | None:
    """Convierte a float o None"""
    if pd.isna(value) or value == "" or value is None:
        return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_string_or_none(value: Any) -> str | None:
    """Convierte a string o None"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    return str(value).strip()


def parse_image_paths(value: Any) -> List[str] | None:
    """Parsea las rutas de imágenes separadas por punto y coma"""
    if pd.isna(value) or value == "" or value is None:
        return None
    
    paths_str = str(value).strip()
    
    if not paths_str:
        return None
    
    # Dividir por punto y coma
    paths = [p.strip() for p in paths_str.split(';') if p.strip()]
    
    return paths if paths else None


def image_to_base64(image_path: str) -> str | None:
    """Convierte una imagen a base64 data URL"""
    try:
        if not os.path.exists(image_path):
            return None
        
        # Determinar el tipo MIME según la extensión
        ext = os.path.splitext(image_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
        }
        
        mime_type = mime_types.get(ext, 'image/jpeg')
        
        # Leer y codificar la imagen
        with open(image_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Crear data URL
        data_url = f"data:{mime_type};base64,{encoded_string}"
        
        return data_url
    except Exception as e:
        print(f"Error convirtiendo imagen {image_path}: {str(e)}")
        return None


def product_has_changes(existing_product: Product, new_data: ProductCreate) -> bool:
    """
    Compara un producto existente con nuevos datos para detectar cambios
    Solo compara campos que NO son primary key ni serial_number
    """
    changes = []
    
    # Comparar campos actualizables
    if existing_product.name != new_data.name:
        changes.append(f"name: '{existing_product.name}' -> '{new_data.name}'")
    
    if existing_product.description != new_data.description:
        changes.append(f"description modificada")
    
    if existing_product.brand_id != new_data.brand_id:
        changes.append(f"brand_id: {existing_product.brand_id} -> {new_data.brand_id}")
    
    if existing_product.category_id != new_data.category_id:
        changes.append(f"category_id: {existing_product.category_id} -> {new_data.category_id}")
    
    if existing_product.warranty_time != new_data.warranty_time:
        changes.append(f"warranty_time: {existing_product.warranty_time} -> {new_data.warranty_time}")
    
    if existing_product.warranty_unit != new_data.warranty_unit:
        changes.append(f"warranty_unit modificado")
    
    if existing_product.cost != new_data.cost:
        changes.append(f"cost: {existing_product.cost} -> {new_data.cost}")
    
    if existing_product.retail_price != new_data.retail_price:
        changes.append(f"retail_price: {existing_product.retail_price} -> {new_data.retail_price}")
    
    if existing_product.status != new_data.status:
        changes.append(f"status: {existing_product.status} -> {new_data.status}")
    
    return len(changes) > 0, changes


def update_product_from_data(product: Product, new_data: ProductCreate, session: Session):
    """Actualiza un producto existente con los nuevos datos"""
    product.name = new_data.name
    product.description = new_data.description
    product.brand_id = new_data.brand_id
    product.category_id = new_data.category_id
    product.warranty_time = new_data.warranty_time
    product.warranty_unit = new_data.warranty_unit
    product.cost = new_data.cost
    product.retail_price = new_data.retail_price
    product.status = new_data.status
    
    session.add(product)
    session.commit()
    session.refresh(product)
    
    return product


def variant_has_changes(existing_variant, new_data: ProductVariantCreate) -> bool:
    """
    Compara una variante existente con nuevos datos para detectar cambios
    """
    changes = []
    
    if existing_variant.branch_id != new_data.branch_id:
        changes.append(f"branch_id: {existing_variant.branch_id} -> {new_data.branch_id}")
    
    if existing_variant.stock != new_data.stock:
        changes.append(f"stock: {existing_variant.stock} -> {new_data.stock}")
    
    if existing_variant.min_stock != new_data.min_stock:
        changes.append(f"min_stock: {existing_variant.min_stock} -> {new_data.min_stock}")
    
    return len(changes) > 0, changes


def update_variant_from_data(variant, new_data: ProductVariantCreate, session: Session):
    """Actualiza una variante existente con los nuevos datos"""
    variant.branch_id = new_data.branch_id
    variant.stock = new_data.stock
    variant.min_stock = new_data.min_stock
    
    # Actualizar imágenes si se proporcionan nuevas
    if new_data.images:
        # Eliminar imágenes anteriores
        for img in variant.images:
            session.delete(img)
        
        # Agregar nuevas imágenes
        for image_url in new_data.images:
            new_image = ProductImage(variant_id=variant.id, image_url=image_url)
            session.add(new_image)
    
    session.add(variant)
    session.commit()
    session.refresh(variant)
    
    return variant


async def process_bulk_upload(
    file: UploadFile,
    session: Session,
    skip_errors: bool = True
) -> BulkUploadResult:
    """
    Procesa un archivo Excel para carga masiva de productos
    
    Args:
        file: Archivo Excel subido
        session: Sesión de base de datos
        skip_errors: Si es True, continúa procesando aunque haya errores en algunas filas
    
    Returns:
        BulkUploadResult con los resultados del procesamiento
    """
    result = BulkUploadResult()
    
    try:
        # Leer el archivo Excel
        contents = await file.read()
        df = pd.read_excel(contents, sheet_name='Productos')
        
        # Saltar las filas de descripción (fila 2)
        if len(df) > 0 and 'Número de serie único' in str(df.iloc[0].values):
            df = df.iloc[1:]
        
        # Resetear índices
        df = df.reset_index(drop=True)
        
        # Validar estructura
        is_valid, errors = validate_excel_structure(df)
        if not is_valid:
            raise HTTPException(status_code=400, detail={"errors": errors})
        
        result.total_rows = len(df)
        
        # Procesar cada fila
        for idx, row in df.iterrows():
            row_num = idx + 4  # +4 porque empezamos en fila 1, hay header, descripción, y ejemplos
            
            try:
                # Validar campos requeridos
                serial_number = parse_string_or_none(row.get('serial_number'))
                name = parse_string_or_none(row.get('name'))
                cost = parse_float_or_none(row.get('cost'))
                retail_price = parse_float_or_none(row.get('retail_price'))
                
                if not serial_number:
                    raise ValueError("serial_number es requerido")
                if not name:
                    raise ValueError("name es requerido")
                if cost is None:
                    raise ValueError("cost es requerido")
                if retail_price is None:
                    raise ValueError("retail_price es requerido")
                
                # Validar IDs de relaciones
                brand_id = parse_int_or_none(row.get('brand_id'))
                category_id = parse_int_or_none(row.get('category_id'))
                
                if brand_id is not None:
                    try:
                        ensure_brand_exists(brand_id, session)
                    except ValueError as e:
                        result.warnings.append({
                            "row": row_num,
                            "field": "brand_id",
                            "message": str(e)
                        })
                        brand_id = None
                
                if category_id is not None:
                    try:
                        ensure_category_exists(category_id, session)
                    except ValueError as e:
                        result.warnings.append({
                            "row": row_num,
                            "field": "category_id",
                            "message": str(e)
                        })
                        category_id = None
                
                # Crear o obtener producto
                product_data = ProductCreate(
                    serial_number=serial_number,
                    name=name,
                    description=parse_string_or_none(row.get('description')),
                    brand_id=brand_id,
                    category_id=category_id,
                    warranty_time=parse_int_or_none(row.get('warranty_time')),
                    warranty_unit=parse_warranty_unit(row.get('warranty_unit')),
                    cost=cost,
                    retail_price=retail_price,
                    status=parse_product_status(row.get('status')),
                )
                
                # Verificar si el producto ya existe
                existing_product = None
                if product_exists_serial(serial_number, session):
                    existing_product = ensure_product_exists_serial(serial_number, session)
                    
                    # Detectar si hay cambios
                    has_changes, changes = product_has_changes(existing_product, product_data)
                    
                    if has_changes:
                        # Actualizar producto existente
                        product = update_product_from_data(existing_product, product_data, session)
                        result.updated_products += 1
                        result.updated_products_list.append(serial_number)
                        result.warnings.append({
                            "row": row_num,
                            "message": f"Producto {serial_number} actualizado: {', '.join(changes[:3])}"
                        })
                    else:
                        # Sin cambios, usar producto existente
                        product = existing_product
                        result.skipped += 1
                        result.skipped_products.append(serial_number)
                else:
                    # Crear nuevo producto
                    product = create_product_service(product_data, session)
                    result.created_products.append(serial_number)
                
                # Crear variante si se especificaron datos de variante
                variant_branch_id = parse_int_or_none(row.get('variant_branch_id'))
                
                if variant_branch_id is not None:
                    try:
                        ensure_branch_exists(variant_branch_id, session)
                    except ValueError as e:
                        raise ValueError(f"Branch ID inválido: {str(e)}")
                    
                    # Procesar imágenes
                    image_paths = parse_image_paths(row.get('image_paths'))
                    image_urls = []
                    
                    # Solo procesar imágenes si NO es una marca de "imágenes ya cargadas"
                    if image_paths and not any('[' in str(p) and 'imágenes ya cargadas' in str(p) for p in image_paths):
                        for img_path in image_paths:
                            base64_url = image_to_base64(img_path)
                            if base64_url:
                                image_urls.append(base64_url)
                            else:
                                result.warnings.append({
                                    "row": row_num,
                                    "field": "image_paths",
                                    "message": f"No se pudo cargar la imagen: {img_path}"
                                })
                    
                    variant_data = ProductVariantCreate(
                        product_id=product.id,
                        branch_id=variant_branch_id,
                        color=parse_color(row.get('variant_color')),
                        size=parse_string_or_none(row.get('variant_size')),
                        size_unit=parse_size_unit(row.get('variant_size_unit')),
                        unit=parse_unit(row.get('variant_unit')),
                        stock=parse_int_or_none(row.get('variant_stock')) or 0,
                        min_stock=parse_int_or_none(row.get('variant_min_stock')) or 5,
                        images=image_urls if image_urls else None,
                    )
                    
                    # Verificar si la variante ya existe
                    existing_variant = find_existing_variant(
                        product.id,
                        variant_data.color,
                        variant_data.size,
                        variant_data.size_unit,
                        variant_data.unit,
                        session
                    )
                    
                    if existing_variant:
                        # Detectar si hay cambios en la variante
                        has_variant_changes, variant_changes = variant_has_changes(existing_variant, variant_data)
                        
                        if has_variant_changes or (image_urls and len(image_urls) > 0):
                            # Actualizar variante existente
                            variant = update_variant_from_data(existing_variant, variant_data, session)
                            result.updated_variants += 1
                            result.updated_variants_list.append(existing_variant.sku)
                            result.warnings.append({
                                "row": row_num,
                                "message": f"Variante {existing_variant.sku} actualizada"
                            })
                        else:
                            # Sin cambios
                            result.warnings.append({
                                "row": row_num,
                                "message": f"Variante {existing_variant.sku} ya existe sin cambios, se omite"
                            })
                    else:
                        # Crear nueva variante
                        variant = create_product_variant_service(variant_data, session)
                        result.created_variants.append(variant.sku)
                
                result.successful += 1
                
            except Exception as e:
                result.failed += 1
                error_detail = {
                    "row": row_num,
                    "serial_number": parse_string_or_none(row.get('serial_number')),
                    "error": str(e)
                }
                result.errors.append(error_detail)
                
                if not skip_errors:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error en fila {row_num}: {str(e)}"
                    )
        
        return result
        
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al leer el archivo Excel: {str(e)}"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando archivo: {str(e)}"
        )
