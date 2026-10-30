import copy

from app.core.config import get_settings
from app.services.prediccion import aplicar_anonimato_perfiles

settings = get_settings()


def test_perfiles_mezclados_minimo_5():
    # (a) perfiles de 5 y de 2 trabajadores con minimo 5: queda solo el de 5, perfilesOmitidos == 1, minimoAnonimato == 5
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": 5, "etiqueta": "P1"},
            {"clusterId": 2, "numTrabajadores": 2, "etiqueta": "P2"},
        ]
    }
    res = aplicar_anonimato_perfiles(datos, minimo=5)
    assert len(res["perfilesClusterKMeans"]) == 1
    assert res["perfilesClusterKMeans"][0]["clusterId"] == 1
    assert res["perfilesOmitidos"] == 1
    assert res["minimoAnonimato"] == 5


def test_todos_perfiles_superan_minimo():
    # (b) todos los perfiles con 5 o mas: perfilesOmitidos == 0
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": 5, "etiqueta": "P1"},
            {"clusterId": 2, "numTrabajadores": 8, "etiqueta": "P2"},
        ]
    }
    res = aplicar_anonimato_perfiles(datos, minimo=5)
    assert len(res["perfilesClusterKMeans"]) == 2
    assert res["perfilesOmitidos"] == 0
    assert res["minimoAnonimato"] == 5


def test_todos_perfiles_menores_que_minimo():
    # (c) todos los perfiles con menos del minimo: lista vacia y perfilesOmitidos igual al total
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": 3, "etiqueta": "P1"},
            {"clusterId": 2, "numTrabajadores": 1, "etiqueta": "P2"},
            {"clusterId": 3, "numTrabajadores": 4, "etiqueta": "P3"},
        ]
    }
    res = aplicar_anonimato_perfiles(datos, minimo=5)
    assert res["perfilesClusterKMeans"] == []
    assert res["perfilesOmitidos"] == 3
    assert res["minimoAnonimato"] == 5


def test_no_modifica_dict_original_y_conserva_campos():
    # (d) el diccionario original no se modifica (compara una copia profunda antes y despues) y alertasTempranas e incidenciaRiesgoPorDimension se conservan identicos
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": 2},
        ],
        "alertasTempranas": [{"dimension": "Liderazgo", "nivelAlerta": "ALTA"}],
        "incidenciaRiesgoPorDimension": [{"dimensionId": "dim-1", "promedioPuntaje": 45.2}],
        "totalParticipantesAnalizados": 10,
    }
    original_copia = copy.deepcopy(datos)
    res = aplicar_anonimato_perfiles(datos, minimo=5)

    assert datos == original_copia, "El diccionario original no debe ser modificado"
    assert res["alertasTempranas"] == datos["alertasTempranas"]
    assert res["incidenciaRiesgoPorDimension"] == datos["incidenciaRiesgoPorDimension"]
    assert res["totalParticipantesAnalizados"] == 10


def test_limite_exacto_4_y_5():
    # (e) un perfil de exactamente 4 se omite y uno de exactamente 5 se conserva con minimo 5
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": 4},
            {"clusterId": 2, "numTrabajadores": 5},
        ]
    }
    res = aplicar_anonimato_perfiles(datos, minimo=5)
    assert len(res["perfilesClusterKMeans"]) == 1
    assert res["perfilesClusterKMeans"][0]["clusterId"] == 2
    assert res["perfilesOmitidos"] == 1


def test_minimo_none_usa_settings():
    # (f) con minimo=None usa settings.min_grupo_anonimato
    datos = {
        "perfilesClusterKMeans": [
            {"clusterId": 1, "numTrabajadores": settings.min_grupo_anonimato - 1},
            {"clusterId": 2, "numTrabajadores": settings.min_grupo_anonimato},
        ]
    }
    res = aplicar_anonimato_perfiles(datos, minimo=None)
    assert res["minimoAnonimato"] == settings.min_grupo_anonimato
    assert len(res["perfilesClusterKMeans"]) == 1
    assert res["perfilesClusterKMeans"][0]["clusterId"] == 2
    assert res["perfilesOmitidos"] == 1
