from pydantic import BaseModel
from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel, Relationship, Enum as Eenum, UniqueConstraint
from typing import List, Optional
from datetime import datetime
from enum import Enum


# =============================================
# MODELOS DE BASE DE DATOS (SQLModel)
# =============================================

class Branch(SQLModel, table=True):
    """Sucursales donde se almacenan los productos"""
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    location: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    products: List["ProductVariant"] = Relationship(back_populates="branch")


class Category(SQLModel, table=True):
    """Categorías de productos"""
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    products: List["Product"] = Relationship(back_populates="category")
    discounts: List["Discount"] = Relationship(back_populates="category")


class Brand(SQLModel, table=True):
    """Marcas de productos"""
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)

    products: List["Product"] = Relationship(back_populates="brand")


# =============================================
# ENUMS
# =============================================

class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISCONTINUED = "DISCONTINUED"


class SizeUnit(str, Enum):
    CLOTHING = "CLOTHING"      # Tallas de ropa (S, M, L)
    DIMENSIONS = "DIMENSIONS"  # Dimensiones (cm, m)
    WEIGHT = "WEIGHT"          # Peso (kg, g)
    OTHER = "OTHER"


class Unit(str, Enum):
    # Peso
    KG = "KG"
    G = "G"
    LB = "LB"
    # Longitud
    CM = "CM"
    M = "M"
    INCH = "INCH"
    # Tallas
    XS = "XS"
    S = "S"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class WarrantyUnit(str, Enum):
    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"


class Color(str, Enum):
    ROJO = "ROJO"
    AZUL = "AZUL"
    VERDE = "VERDE"
    AMARILLO = "AMARILLO"
    NARANJA = "NARANJA"
    VIOLETA = "VIOLETA"
    ROSADO = "ROSADO"
    MARRON = "MARRON"
    GRIS = "GRIS"
    BLANCO = "BLANCO"
    NEGRO = "NEGRO"
    BORDO = "BORDO"


# =============================================
# MODELOS PRINCIPALES
# =============================================

class Product(SQLModel, table=True):
    """Producto principal"""
    __table_args__ = (
        UniqueConstraint("name", "category_id", "brand_id", name="unique_product_per_category_brand"),
        CheckConstraint("cost >= 0", name="check_cost_positive"),
        CheckConstraint("retail_price >= 0", name="check_retail_price_positive"),
    )
    
    id: int | None = Field(default=None, primary_key=True)
    serial_number: str = Field(unique=True, nullable=False, index=True)
    name: str = Field(index=True, nullable=False)
    description: str | None = Field(nullable=True, default=None)
    warranty_unit: WarrantyUnit | None = Eenum(WarrantyUnit, nullable=True)
    warranty_time: int | None = Field(nullable=True)
    cost: float = Field(nullable=False)
    retail_price: float = Field(nullable=False)
    status: ProductStatus = Eenum(ProductStatus, default=ProductStatus.ACTIVE, nullable=False)
    category_id: int | None = Field(default=None, foreign_key="category.id")
    brand_id: int | None = Field(default=None, foreign_key="brand.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})

    # Relaciones
    brand: Optional["Brand"] = Relationship(back_populates="products")
    category: Optional["Category"] = Relationship(back_populates="products")
    variants: List["ProductVariant"] = Relationship(back_populates="product", cascade_delete=True)
    discounts: List["Discount"] = Relationship(back_populates="product")


class ProductVariant(SQLModel, table=True):
    """Variantes de producto (color, talla, etc.)"""
    __table_args__ = (
        UniqueConstraint("product_id", "color", "size", "size_unit", name="unique_variant_constraint"),
        CheckConstraint("stock >= 0", name="check_stock_positive"),
    )
    
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", nullable=False)
    sku: str = Field(index=True, nullable=False, unique=True)
    color: Color | None = Eenum(Color, nullable=True, default=None, index=True)
    size: str | None = Field(nullable=True, default=None, index=True)
    size_unit: SizeUnit | None = Eenum(SizeUnit, nullable=True, default=None)
    unit: Unit | None = Eenum(Unit, nullable=True)
    branch_id: int | None = Field(default=None, foreign_key="branch.id")
    stock: int = Field(default=0, index=True)
    min_stock: int = Field(default=5, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})

    # Relaciones
    product: Optional["Product"] = Relationship(back_populates="variants")
    images: List["ProductImage"] = Relationship(back_populates="variant", cascade_delete=True)
    branch: Optional["Branch"] = Relationship(back_populates="products")


class ProductImage(SQLModel, table=True):
    """Imágenes de variantes de producto"""
    id: int | None = Field(default=None, primary_key=True)
    variant_id: int = Field(foreign_key="productvariant.id", nullable=False)
    image_url: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)

    variant: Optional["ProductVariant"] = Relationship(back_populates="images")


class Discount(SQLModel, table=True):
    """Descuentos para productos o categorías"""
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    discount_type: str = Field(nullable=False)  # 'percentage' o 'fixed'
    value: float = Field(nullable=False)
    start_date: datetime | None = Field(nullable=True)
    end_date: datetime | None = Field(nullable=True)
    is_active: bool = Field(default=True)
    product_id: int | None = Field(default=None, foreign_key="product.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")

    product: Optional["Product"] = Relationship(back_populates="discounts")
    category: Optional["Category"] = Relationship(back_populates="discounts")


# =============================================
# SCHEMAS PYDANTIC - PRODUCTOS
# =============================================

class ProductVariantCreate(BaseModel):
    product_id: int
    color: Color | None = None
    size: str | None = None
    size_unit: SizeUnit | None = None
    unit: Unit | None = None
    branch_id: int | None = None
    stock: int = 0
    min_stock: int = 5
    images: list[str] | None = None

    class Config:
        from_attributes = True


class ProductVariantCreateList(BaseModel):
    variants: List[ProductVariantCreate]

    class Config:
        from_attributes = True


class ProductVariantUpdate(BaseModel):
    color: Color | None = None
    size: str | None = None
    size_unit: SizeUnit | None = None
    unit: Unit | None = None
    branch_id: int | None = None
    stock: int | None = None
    images: list[str] | None = None


class ProductImageOut(BaseModel):
    id: int
    variant_id: int
    image_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProductVariantOut(BaseModel):
    id: int
    product_id: int
    sku: str
    color: str | None
    size: str | None
    size_unit: SizeUnit | None
    unit: Unit | None
    branch_id: int | None
    stock: int
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageOut] | None = None

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    serial_number: str
    name: str
    description: str | None = None
    brand_id: int | None = None
    warranty_time: int | None = None
    warranty_unit: WarrantyUnit | None = None
    cost: float
    retail_price: float
    status: ProductStatus | None = ProductStatus.ACTIVE
    category_id: int | None = None


class ProductUpdate(BaseModel):
    serial_number: str | None = None
    name: str | None = None
    description: str | None = None
    brand_id: int | None = None
    warranty_time: int | None = None
    warranty_unit: WarrantyUnit | None = None
    cost: float | None = None
    retail_price: float | None = None
    status: ProductStatus | None = None
    category_id: int | None = None

    class Config:
        from_attributes = True


# =============================================
# SCHEMAS PYDANTIC - CATEGORÍAS
# =============================================

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None

    class Config:
        from_attributes = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================
# SCHEMAS PYDANTIC - MARCAS
# =============================================

class BrandCreate(BaseModel):
    name: str

    class Config:
        from_attributes = True


class BrandUpdate(BaseModel):
    name: str | None = None


class BrandOut(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================
# SCHEMAS PYDANTIC - SUCURSALES
# =============================================

class BranchCreate(BaseModel):
    name: str
    location: str | None = None

    class Config:
        from_attributes = True


class BranchUpdate(BaseModel):
    name: str | None = None
    location: str | None = None


class BranchOut(BaseModel):
    id: int
    name: str
    location: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================
# SCHEMAS PYDANTIC - RESPUESTAS DE PRODUCTOS
# =============================================

class ProductOut(BaseModel):
    id: int
    serial_number: str
    name: str
    description: str | None
    warranty_time: int | None
    warranty_unit: WarrantyUnit | None
    cost: float
    retail_price: float
    status: ProductStatus
    category: CategoryOut | None
    brand: BrandOut | None
    created_at: datetime
    updated_at: datetime
    variants: list[ProductVariantOut] | None = None

    class Config:
        from_attributes = True


class ProductOutSimple(BaseModel):
    """Schema simplificado para listados"""
    id: int
    name: str
    retail_price: float
    status: ProductStatus
    category: CategoryOut | None
    brand: BrandOut | None
    variants: list[ProductVariantOut] | None = None

    class Config:
        from_attributes = True


class ProductOutPaginated(BaseModel):
    """Respuesta paginada de productos"""
    products: List[ProductOutSimple]
    total: int
    page: int
    size: int
    pages: int
