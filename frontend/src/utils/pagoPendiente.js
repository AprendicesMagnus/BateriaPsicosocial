import request from "../api/client";

// ==================================================
// PAGO EN CURSO
// ==================================================
//
// Guarda en el navegador la referencia del pago que el usuario
// está haciendo en el widget de Wompi. Sirve para dos cosas:
//
//   1. Advertir antes de cerrar sesión mientras hay un pago en curso.
//   2. Recuperar el resultado cuando el usuario vuelve a iniciar
//      sesión, aunque el callback del widget no haya podido
//      confirmarlo con el backend (sesión cerrada o vencida).
//
// No se guarda ningún dato sensible: solo ids y la referencia.
// Tampoco se borra al cerrar sesión; queda ligado al usuario que
// inició el pago, así otra persona que use el mismo equipo no lo ve.

const CLAVE = "magnussing_pago_pendiente";
const VIGENCIA_RECUPERACION_MS = 24 * 60 * 60 * 1000;
const VENTANA_ADVERTENCIA_MS = 30 * 60 * 1000;

function leer() {
    try {
        return JSON.parse(localStorage.getItem(CLAVE));
    } catch {
        return null;
    }
}

export function guardarPagoPendiente({ usuarioId, compraId, reference }) {
    try {
        localStorage.setItem(
            CLAVE,
            JSON.stringify({
                usuarioId: usuarioId ? String(usuarioId) : null,
                compraId,
                reference,
                transactionId: null,
                creadoEn: Date.now(),
            })
        );
    } catch {
        // Si el navegador no permite guardar, el pago sigue funcionando igual.
    }
}

export function actualizarPagoPendiente(cambios) {
    const actual = leer();
    if (!actual) return;
    try {
        localStorage.setItem(CLAVE, JSON.stringify({ ...actual, ...cambios }));
    } catch {
        // Ver comentario en guardarPagoPendiente.
    }
}

export function limpiarPagoPendiente() {
    try {
        localStorage.removeItem(CLAVE);
    } catch {
        // Sin acción posible.
    }
}

export function obtenerPagoPendiente(usuarioId) {
    const registro = leer();
    if (!registro) return null;

    if (Date.now() - registro.creadoEn > VIGENCIA_RECUPERACION_MS) {
        limpiarPagoPendiente();
        return null;
    }

    if (usuarioId && registro.usuarioId !== String(usuarioId)) {
        return null;
    }

    return registro;
}

// true si hay un pago iniciado hace menos de 30 minutos.
export function hayPagoEnCurso(usuarioId) {
    const registro = obtenerPagoPendiente(usuarioId);
    return Boolean(registro) && Date.now() - registro.creadoEn < VENTANA_ADVERTENCIA_MS;
}

const MENSAJES = {
    PAGADA: "Tu pago fue confirmado. Tu compra quedó registrada correctamente.",
    RECHAZADO: "El pago fue rechazado. El resultado quedó registrado en tu historial de compras.",
    ERROR: "Wompi reportó un error al procesar el pago. El resultado quedó registrado en tu historial de compras.",
    EXPIRADA: "La compra expiró. Si alcanzaste a pagar, Wompi confirmará el pago y lo verás reflejado en tu historial de compras.",
    CANCELADA: "La compra fue cancelada.",
};

// Revisa el resultado de un pago que quedó en curso (por ejemplo,
// porque el usuario cerró sesión antes de que se confirmara).
//
// Devuelve { estado, mensaje } si había algo que revisar, o null.
export async function recuperarPagoPendiente({ usuarioId, token }) {
    const pendiente = obtenerPagoPendiente(usuarioId);
    if (!pendiente) return null;

    try {
        // El backend consulta a Wompi si la transacción ya es conocida.
        let compra = await request(`/compras/${pendiente.compraId}`, { token });

        // Si el widget alcanzó a devolver la transacción pero el backend
        // nunca se enteró (sesión cerrada antes de confirmarla), se la
        // informamos ahora. El backend la valida directamente con Wompi.
        if (
            pendiente.transactionId &&
            (compra.estado === "PENDIENTE" || compra.estado === "EXPIRADA")
        ) {
            try {
                await request("/pagos", {
                    method: "POST",
                    token,
                    body: {
                        compraId: pendiente.compraId,
                        wompiTransactionId: pendiente.transactionId,
                    },
                });
                compra = await request(`/compras/${pendiente.compraId}`, { token });
            } catch (err) {
                if (err.status === 401) throw err;
                // Otro rechazo: se conserva el estado que ya tenía la compra.
            }
        }

        if (compra.estado === "PENDIENTE") {
            return pendiente.transactionId
                ? {
                    estado: compra.estado,
                    mensaje:
                        "Tu pago sigue pendiente de confirmación. Puedes revisar su estado desde tu historial de compras.",
                }
                : null;
        }

        limpiarPagoPendiente();

        return {
            estado: compra.estado,
            mensaje: MENSAJES[compra.estado] || null,
        };
    } catch {
        // Sin conexión o sesión vencida: el registro se conserva
        // y se vuelve a intentar la próxima vez.
        return null;
    }
}