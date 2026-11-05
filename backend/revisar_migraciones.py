
from pathlib import Path

carpeta = Path("alembic/versions")

for archivo in sorted(carpeta.glob("*.py")):
    revision = "NO ENCONTRADA"
    down_revision = "NO ENCONTRADA"

    with open(archivo, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            if linea.startswith("revision:") or linea.startswith("revision ="):
                revision = linea.split("=", 1)[1].strip()

            if linea.startswith("down_revision:") or linea.startswith("down_revision ="):
                down_revision = linea.split("=", 1)[1].strip()

    print(f"{archivo.name} | revision={revision} | down_revision={down_revision}")
