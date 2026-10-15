from app.core.config import get_settings
from sqlalchemy import create_engine, text

engine = create_engine(get_settings().sqlalchemy_database_url)

try:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS tabla_referenciada,
                ccu.column_name AS columna_referenciada
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.constraint_schema = kcu.constraint_schema
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
             AND tc.constraint_schema = ccu.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_schema = 'public'
              AND tc.table_name = 'organizaciones'
        """)).fetchall()

        print("CLAVES FORÁNEAS DE organizaciones:")
        for row in rows:
            print(row)
finally:
    engine.dispose()
