import hashlib
import hmac

import httpx

from app.core.config import get_settings


def get_wompi_api_url() -> str:
    return get_settings().wompi_api_url.strip().rstrip("/")


def get_wompi_public_key() -> str:
    return get_settings().wompi_public_key.strip()


def get_wompi_private_key() -> str:
    return get_settings().wompi_private_key.strip()


def get_wompi_integrity_secret() -> str:
    return get_settings().wompi_integrity_secret.strip()


def get_wompi_events_secret() -> str:
    return get_settings().wompi_events_secret.strip()


def require_public_configuration() -> str:
    public_key = get_wompi_public_key()

    if not public_key:
        raise RuntimeError(
            "WOMPI_PUBLIC_KEY no está configurado."
        )

    return public_key


def generate_integrity_signature(
    reference: str,
    amount_in_cents: int,
    currency: str = "COP",
) -> str:
    secret = get_wompi_integrity_secret()

    if not secret:
        raise RuntimeError(
            "WOMPI_INTEGRITY_SECRET no está configurado."
        )

    reference = reference.strip()
    currency = currency.strip().upper()

    if not reference:
        raise ValueError("La referencia es obligatoria.")

    if amount_in_cents <= 0:
        raise ValueError("El monto debe ser mayor que cero.")

    if currency != "COP":
        raise ValueError("La moneda debe ser COP.")

    cadena = f"{reference}{amount_in_cents}{currency}{secret}"

    return hashlib.sha256(
        cadena.encode("utf-8")
    ).hexdigest()


def consultar_transaccion(transaction_id: str) -> dict:
    """
    Consulta una transacción en Wompi usando la llave privada.
    Esta función debe ejecutarse únicamente en el backend.
    """

    private_key = get_wompi_private_key()

    if not private_key:
        raise RuntimeError(
            "WOMPI_PRIVATE_KEY no está configurado."
        )

    transaction_id = transaction_id.strip()

    if not transaction_id:
        raise ValueError(
            "El ID de la transacción de Wompi es obligatorio."
        )

    api_url = get_wompi_api_url()

    if not api_url:
        raise RuntimeError(
            "WOMPI_API_URL no está configurado."
        )

    url = f"{api_url}/transactions/{transaction_id}"

    headers = {
        "Authorization": f"Bearer {private_key}",
        "Accept": "application/json",
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            timeout=httpx.Timeout(
                connect=5.0,
                read=15.0,
                write=5.0,
                pool=5.0,
            ),
        )

        response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "La consulta a Wompi excedió el tiempo de espera."
        ) from exc

    except httpx.RequestError as exc:
        raise RuntimeError(
            "No fue posible comunicarse con Wompi."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Wompi respondió con HTTP {exc.response.status_code}."
        ) from exc

    try:
        resultado = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "Wompi devolvió una respuesta que no es JSON válido."
        ) from exc

    if not isinstance(resultado, dict):
        raise RuntimeError(
            "Wompi devolvió una respuesta con formato inesperado."
        )

    return resultado


def validar_firma_evento(
    properties: list[str],
    signature_checksum: str,
    timestamp: int,
    data: dict,
) -> bool:
    """
    Valida la firma de seguridad enviada por Wompi
    en los eventos webhook.
    """

    events_secret = get_wompi_events_secret()

    if not events_secret:
        raise RuntimeError(
            "WOMPI_EVENTS_SECRET no está configurado."
        )

    if not isinstance(properties, list):
        return False

    if not properties:
        return False

    if not isinstance(signature_checksum, str):
        return False

    signature_checksum = signature_checksum.strip().lower()

    if not signature_checksum:
        return False

    if len(signature_checksum) != 64:
        return False

    try:
        int(signature_checksum, 16)
    except ValueError:
        return False

    if not isinstance(timestamp, int):
        return False

    if not isinstance(data, dict):
        return False

    def obtener_valor(objeto: dict, ruta: str):
        if not isinstance(ruta, str) or not ruta.strip():
            return None

        valor = objeto

        for parte in ruta.split("."):
            if not isinstance(valor, dict):
                return None

            valor = valor.get(parte)

        return valor

    valores = []

    for propiedad in properties:
        valor = obtener_valor(data, propiedad)

        if valor is None:
            return False

        valores.append(str(valor))

    cadena = (
        "".join(valores)
        + str(timestamp)
        + events_secret
    )

    firma_calculada = hashlib.sha256(
        cadena.encode("utf-8")
    ).hexdigest()

    return hmac.compare_digest(
        firma_calculada,
        signature_checksum,
    )
