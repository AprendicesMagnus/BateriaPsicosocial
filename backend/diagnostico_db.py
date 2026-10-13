from app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
engine = create_engine(settings.sqlalchemy_database_url)

try:
    with engine.connect() as conn:
        print("BASE DE DATOS:", engine.url.database)
        print("SERVIDOR:", engine.url.host)
        print("PUERTO:", engine.url.port)
        print("ESQUEMA:", conn.execute(text("SELECT current_schema()")).scalar())
        print(
            "TABLA ALEMBIC:",
            conn.execute(
                text("SELECT to_regclass(:name)"),
                {"name": "public.alembic_version"}
            ).scalar()
        )
finally:
    engine.dispose()
