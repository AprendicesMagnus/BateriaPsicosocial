"""Genera app/db/data/intralaboral_forma_{A,B}.json a partir de las páginas del frontend.

Deja una sola dimensión provisional con todos los ítems. Después se reemplaza
por las dimensiones, ítems inversos y baremos oficiales del manual.

Uso (desde la carpeta backend, con el venv activo):
    python scripts\\manual\\extraer_textos_intralaboral.py
"""
import json
import re
from pathlib import Path

# Raíz del proyecto (BateriaPsicosocial): este archivo está en backend/scripts/manual/
RAIZ = Path(__file__).resolve().parents[3]

# forma -> (página JSX de donde se leen los textos, rangos de preguntas condicionales por filtro).
# Forma A: 106-114 dependen de "¿Atiende clientes?" y 115-123 de "¿Es jefe?". Forma B solo tiene clientes.
PAGINAS = {
    "forma_A": ("CuestionarioIntralaboral.jsx", {"CLIENTES": [106, 114], "JEFE": [115, 123]}),
    "forma_B": ("CuestionarioIntralaboralB.jsx", {"CLIENTES": [89, 97]}),
}

# Captura las preguntas escritas en el JSX como { id: 12, tipo: "likert", texto: "..." }
PATRON = re.compile(r'\{\s*id:\s*(\d+),\s*tipo:\s*"likert",\s*texto:\s*"(.*?)"\s*\}')

for forma, (archivo, filtros) in PAGINAS.items():
    jsx = (RAIZ / "frontend" / "src" / "pages" / archivo).read_text(encoding="utf-8")
    # número de pregunta (como texto) -> enunciado
    textos = {m.group(1): m.group(2) for m in PATRON.finditer(jsx)}
    items = sorted(int(n) for n in textos)
    # Estructura que lee app/db/intralaboral.py
    datos = {
        "textos": textos,
        "inversos": [],
        "filtros": filtros,
        "dimensiones": [
            {
                "codigo": "INTRALABORAL_PROVISIONAL",
                "nombre": "Intralaboral (provisional)",
                "dominio": "Intralaboral",
                "items": items,
                "factor": None,
            }
        ],
    }
    destino = RAIZ / "backend" / "app" / "db" / "data" / f"intralaboral_{forma}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{forma}: {len(items)} preguntas -> {destino}")
