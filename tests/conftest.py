import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture(scope="session")
def test_engine():
    connect_args = {}
    if TEST_DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    eng = create_engine(TEST_DATABASE_URL, connect_args=connect_args)

    if TEST_DATABASE_URL.startswith("sqlite"):
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_conn, _rec):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture(scope="function")
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
