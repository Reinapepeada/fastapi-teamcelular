import os
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "sqlite:///./tests_bootstrap.db")

from database.models.product import Brand, Category, Product, ProductStatus, WarrantyUnit
from services.product_s import fetch_products_with_filters


@pytest.fixture
def session(tmp_path: Path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'catalog_test.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        # "Modulos " se guardo con espacio final en produccion y dejaba sus
        # productos fuera de todo filtro por categoria.
        s.add(Category(id=1, name="Modulos ", description="Samsung"))
        s.add(Category(id=2, name="Cables", description="Cables"))
        s.add(Brand(id=1, name="Samsung"))
        for pid, sn, name, cat in ((1, "MOD-1", "Modulo A", 1), (2, "CAB-1", "Cable A", 2)):
            s.add(
                Product(
                    id=pid,
                    serial_number=sn,
                    name=name,
                    category_id=cat,
                    brand_id=1,
                    cost=1000.0,
                    retail_price=2000.0,
                    warranty_unit=WarrantyUnit.DAYS,
                    warranty_time=90,
                    status=ProductStatus.ACTIVE,
                )
            )
        s.commit()
        yield s


def test_categoria_con_espacio_final_sigue_filtrando(session):
    products, total = fetch_products_with_filters(session, 1, 10, {"categories": "Modulos"})
    assert [p.name for p in products] == ["Modulo A"]
    assert total == 1


def test_categoria_limpia_no_se_rompe(session):
    products, _ = fetch_products_with_filters(session, 1, 10, {"categories": "Cables"})
    assert [p.name for p in products] == ["Cable A"]
