from sqlmodel import select
from database.models.product import Category, CategoryCreate


def ensure_category_exists(category_id: int, session):
    category = session.get(Category, category_id)
    if not category:
        raise ValueError(f"category with id {category_id} does not exist")
    return category


def unique_constraint_category(category: CategoryCreate, session, *, exclude_id: int | None = None):
    stmt = select(Category).where(Category.name == category.name)
    if exclude_id is not None:
        stmt = stmt.where(Category.id != exclude_id)

    existing = session.exec(stmt).first()
    if existing:
        raise ValueError(f"categoria con el nombre {category.name} ya existe")
    return True


def create_category_db(category: CategoryCreate, session):
    try:
        unique_constraint_category(category, session)
        db_category = Category(name=category.name, description=category.description)
        session.add(db_category)
        session.commit()
        session.refresh(db_category)
    except Exception as e:
        session.rollback()
        raise e

    return db_category


def delete_category_db(category_id: int, session):
    try:
        db_category = ensure_category_exists(category_id, session)
        session.delete(db_category)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def update_category_db(category_id: int, category: CategoryCreate, session):
    try:
        db_category = ensure_category_exists(category_id, session)
        unique_constraint_category(category, session, exclude_id=category_id)
        for key, value in category.model_dump(exclude_unset=True).items():
            setattr(db_category, key, value)
        session.commit()
        session.refresh(db_category)
    except Exception as e:
        session.rollback()
        raise e
    return db_category


def get_categories_all_db(session):
    try:
        categorys = session.exec(select(Category)).all()
        return categorys
    except Exception as e:
        session.rollback()
        raise e
