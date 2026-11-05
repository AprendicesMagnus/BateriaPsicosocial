"""Regla de anonimato de los perfiles K-Means del análisis predictivo.

El endpoint /api/informes/agrupado ahora devuelve un ZIP con las plantillas Excel;
ese flujo se prueba en test_informes_agrupado.py.
"""

from app.services.informes import _perfiles_visibles


def test_perfiles_visibles_regla_anonimato():
    prediccion = {
        "perfilesClusterKMeans": [
            {"etiqueta": "Cluster A", "numTrabajadores": 5},
            {"etiqueta": "Cluster B", "numTrabajadores": 2},
        ]
    }
    visibles, omitidos = _perfiles_visibles(prediccion, minimo=5)
    assert len(visibles) == 1
    assert visibles[0]["numTrabajadores"] == 5
    assert omitidos == 1