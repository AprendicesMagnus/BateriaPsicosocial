from app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()
engine = create_engine(settings.test_database_url)

try:
    with engine.connect() as conn:
        print("BASE:", conn.execute(text("SELECT current_database()")).scalar())

        version_exists = conn.execute(text("""
            SELECT to_regclass('public.alembic_version')
        """)).scalar()

        print("TABLA ALEMBIC:", version_exists)

        if version_exists:
            versions = conn.execute(text("""
                SELECT version_num FROM public.alembic_version
            """)).fetchall()
            print("VERSIONES:", versions)

        for table in ("organizaciones", "usuarios"):
            columns = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table
                ORDER BY ordinal_position
            """), {"table": table}).scalars().all()

            print(f"COLUMNAS DE {table}:", columns)

finally:
    engine.dispose()
