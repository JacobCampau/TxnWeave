"""Shared test fixtures. Each API test gets its own empty SQLite file in a temp folder."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from txnweave_api.db.database import get_session, make_engine
from txnweave_api.db.models import Base
from txnweave_api.main import app


@pytest.fixture
def client(tmp_path):
    engine = make_engine(str(tmp_path / "test.db"))
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def test_session():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    # Not used as a context manager, so the app's startup (init_db on the real file) doesn't run.
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def investigation_id(client) -> int:
    return client.post("/api/investigations", json={}).json()["id"]
