from sqlmodel import select
from database.models.product import Brand, BrandCreate


def ensure_brand_exists(brand_id: int, session):
    brand = session.get(Brand, brand_id)
    if not brand:
        raise ValueError(f"brand with id {brand_id} does not exist")
    return brand


def unique_constraint_brand(brand: BrandCreate, session, *, exclude_id: int | None = None):
    stmt = select(Brand).where(Brand.name == brand.name)
    if exclude_id is not None:
        stmt = stmt.where(Brand.id != exclude_id)

    existing = session.exec(stmt).first()
    if existing:
        raise ValueError(f"marca con el nombre '{brand.name}' ya existe")
    return True


def create_brand_db(brand: BrandCreate, session):
    try:
        unique_constraint_brand(brand, session)
        db_brand = Brand(
            name=brand.name,
        )
        session.add(db_brand)
        session.commit()
        session.refresh(db_brand)
    except Exception as e:
        session.rollback()
        raise e

    return db_brand


def delete_brand_db(brand_id: int, session):
    try:
        db_brand = ensure_brand_exists(brand_id, session)
        session.delete(db_brand)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def update_brand_db(brand_id: int, brand: BrandCreate, session):
    try:
        db_brand = ensure_brand_exists(brand_id, session)
        unique_constraint_brand(brand, session, exclude_id=brand_id)
        for key, value in brand.model_dump(exclude_unset=True).items():
            setattr(db_brand, key, value)
        session.commit()
        session.refresh(db_brand)
    except Exception as e:
        session.rollback()
        raise e
    return db_brand


def get_brands_all(session):
    try:
        brands = session.exec(select(Brand)).all()
        return brands
    except Exception as e:
        session.rollback()
        raise e
