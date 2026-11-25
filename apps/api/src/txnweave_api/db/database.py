"""Database engine, sessions and table creation (persistence.md, B1)."""

from collections.abc import Iterator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from txnweave_api import config
from txnweave_api.db.models import Base


def make_engine(db_path: str) -> Engine:
    engine = create_engine(f"sqlite:///{db_path}")

    # SQLite only enforces foreign keys (and so ON DELETE CASCADE) when this is switched on,
    # and it has to be switched on for every new connection.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


# Creating the engine doesn't open the file yet; that happens on the first query.
engine = make_engine(config.DB_PATH)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Create the folder and any missing tables. No migrations yet (persistence non-goals)."""
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
