from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from app.db.db_connection import Base
from alembic import context
from app.core.config import get_settings
from app.models import *

# this is the Alembic Config object
config = context.config

# --- INICIO DE LA MODIFICACIÓN CLAVE ---
# Comprobamos si estamos en el entorno de migración de Cloud Build
# buscando la variable de entorno DB_HOST.
if os.environ.get("DB_HOST"):
    # Si estamos en el pipeline, construimos la URL dinámicamente
    # con las variables que nos pasa el 'docker run' de Cloud Build.
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")
    
    # ¡AQUÍ ESTÁ EL CAMBIO! Usamos el dialecto mysql+pymysql.
    prod_database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    config.set_main_option('sqlalchemy.url', prod_database_url)
else:
    # Si no, estamos en local y usamos la configuración del .env como siempre.
    settings = get_settings()
    config.set_main_option(
        'sqlalchemy.url',
        settings.prod_database_url or settings.database_url
    )
# --- FIN DE LA MODIFICACIÓN CLAVE ---

# El resto del archivo permanece igual
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()