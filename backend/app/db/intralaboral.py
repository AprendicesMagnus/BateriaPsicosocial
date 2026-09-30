"""Siembra los cuestionarios intralaborales (Forma A y Forma B) en la base de datos.

Los datos (textos, dimensiones, ítems inversos, filtros y baremos) se leen de
app/db/data/intralaboral_forma_{A,B}.json, generados con
scripts/manual/extraer_textos_intralaboral.py.
"""
import json
from pathlib import Path

from app.models.survey import Baremo, CuestionarioVersion, Dimension, Pregunta

# Carpeta donde están los JSON con los datos de cada forma
DATA_DIR = Path(__file__).parent / "data"

# forma -> (código del cuestionario en BD, nombre, prefijo del código de cada pregunta).
# El prefijo + número de la pregunta en la página (p. ej. "INTA_12") es lo que usa el
# hook useCuestionarioBackend del frontend para encontrar el UUID de cada pregunta.
CONFIG = {
    "forma_A": ("INTRALABORAL_A", "Cuestionario de Factores de Riesgo Psicosocial Intralaboral - Forma A", "INTA_"),
    "forma_B": ("INTRALABORAL_B", "Cuestionario de Factores de Riesgo Psicosocial Intralaboral - Forma B", "INTB_"),
}


def _filtro_de(numero: int, filtros: dict) -> str | None:
    """Devuelve el filtro ("CLIENTES" / "JEFE") al que pertenece la pregunta, o None si no es condicional.

    filtros tiene la forma {"CLIENTES": [desde, hasta], ...} con el rango de números de pregunta.
    """
    for nombre, (desde, hasta) in filtros.items():
        if desde <= numero <= hasta:
            return nombre
    return None


def sembrar_forma_intralaboral(db, forma: str) -> CuestionarioVersion:
    """Crea la versión vigente del intralaboral de la forma indicada ("forma_A" o "forma_B").

    Si ya existe una versión vigente con ese código no hace nada y la devuelve,
    así el seed se puede ejecutar varias veces sin duplicar preguntas.
    """
    codigo, nombre, prefijo = CONFIG[forma]
    existente = (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == codigo, CuestionarioVersion.vigente.is_(True))
        .first()
    )
    if existente:
        return existente

    datos = json.loads((DATA_DIR / f"intralaboral_{forma}.json").read_text(encoding="utf-8"))
    # Ítems que se califican al revés según el manual (tabulacion.py aplica 4 - valor)
    inversos = set(datos.get("inversos", []))
    # Rangos de preguntas condicionales por filtro
    filtros = datos.get("filtros", {})

    version = CuestionarioVersion(codigo=codigo, nombre=nombre, numero_version=1, vigente=True)
    db.add(version)
    db.flush()

    for orden_dim, d in enumerate(datos["dimensiones"], start=1):
        # tipo: DIMENSION (tiene ítems), DOMINIO (suma dimensiones con dominio == su nombre) o TOTAL
        dimension = Dimension(
            version_id=version.id,
            codigo=d["codigo"],
            nombre=d["nombre"],
            dominio=d["dominio"],
            orden=orden_dim,
            tipo=d.get("tipo", "DIMENSION"),
            factor_transformacion=d.get("factor"),
        )
        db.add(dimension)
        db.flush()
        for n in d.get("items", []):
            db.add(
                Pregunta(
                    dimension_id=dimension.id,
                    codigo=f"{prefijo}{n}",
                    enunciado=datos["textos"][str(n)],
                    orden=n,
                    inversa=n in inversos,
                    # Escala oficial del intralaboral: Nunca=0 ... Siempre=4
                    valor_minimo=0,
                    valor_maximo=4,
                    tipo_respuesta="LIKERT",
                    filtro=_filtro_de(n, filtros),
                )
            )
        # Si la dimensión no trae baremos, el seed le asigna después los baremos estándar
        for orden_b, b in enumerate(d.get("baremos", []), start=1):
            db.add(Baremo(dimension_id=dimension.id, nivel=b["nivel"], minimo=b["min"], maximo=b["max"], orden=orden_b))
    db.flush()
    return version
