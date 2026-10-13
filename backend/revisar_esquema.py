from app.core.config import get_settings
from sqlalchemy import create_engine, text

engine = create_engine(get_settings().sqlalchemy_database_url)

try:
    with engine.connect() as conn:
        version = conn.execute(
            text("SELECT version_num FROM public.alembic_version")
        ).fetchall()
        print("VERSIONES REGISTRADAS:", version)

        for table in ("organizaciones", "usuarios"):
            columns = conn.execute(
                text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table
                    ORDER BY ordinal_position
                """),
                {"table": table}
            ).scalars().all()
            print(f"Columnas de {table}:", columns)
finally:
    engine.dispose()
