from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Creation of the database engine
engine = None
SessionLocal = None

# Base class for declarative models
Base = declarative_base()

def init_db():
    global engine, SessionLocal
    from app.core.config import get_settings  # Importa dentro para evitar errores en tests
    db_url = get_settings().database_url
    engine = create_engine(db_url, echo=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency to get the database session
def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_sync_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()