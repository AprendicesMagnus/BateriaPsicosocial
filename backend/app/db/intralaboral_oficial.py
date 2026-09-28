from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.models.evaluation import ResultadoDimension
from app.models.survey import Baremo, CuestionarioVersion, Dimension, Pregunta

JSON_PATH = Path(__file__).resolve().parents[2] / "docs" / "referencia_intralaboral_A_B.json"

NIVELES_BAREMO = {
    "SIN_RIESGO": "SIN_RIESGO",
    "BAJO": "BAJO",
    "MEDIO": "MEDIO",
    "ALTO": "ALTO",
    "MUY_ALTO": "MUY_ALTO",
}


@lru_cache(maxsize=1)
def cargar_referencia() -> dict:
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"No existe la referencia oficial: {JSON_PATH}")
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _borrar_dimensiones(db, version: CuestionarioVersion) -> None:
    ids = [d.id for d in version.dimensiones]
    if not ids:
        return
    db.query(ResultadoDimension).filter(ResultadoDimension.dimension_id.in_(ids)).delete(synchronize_session=False)
    for dim in list(version.dimensiones):
        db.delete(dim)
    db.flush()


def _agregar_baremos(db, dimension_id, baremos: list[dict]) -> None:
    for b in baremos:
        db.add(
            Baremo(
                dimension_id=dimension_id,
                nivel=NIVELES_BAREMO[b["nivel"]],
                minimo=b["minimo"],
                maximo=b["maximo"],
                orden=b["orden"],
            )
        )


def sembrar_forma_intralaboral(db, forma_key: str) -> CuestionarioVersion:
    ref = cargar_referencia()
    forma = ref[forma_key]
    codigo = forma["codigo"]
    nombre = (
        "Cuestionario de Factores de Riesgo Psicosocial Intralaboral - Forma A"
        if codigo.endswith("_A")
        else "Cuestionario de Factores de Riesgo Psicosocial Intralaboral - Forma B"
    )
    descripcion = (
        "Instrumento oficial Forma A (jefes, profesionales, analistas, técnicos)."
        if codigo.endswith("_A")
        else "Instrumento oficial Forma B (auxiliares, asistentes, operarios, servicios generales)."
    )
    version = (
        db.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == codigo, CuestionarioVersion.vigente.is_(True))
        .first()
    )
    n_dim_esperadas = len(forma["dimensiones"])
    n_actual = 0
    if version:
        n_actual = sum(1 for d in version.dimensiones if d.tipo == "DIMENSION")
        if n_actual == n_dim_esperadas:
            return version
        _borrar_dimensiones(db, version)
    else:
        version = CuestionarioVersion(
            codigo=codigo,
            nombre=nombre,
            numero_version=1,
            descripcion=descripcion,
            vigente=True,
        )
        db.add(version)
        db.flush()

    textos = {it["n"]: it for it in forma["items"]}
    orden = 1
    for dim_data in forma["dimensiones"]:
        dim = Dimension(
            version_id=version.id,
            codigo=dim_data["codigo"],
            nombre=dim_data["nombre"],
            dominio=dim_data["dominio"],
            orden=orden,
            tipo="DIMENSION",
            factor_transformacion=float(dim_data["factor"]),
        )
        db.add(dim)
        db.flush()
        _agregar_baremos(db, dim.id, dim_data["baremos"])
        for n in dim_data["items"]:
            item = textos[n]
            db.add(
                Pregunta(
                    dimension_id=dim.id,
                    codigo=f"{codigo}_{n}",
                    enunciado=item["texto"],
                    orden=n,
                    inversa=bool(item["invertido"]),
                    valor_minimo=0,
                    valor_maximo=4,
                    tipo_respuesta="LIKERT",
                )
            )
        orden += 1

    for dom in forma["dominios"]:
        dim = Dimension(
            version_id=version.id,
            codigo=dom["codigo"],
            nombre=dom["nombre"],
            dominio=dom["nombre"],
            orden=orden,
            tipo="DOMINIO",
            factor_transformacion=float(dom["factor"]),
        )
        db.add(dim)
        db.flush()
        _agregar_baremos(db, dim.id, dom["baremos"])
        orden += 1

    total = forma["total_cuestionario"]
    dim_total = Dimension(
        version_id=version.id,
        codigo="TOTAL_CUESTIONARIO",
        nombre="Puntaje total del cuestionario",
        dominio="Total intralaboral",
        orden=orden,
        tipo="TOTAL",
        factor_transformacion=float(total["factor"]),
    )
    db.add(dim_total)
    db.flush()
    _agregar_baremos(db, dim_total.id, total["baremos"])
    db.flush()
    return version
