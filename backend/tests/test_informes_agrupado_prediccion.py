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