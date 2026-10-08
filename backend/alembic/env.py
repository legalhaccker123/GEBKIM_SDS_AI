from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database.base import Base
from app.database.config import settings

# Modellerin SQLAlchemy metadata'ya kayıt olması için
# modelleri import ediyoruz.
from app.models import (
    Chemical,
    ChemicalIdentifier,
    SDSDocument,
    SDSSection,
)


# =========================================================
# ALEMBIC CONFIG
# =========================================================

config = context.config


# =========================================================
# DATABASE URL
# =========================================================

# Alembic'in alembic.ini içerisindeki sabit URL yerine
# uygulamamızın kullandığı database_url'i kullanmasını sağlıyoruz.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url
)


# =========================================================
# LOGGING
# =========================================================

if config.config_file_name is not None:
    fileConfig(
        config.config_file_name
    )


# =========================================================
# SQLALCHEMY METADATA
# =========================================================

# Alembic autogenerate işlemi Base.metadata ile
# gerçek veritabanını karşılaştıracak.
target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATION
# =========================================================

def run_migrations_offline() -> None:
    """
    Database bağlantısı oluşturmadan migration üretir.
    """

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE MIGRATION
# =========================================================

def run_migrations_online() -> None:
    """
    Gerçek database bağlantısı üzerinden migration çalıştırır.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================================================
# RUN
# =========================================================

if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()