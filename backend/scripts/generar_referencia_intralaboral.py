"""Genera backend/docs/referencia_intralaboral_A_B.json desde:
- textos numerados de los JSX (misma numeración oficial 1..n)
- Tablas 21-34 del Manual del usuario Formas A y B (Ministerio, 2010)
  extraídas de:
  https://www.fondoriesgoslaborales.gov.co/wp-content/uploads/2025/06/2.-Manual-evaluacion-de-factores-de-riesgo-psicosociales-intralaboral-forma-AyB.pdf
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src" / "pages"
OUT = Path(__file__).resolve().parents[1] / "docs" / "referencia_intralaboral_A_B.json"

NIVELES = ["SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "MUY_ALTO"]


def parse_items_jsx(path: Path) -> dict[int, str]:
    text = path.read_text(encoding="utf-8")
    items = {}
    for m in re.finditer(r'\{\s*id:\s*(\d+)\s*,\s*tipo:\s*"likert"\s*,\s*texto:\s*"([^"]+)"\s*\}', text):
        items[int(m.group(1))] = m.group(2)
    return items


def baremos(ranges: list[tuple[float, float]]) -> list[dict]:
    assert len(ranges) == 5
    out = []
    for i, (mn, mx) in enumerate(ranges):
        out.append({"nivel": NIVELES[i], "minimo": mn, "maximo": mx, "orden": i + 1})
    return out


# Tabla 21: Siempre=0 / Nunca=4 (ítems protectores). El resto es Siempre=4 / Nunca=0.
# Ítem 80 Forma A ("maltratan") es de riesgo, no invertido.
INVERTIDOS_A = (
    {4, 5, 6, 9, 12, 14, 32, 34}
    | set(range(39, 52))
    | set(range(53, 80))
    | set(range(81, 106))
)

# Tabla 22. Corrección crítica ítem 66 Forma B: "maltratan" es riesgo (NO invertido).
INVERTIDOS_B = (
    {4, 5, 6, 9, 12, 14, 22, 24, 37, 97}
    | set(range(29, 37))
    | set(range(38, 66))
    | set(range(67, 89))
)

# Tabla 23 + Tabla 25
DIM_A = [
    {
        "codigo": "LIDERAZGO",
        "nombre": "Características del liderazgo",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(63, 76)),
        "factor": 52,
        "baremos": baremos([(0.0, 3.8), (3.9, 15.4), (15.5, 30.8), (30.9, 46.2), (46.3, 100.0)]),
    },
    {
        "codigo": "RELACIONES_SOCIALES",
        "nombre": "Relaciones sociales en el trabajo",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(76, 90)),
        "factor": 56,
        "baremos": baremos([(0.0, 5.4), (5.5, 16.1), (16.2, 25.0), (25.1, 37.5), (37.6, 100.0)]),
    },
    {
        "codigo": "RETROALIMENTACION",
        "nombre": "Retroalimentación del desempeño",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(90, 95)),
        "factor": 20,
        "baremos": baremos([(0.0, 10.0), (10.1, 25.0), (25.1, 40.0), (40.1, 55.0), (55.1, 100.0)]),
    },
    {
        "codigo": "RELACION_COLABORADORES",
        "nombre": "Relación con los colaboradores (subordinados)",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(115, 124)),
        "factor": 36,
        "baremos": baremos([(0.0, 13.9), (14.0, 25.0), (25.1, 33.3), (33.4, 47.2), (47.3, 100.0)]),
    },
    {
        "codigo": "CLARIDAD_ROL",
        "nombre": "Claridad de rol",
        "dominio": "Control sobre el trabajo",
        "items": list(range(53, 60)),
        "factor": 28,
        "baremos": baremos([(0.0, 0.9), (1.0, 10.7), (10.8, 21.4), (21.5, 39.3), (39.4, 100.0)]),
    },
    {
        "codigo": "CAPACITACION",
        "nombre": "Capacitación",
        "dominio": "Control sobre el trabajo",
        "items": list(range(60, 63)),
        "factor": 12,
        "baremos": baremos([(0.0, 0.9), (1.0, 16.7), (16.8, 33.3), (33.4, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "PARTICIPACION_CAMBIO",
        "nombre": "Participación y manejo del cambio",
        "dominio": "Control sobre el trabajo",
        "items": [48, 49, 50, 51],
        "factor": 16,
        "baremos": baremos([(0.0, 12.5), (12.6, 25.0), (25.1, 37.5), (37.6, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "OPORTUNIDADES_HABILIDADES",
        "nombre": "Oportunidades para el uso y desarrollo de habilidades y conocimientos",
        "dominio": "Control sobre el trabajo",
        "items": [39, 40, 41, 42],
        "factor": 16,
        "baremos": baremos([(0.0, 0.9), (1.0, 6.3), (6.4, 18.8), (18.9, 31.3), (31.4, 100.0)]),
    },
    {
        "codigo": "CONTROL_AUTONOMIA",
        "nombre": "Control y autonomía sobre el trabajo",
        "dominio": "Control sobre el trabajo",
        "items": [44, 45, 46],
        "factor": 12,
        "baremos": baremos([(0.0, 8.3), (8.4, 25.0), (25.1, 41.7), (41.8, 58.3), (58.4, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_AMBIENTALES",
        "nombre": "Demandas ambientales y de esfuerzo físico",
        "dominio": "Demandas del trabajo",
        "items": list(range(1, 13)),
        "factor": 48,
        "baremos": baremos([(0.0, 14.6), (14.7, 22.9), (23.0, 31.3), (31.4, 39.6), (39.7, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_EMOCIONALES",
        "nombre": "Demandas emocionales",
        "dominio": "Demandas del trabajo",
        "items": list(range(106, 115)),
        "factor": 36,
        "baremos": baremos([(0.0, 16.7), (16.8, 25.0), (25.1, 33.3), (33.4, 47.2), (47.3, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_CUANTITATIVAS",
        "nombre": "Demandas cuantitativas",
        "dominio": "Demandas del trabajo",
        "items": [13, 14, 15, 32, 43, 47],
        "factor": 24,
        "baremos": baremos([(0.0, 25.0), (25.1, 33.3), (33.4, 45.8), (45.9, 54.2), (54.3, 100.0)]),
    },
    {
        "codigo": "INFLUENCIA_EXTRALABORAL",
        "nombre": "Influencia del trabajo sobre el entorno extralaboral",
        "dominio": "Demandas del trabajo",
        "items": [35, 36, 37, 38],
        "factor": 16,
        "baremos": baremos([(0.0, 18.8), (18.9, 31.3), (31.4, 43.8), (43.9, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "RESPONSABILIDAD_CARGO",
        "nombre": "Exigencias de responsabilidad del cargo",
        "dominio": "Demandas del trabajo",
        "items": [19, 22, 23, 24, 25, 26],
        "factor": 24,
        "baremos": baremos([(0.0, 37.5), (37.6, 54.2), (54.3, 66.7), (66.8, 79.2), (79.3, 100.0)]),
    },
    {
        "codigo": "CARGA_MENTAL",
        "nombre": "Demandas de carga mental",
        "dominio": "Demandas del trabajo",
        "items": [16, 17, 18, 20, 21],
        "factor": 20,
        "baremos": baremos([(0.0, 60.0), (60.1, 70.0), (70.1, 80.0), (80.1, 90.0), (90.1, 100.0)]),
    },
    {
        "codigo": "CONSISTENCIA_ROL",
        "nombre": "Consistencia del rol",
        "dominio": "Demandas del trabajo",
        "items": [27, 28, 29, 30, 52],
        "factor": 20,
        "baremos": baremos([(0.0, 15.0), (15.1, 25.0), (25.1, 35.0), (35.1, 45.0), (45.1, 100.0)]),
    },
    {
        "codigo": "JORNADA",
        "nombre": "Demandas de la jornada de trabajo",
        "dominio": "Demandas del trabajo",
        "items": [31, 33, 34],
        "factor": 12,
        "baremos": baremos([(0.0, 8.3), (8.4, 25.0), (25.1, 33.3), (33.4, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "RECOMPENSAS_PERTENENCIA",
        "nombre": "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza",
        "dominio": "Recompensas",
        "items": [95, 102, 103, 104, 105],
        "factor": 20,
        "baremos": baremos([(0.0, 0.9), (1.0, 5.0), (5.1, 10.0), (10.1, 20.0), (20.1, 100.0)]),
    },
    {
        "codigo": "RECONOCIMIENTO_COMPENSACION",
        "nombre": "Reconocimiento y compensación",
        "dominio": "Recompensas",
        "items": [96, 97, 98, 99, 100, 101],
        "factor": 24,
        "baremos": baremos([(0.0, 4.2), (4.3, 16.7), (16.8, 25.0), (25.1, 37.5), (37.6, 100.0)]),
    },
]

DIM_B = [
    {
        "codigo": "LIDERAZGO",
        "nombre": "Características del liderazgo",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(49, 62)),
        "factor": 52,
        "baremos": baremos([(0.0, 3.8), (3.9, 13.5), (13.6, 25.0), (25.1, 38.5), (38.6, 100.0)]),
    },
    {
        "codigo": "RELACIONES_SOCIALES",
        "nombre": "Relaciones sociales en el trabajo",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(62, 74)),
        "factor": 48,
        "baremos": baremos([(0.0, 6.3), (6.4, 14.6), (14.7, 27.1), (27.2, 37.5), (37.6, 100.0)]),
    },
    {
        "codigo": "RETROALIMENTACION",
        "nombre": "Retroalimentación del desempeño",
        "dominio": "Liderazgo y relaciones sociales en el trabajo",
        "items": list(range(74, 79)),
        "factor": 20,
        "baremos": baremos([(0.0, 5.0), (5.1, 20.0), (20.1, 30.0), (30.1, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "CLARIDAD_ROL",
        "nombre": "Claridad de rol",
        "dominio": "Control sobre el trabajo",
        "items": list(range(41, 46)),
        "factor": 20,
        "baremos": baremos([(0.0, 0.9), (1.0, 5.0), (5.1, 15.0), (15.1, 30.0), (30.1, 100.0)]),
    },
    {
        "codigo": "CAPACITACION",
        "nombre": "Capacitación",
        "dominio": "Control sobre el trabajo",
        "items": [46, 47, 48],
        "factor": 12,
        "baremos": baremos([(0.0, 0.9), (1.0, 16.7), (16.8, 25.0), (25.1, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "PARTICIPACION_CAMBIO",
        "nombre": "Participación y manejo del cambio",
        "dominio": "Control sobre el trabajo",
        "items": [38, 39, 40],
        "factor": 12,
        "baremos": baremos([(0.0, 16.7), (16.8, 33.3), (33.4, 41.7), (41.8, 58.3), (58.4, 100.0)]),
    },
    {
        "codigo": "OPORTUNIDADES_HABILIDADES",
        "nombre": "Oportunidades para el uso y desarrollo de habilidades y conocimientos",
        "dominio": "Control sobre el trabajo",
        "items": [29, 30, 31, 32],
        "factor": 16,
        "baremos": baremos([(0.0, 12.5), (12.6, 25.0), (25.1, 37.5), (37.6, 56.3), (56.4, 100.0)]),
    },
    {
        "codigo": "CONTROL_AUTONOMIA",
        "nombre": "Control y autonomía sobre el trabajo",
        "dominio": "Control sobre el trabajo",
        "items": [34, 35, 36],
        "factor": 12,
        "baremos": baremos([(0.0, 33.3), (33.4, 50.0), (50.1, 66.7), (66.8, 75.0), (75.1, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_AMBIENTALES",
        "nombre": "Demandas ambientales y de esfuerzo físico",
        "dominio": "Demandas del trabajo",
        "items": list(range(1, 13)),
        "factor": 48,
        "baremos": baremos([(0.0, 22.9), (23.0, 31.3), (31.4, 39.6), (39.7, 47.9), (48.0, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_EMOCIONALES",
        "nombre": "Demandas emocionales",
        "dominio": "Demandas del trabajo",
        "items": list(range(89, 98)),
        "factor": 36,
        "baremos": baremos([(0.0, 19.4), (19.5, 27.8), (27.9, 38.9), (39.0, 47.2), (47.3, 100.0)]),
    },
    {
        "codigo": "DEMANDAS_CUANTITATIVAS",
        "nombre": "Demandas cuantitativas",
        "dominio": "Demandas del trabajo",
        "items": [13, 14, 15],
        "factor": 12,
        "baremos": baremos([(0.0, 16.7), (16.8, 33.3), (33.4, 41.7), (41.8, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "INFLUENCIA_EXTRALABORAL",
        "nombre": "Influencia del trabajo sobre el entorno extralaboral",
        "dominio": "Demandas del trabajo",
        "items": [25, 26, 27, 28],
        "factor": 16,
        "baremos": baremos([(0.0, 12.5), (12.6, 25.0), (25.1, 31.3), (31.4, 50.0), (50.1, 100.0)]),
    },
    {
        "codigo": "CARGA_MENTAL",
        "nombre": "Demandas de carga mental",
        "dominio": "Demandas del trabajo",
        "items": [16, 17, 18, 19, 20],
        "factor": 20,
        "baremos": baremos([(0.0, 50.0), (50.1, 65.0), (65.1, 75.0), (75.1, 85.0), (85.1, 100.0)]),
    },
    {
        "codigo": "JORNADA",
        "nombre": "Demandas de la jornada de trabajo",
        "dominio": "Demandas del trabajo",
        "items": [21, 22, 23, 24, 33, 37],
        "factor": 24,
        "baremos": baremos([(0.0, 25.0), (25.1, 37.5), (37.6, 45.8), (45.9, 58.3), (58.4, 100.0)]),
    },
    {
        "codigo": "RECOMPENSAS_PERTENENCIA",
        "nombre": "Recompensas derivadas de la pertenencia a la organización y del trabajo que se realiza",
        "dominio": "Recompensas",
        "items": [85, 86, 87, 88],
        "factor": 16,
        "baremos": baremos([(0.0, 0.9), (1.0, 6.3), (6.4, 12.5), (12.6, 18.8), (18.9, 100.0)]),
    },
    {
        "codigo": "RECONOCIMIENTO_COMPENSACION",
        "nombre": "Reconocimiento y compensación",
        "dominio": "Recompensas",
        "items": [79, 80, 81, 82, 83, 84],
        "factor": 24,
        "baremos": baremos([(0.0, 0.9), (1.0, 12.5), (12.6, 25.0), (25.1, 37.5), (37.6, 100.0)]),
    },
]

# Tabla 26
DOM_A = [
    {"codigo": "DOM_LIDERAZGO", "nombre": "Liderazgo y relaciones sociales en el trabajo", "factor": 164,
     "baremos": baremos([(0.0, 9.1), (9.2, 17.7), (17.8, 25.6), (25.7, 34.8), (34.9, 100.0)])},
    {"codigo": "DOM_CONTROL", "nombre": "Control sobre el trabajo", "factor": 84,
     "baremos": baremos([(0.0, 10.7), (10.8, 19.0), (19.1, 29.8), (29.9, 40.5), (40.6, 100.0)])},
    {"codigo": "DOM_DEMANDAS", "nombre": "Demandas del trabajo", "factor": 200,
     "baremos": baremos([(0.0, 28.5), (28.6, 35.0), (35.1, 41.5), (41.6, 47.5), (47.6, 100.0)])},
    {"codigo": "DOM_RECOMPENSAS", "nombre": "Recompensas", "factor": 44,
     "baremos": baremos([(0.0, 4.5), (4.6, 11.4), (11.5, 20.5), (20.6, 29.5), (29.6, 100.0)])},
]
DOM_B = [
    {"codigo": "DOM_LIDERAZGO", "nombre": "Liderazgo y relaciones sociales en el trabajo", "factor": 120,
     "baremos": baremos([(0.0, 8.3), (8.4, 17.5), (17.6, 26.7), (26.8, 38.3), (38.4, 100.0)])},
    {"codigo": "DOM_CONTROL", "nombre": "Control sobre el trabajo", "factor": 72,
     "baremos": baremos([(0.0, 19.4), (19.5, 26.4), (26.5, 34.7), (34.8, 43.1), (43.2, 100.0)])},
    {"codigo": "DOM_DEMANDAS", "nombre": "Demandas del trabajo", "factor": 156,
     "baremos": baremos([(0.0, 26.9), (27.0, 33.3), (33.4, 37.8), (37.9, 44.2), (44.3, 100.0)])},
    {"codigo": "DOM_RECOMPENSAS", "nombre": "Recompensas", "factor": 40,
     "baremos": baremos([(0.0, 2.5), (2.6, 10.0), (10.1, 17.5), (17.6, 27.5), (27.6, 100.0)])},
]

# Tabla 27 y 33
TOTAL_A = {"factor": 492, "baremos": baremos([(0.0, 19.7), (19.8, 25.8), (25.9, 31.5), (31.6, 38.0), (38.1, 100.0)])}
TOTAL_B = {"factor": 388, "baremos": baremos([(0.0, 20.6), (20.7, 26.0), (26.1, 31.2), (31.3, 38.7), (38.8, 100.0)])}

# Tabla 28 y 34 (intra+extra)
TOTAL_GENERAL_A = {"factor": 616, "baremos": baremos([(0.0, 18.8), (18.9, 24.4), (24.5, 29.5), (29.6, 35.4), (35.5, 100.0)])}
TOTAL_GENERAL_B = {"factor": 512, "baremos": baremos([(0.0, 19.9), (20.0, 24.8), (24.9, 29.5), (29.6, 35.4), (35.5, 100.0)])}


def forma(codigo, items_textos, invertidos, dims, dominios, total, total_general):
    n = 123 if codigo.endswith("A") else 97
    items = []
    for i in range(1, n + 1):
        items.append({
            "n": i,
            "texto": items_textos[i],
            "invertido": i in invertidos,
            "grupo_calificacion": "INVERTIDO" if i in invertidos else "NORMAL",
        })
    return {
        "codigo": codigo,
        "items": items,
        "dimensiones": dims,
        "dominios": dominios,
        "total_cuestionario": total,
        "total_general_intra_extra": total_general,
    }


def validar(forma_data, esperado):
    nums = [it["n"] for it in forma_data["items"]]
    assert nums == list(range(1, esperado + 1)), f"Huecos en {forma_data['codigo']}: {nums}"
    cubiertos = []
    for d in forma_data["dimensiones"]:
        cubiertos.extend(d["items"])
        assert d["factor"] == len(d["items"]) * 4, (d["nombre"], d["factor"], len(d["items"]))
    assert sorted(cubiertos) == list(range(1, esperado + 1)), (
        f"{forma_data['codigo']} unión dimensiones != 1..{esperado}: "
        f"faltan {set(range(1, esperado+1)) - set(cubiertos)} extra {set(cubiertos) - set(range(1, esperado+1))}"
    )
    suma_factores_dim = sum(d["factor"] for d in forma_data["dimensiones"])
    assert suma_factores_dim == forma_data["total_cuestionario"]["factor"]
    suma_dom = sum(d["factor"] for d in forma_data["dominios"])
    assert suma_dom == forma_data["total_cuestionario"]["factor"]


def main():
    textos_a = parse_items_jsx(FRONTEND / "CuestionarioIntralaboral.jsx")
    textos_b = parse_items_jsx(FRONTEND / "CuestionarioIntralaboralB.jsx")
    assert set(textos_a) == set(range(1, 124)), set(range(1, 124)) - set(textos_a)
    assert set(textos_b) == set(range(1, 98)), set(range(1, 98)) - set(textos_b)

    fa = forma("INTRALABORAL_A", textos_a, INVERTIDOS_A, DIM_A, DOM_A, TOTAL_A, TOTAL_GENERAL_A)
    fb = forma("INTRALABORAL_B", textos_b, INVERTIDOS_B, DIM_B, DOM_B, TOTAL_B, TOTAL_GENERAL_B)
    validar(fa, 123)
    validar(fb, 97)

    doc = {
        "fuente": (
            "Ministerio de la Protección Social (2010). Batería de instrumentos para la evaluación "
            "de factores de riesgo psicosocial. II – Cuestionarios de factores de riesgo psicosocial "
            "intralaboral – Forma A y Forma B – Manual del Usuario. Tablas 21 a 34."
        ),
        "escala_oficial": {
            "valor_minimo": 0,
            "valor_maximo": 4,
            "grupo_NORMAL": {"Siempre": 4, "Casi siempre": 3, "Algunas veces": 2, "Casi nunca": 1, "Nunca": 0},
            "grupo_INVERTIDO": {"Siempre": 0, "Casi siempre": 1, "Algunas veces": 2, "Casi nunca": 3, "Nunca": 4},
            "nota_item_66_forma_B": (
                "El ítem 66 de Forma B ('En mi grupo de trabajo algunas personas me maltratan.') "
                "pertenece al grupo NORMAL (Siempre=4). No es invertido."
            ),
        },
        "formula_transformacion": "puntaje_transformado = (puntaje_bruto / factor_transformacion) * 100, redondeo a 1 decimal",
        "equivalencia_minmax": (
            "Con escala 0-4 y todos los ítems respondidos, factor = n_items * 4 = maximo, minimo = 0, "
            "por lo que 100*(bruto-minimo)/(maximo-minimo) = 100*bruto/factor."
        ),
        "forma_A": fa,
        "forma_B": fb,
        "conteos": {
            "items_A": len(fa["items"]),
            "invertidos_A": sum(1 for i in fa["items"] if i["invertido"]),
            "dimensiones_A": len(fa["dimensiones"]),
            "items_B": len(fb["items"]),
            "invertidos_B": sum(1 for i in fb["items"] if i["invertido"]),
            "dimensiones_B": len(fb["dimensiones"]),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito {OUT}")
    print(json.dumps(doc["conteos"], indent=2))
    print("union A 1-123 sin huecos: OK")
    print("union B 1-97 sin huecos: OK")


if __name__ == "__main__":
    main()
