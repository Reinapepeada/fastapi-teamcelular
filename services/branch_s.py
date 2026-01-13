from sqlmodel import select
from database.models.product import Branch, BranchCreate


def ensure_branch_exists(branch_id: int, session):
    branch = session.get(Branch, branch_id)
    if not branch:
        raise ValueError(f"Branch with id {branch_id} does not exist")
    return branch


def unique_constraint_branch(branch: BranchCreate, session, *, exclude_id: int | None = None):
    stmt = select(Branch).where(Branch.name == branch.name)
    if exclude_id is not None:
        stmt = stmt.where(Branch.id != exclude_id)

    existing = session.exec(stmt).first()
    if existing:
        raise ValueError(f"Local con nombre '{branch.name}' ya existe")
    return True


def create_branch_db(branch: BranchCreate, session):
    try:
        unique_constraint_branch(branch, session)
        db_branch = Branch(
            name=branch.name,
            location=branch.location,
        )
        session.add(db_branch)
        session.commit()
        session.refresh(db_branch)
    except Exception as e:
        session.rollback()
        raise e

    return db_branch


def delete_branch_db(branch_id: int, session):
    try:
        db_branch = ensure_branch_exists(branch_id, session)
        session.delete(db_branch)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


def update_branch_db(branch_id: int, branch: BranchCreate, session):
    try:
        db_branch = ensure_branch_exists(branch_id, session)
        unique_constraint_branch(branch, session, exclude_id=branch_id)
        for key, value in branch.model_dump(exclude_unset=True).items():
            setattr(db_branch, key, value)
        session.commit()
        session.refresh(db_branch)
    except Exception as e:
        session.rollback()
        raise e
    return db_branch


def get_branches_all(session):
    try:
        branches = session.exec(select(Branch)).all()
        return branches
    except Exception as e:
        session.rollback()
        raise e
