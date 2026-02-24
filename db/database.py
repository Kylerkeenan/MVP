from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url(), future=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


@contextmanager
def get_session() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_sql_file(path: str) -> None:
    engine = get_engine()
    with open(path, 'r', encoding='utf-8') as file:
        sql = file.read()
    with engine.begin() as conn:
        if 'sqlite' in engine.url.drivername:
            for stmt in [s.strip() for s in sql.split(';') if s.strip()]:
                conn.execute(text(stmt))
        else:
            conn.execute(text(sql))
