from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

# URL of the database
SQLALCHEMY_DATABASE_URL = get_settings().database_url

# Creation of the database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creation of the session local class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()