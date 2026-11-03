import numpy as np

from app.services import prediccion as p


def _dos_grupos(n=10, dims=3, seed=0):
    rng = np.random.default_rng(seed)
    bajo = rng.normal(20, 3, size=(n, dims))
    alto = rng.normal(75, 3, size=(n, dims))
    return np.vstack([bajo, alto])


def test_elige_dos_perfiles_cuando_hay_dos_grupos_claros():
    from sklearn.preprocessing import StandardScaler

    X = StandardScaler().fit_transform(_dos_grupos())
    k, silueta = p._elegir_clusters(X, len(np.unique(X, axis=0)))
    assert k == 2 and silueta > 0.5
    assert "Buena" in p._lectura_silueta(silueta)


def test_muestra_muy_pequena_no_intenta_separar():
    X = np.array([[1.0, 2.0], [1.0, 2.0]])
    assert p._elegir_clusters(X, 1) == (1, None)
    assert "insuficiente" in p._lectura_silueta(None)


def test_descripcion_del_perfil_nombra_lo_que_lo_distingue():
    altos = [{"dimension": "Demandas emocionales", "promedio": 80.0, "diferencia": 22.5}]
    bajos = [{"dimension": "Recompensas", "promedio": 10.0, "diferencia": -9.0}]
    texto = p._describir_perfil(altos, bajos)
    assert "Demandas emocionales (+22.5 pts)" in texto and "Recompensas (-9.0 pts)" in texto
    assert "similar al promedio" in p._describir_perfil([], [])


def test_dimensiones_relacionadas_solo_con_muestra_suficiente():
    X = _dos_grupos(n=6)
    assert len(p._dimensiones_relacionadas(X[:5], ["A", "B", "C"])) == 0  # menos de 8 personas
    pares = p._dimensiones_relacionadas(X, ["A", "B", "C"])
    assert pares and all(abs(x["correlacion"]) >= 0.7 for x in pares)


def test_dimensiones_constantes_no_rompen_la_correlacion():
    X = np.column_stack([np.full(10, 50.0), np.arange(10.0)])
    assert p._dimensiones_relacionadas(X, ["Constante", "Variable"]) == []


def test_resumen_y_recomendaciones():
    incidencia = [
        {"dimension": "Liderazgo", "promedioPuntaje": 70.0, "porcentajeRiesgoCritico": 60.0},
        {"dimension": "Control", "promedioPuntaje": 20.0, "porcentajeRiesgoCritico": 0.0},
    ]
    alertas = [{"dimension": "Liderazgo", "nivelAlerta": "ALTA", "mensaje": "x"}]
    texto = p._resumen_interpretativo(12, incidencia, alertas, 2)
    assert "12 cuestionario(s)" in texto and "Liderazgo (60.0%)" in texto and "1 alerta(s)" in texto and "2 perfiles" in texto
    assert "jefes" in p._recomendacion_para("Liderazgo y relaciones sociales", "Relaciones")
    assert p._recomendacion_para(None, "Otra cosa") == p.RECOMENDACION_GENERAL
