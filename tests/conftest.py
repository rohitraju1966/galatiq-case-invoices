"""Shared test fixtures."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import agents.tools.db as db_module
from db.models import Base, MasterInventory, MasterMerchant


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    """A fresh SQLite DB pointed at a temp file, seeded with the master catalog
    and one known merchant. Each test gets an isolated database. The full seed
    lives in migrations/seed.py; here we seed only what the tests exercise.
    """
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))

    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all(
        [
            MasterInventory(item_name="WidgetA", unit_price=250.0, item_budget=10_000.0, stock_qty=15),
            MasterInventory(item_name="WidgetB", unit_price=500.0, item_budget=15_000.0, stock_qty=10),
            MasterInventory(item_name="GadgetX", unit_price=750.0, item_budget=8_000.0, stock_qty=5),
            MasterMerchant(merchant_name="Atlas Industrial Supply", rating=4, on_time_history="reliable", notes=""),
        ]
    )
    session.commit()
    session.close()
    return str(db_file)
