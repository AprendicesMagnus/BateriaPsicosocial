"""
Utilidad para cálculo y validación del Dígito de Verificación (DV) de NIT colombiano.
Algoritmo de la DIAN (Módulo 11).
"""

PESOS = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]


def calcular_digito_verificador_nit(nit_base: str) -> int:
    """
    Calcula el dígito de verificación (DV) de un NIT numérico según el algoritmo DIAN (Módulo 11).
    :param nit_base: Cadena con los dígitos base del NIT (sin guion ni DV, ej. "899999068").
    :return: Entero del dígito verificador (0 a 9).
    """
    digitos_limpios = [int(c) for c in nit_base if c.isdigit()]
    if not digitos_limpios:
        raise ValueError("El NIT base debe contener al menos un dígito numérico.")

    # Asignación de pesos de derecha a izquierda
    suma = 0
    for i, digito in enumerate(reversed(digitos_limpios)):
        peso = PESOS[i % len(PESOS)]
        suma += digito * peso

    residuo = suma % 11

    if residuo == 0 or residuo == 1:
        return residuo
    return 11 - residuo


def nit_valido(nit_completo: str) -> bool:
    """
    Valida si un NIT completo en formato "123456789-0" o "1234567890" es válido según el DV DIAN.
    """
    if not nit_completo:
        return False

    cadena = nit_completo.strip()
    if "-" in cadena:
        partes = cadena.split("-")
        if len(partes) != 2:
            return False
        base, dv_str = partes[0], partes[1]
    else:
        if len(cadena) < 2:
            return False
        base, dv_str = cadena[:-1], cadena[-1]

    if not base.isdigit() or not dv_str.isdigit():
        return False

    try:
        dv_calculado = calcular_digito_verificador_nit(base)
        return int(dv_str) == dv_calculado
    except ValueError:
        return False


def validar_nit_con_dv(nit: str) -> None:
    """
    Valida que un NIT no sea vacío, tenga formato '#########-#' y que su Dígito de Verificación coincida.
    Lanza AppError(400, ...) en caso de cualquier inconsistencia.
    """
    from app.core.errors import AppError

    if not nit or not isinstance(nit, str):
        raise AppError(400, "El NIT es obligatorio.")
    nit_limpio = nit.strip()
    if "-" not in nit_limpio:
        raise AppError(400, "El NIT debe estar en formato 900123456-7 (9 dígitos base, guion y dígito verificador).")
    partes = nit_limpio.split("-")
    if len(partes) != 2 or not partes[0].isdigit() or not partes[1].isdigit() or len(partes[0]) != 9 or len(partes[1]) != 1:
        raise AppError(400, "El NIT debe estar en formato 900123456-7 (9 dígitos base, guion y dígito verificador).")
    nit_base, dv_str = partes[0], partes[1]
    if calcular_digito_verificador_nit(nit_base) != int(dv_str):
        raise AppError(400, "El dígito de verificación del NIT no es válido.")

