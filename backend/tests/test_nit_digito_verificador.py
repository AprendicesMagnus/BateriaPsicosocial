"""
Tests unitarios del Dígito de Verificación (DV) de NIT colombiano (Módulo 11 DIAN).
Usa NITs reales y públicos de entidades colombianas conocidas para asegurar la exactitud del algoritmo.
"""

from app.core.nit_utils import calcular_digito_verificador_nit, nit_valido


def test_ecopetrol_nit_real():
    # ECOPETROL S.A.: NIT 899999068-1
    base = "899999068"
    dv_esperado = 1
    assert calcular_digito_verificador_nit(base) == dv_esperado
    assert nit_valido("899999068-1") is True
    assert nit_valido("899999068-2") is False


def test_banco_de_bogota_nit_real():
    # BANCO DE BOGOTA S.A.: NIT 860003020-1
    base = "860003020"
    dv_esperado = 1
    assert calcular_digito_verificador_nit(base) == dv_esperado
    assert nit_valido("860003020-1") is True
    assert nit_valido("860003020-5") is False


def test_dian_nit_real():
    # DIAN (Dirección de Impuestos y Aduanas Nacionales): NIT 800197268-4
    base = "800197268"
    dv_esperado = 4
    assert calcular_digito_verificador_nit(base) == dv_esperado
    assert nit_valido("800197268-4") is True
    assert nit_valido("800197268-0") is False


def test_bavaria_nit_real():
    # BAVARIA S.A.: NIT 860005224-6
    base = "860005224"
    dv_esperado = 6
    assert calcular_digito_verificador_nit(base) == dv_esperado
    assert nit_valido("860005224-6") is True
    assert nit_valido("860005224-1") is False


def test_mineducacion_nit_real():
    # MINISTERIO DE EDUCACIÓN NACIONAL: NIT 899999001-7
    base = "899999001"
    dv_esperado = 7
    assert calcular_digito_verificador_nit(base) == dv_esperado
    assert nit_valido("899999001-7") is True
