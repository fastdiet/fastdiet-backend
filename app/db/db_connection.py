import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Creation of the database engine
engine = None
SessionLocal = None

# Base class for declarative models
Base = declarative_base()

def init_db():
    global engine, SessionLocal
    from app.core.config import get_settings
    settings = get_settings()

    if os.environ.get("K_SERVICE"):
        from google.cloud.sql.connector import Connector

        instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"] 
        db_user = os.environ["DB_USER"]           
        db_pass = os.environ["DB_PASS"] 
        db_name = os.environ["DB_NAME"]

        connector = Connector()

        def getconn():
            conn = connector.connect(
                instance_connection_name,
                "pymysql",
                user=db_user,
                password=db_pass,
                db=db_name,
            )
            return conn

        engine = create_engine(
            "mysql+pymysql://",
            creator=getconn,
            echo=False,
            pool_recycle=1800 
        )
    else:
        db_url = settings.database_url
        engine = create_engine(db_url, echo=False)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized")
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