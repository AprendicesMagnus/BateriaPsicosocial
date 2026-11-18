import { useEffect, useState } from "react";
import { API_URL, request } from "../api/client";
import "../styles/PagoNequi.css";

export default function PagoNequi({ tipo, compraId, token, total, onComplete }) {
  const [pago, setPago] = useState(null);
  const [archivo, setArchivo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [enviado, setEnviado] = useState(false);

  useEffect(() => {
    let activo = true;
    request(`/pagos-nequi/${tipo}/${compraId}/iniciar`, { method: "POST", token })
      .then((data) => {
        if (activo) setPago(data);
      })
      .catch((err) => {
        if (activo) setError(err.message);
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [tipo, compraId, token]);

  async function enviarComprobante() {
    if (!archivo || enviando) return;
    setError("");
    setEnviando(true);
    try {
      const body = new FormData();
      body.append("file", archivo);
      await request(`/pagos-nequi/${tipo}/${compraId}/comprobante`, {
        method: "POST",
        body,
        token,
      });
      setEnviado(true);
      onComplete?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  if (cargando) {
    return (
      <div className="pago-nequi">
        <p>Preparando el pago seguro…</p>
      </div>
    );
  }

  return (
    <section className="pago-nequi">
      <div className="pago-nequi__encabezado">
        <span>Pago mediante Nequi</span>
        <h2>Escanea el código QR</h2>
        <p>Realiza la transferencia por el valor exacto y adjunta el comprobante.</p>
      </div>

      {error && <p className="pago-nequi__error" role="alert">{error}</p>}

      {pago && (
        <>
          <div className="pago-nequi__contenido">
            <div className="pago-nequi__qr">
              <img
                src={`${API_URL}/pagos-nequi/qr`}
                alt="Código QR de Nequi Negocios"
              />
              <div className="pago-nequi__llave">
                <span>Llave Bre-B</span>
                <strong>{pago.llave || "Consulta la llave con el administrador"}</strong>
                <small>Titular: {pago.titular || "No configurado"}</small>
              </div>
            </div>

            <div className="pago-nequi__detalle">
              <span>Valor exacto a transferir</span>
              <strong>
                ${Math.round(Number(pago.total ?? pago.pago?.monto ?? total)).toLocaleString("es-CO")} COP
              </strong>
              <p>1. Abre Nequi y escanea el QR.</p>
              <p>2. Verifica el valor antes de confirmar.</p>
              <p>3. Realiza la transferencia y guarda el comprobante.</p>
              <small>Referencia: {pago.pago?.referencia}</small>
            </div>
          </div>

          {enviado || pago.pago?.estado === "PENDIENTE_VERIFICACION" ? (
            <div className="pago-nequi__exito">
              <strong>Comprobante recibido.</strong>
              <p>
                Tu compra quedó pendiente de verificación administrativa. No se
                habilitarán baterías ni se confirmará el pedido hasta que se
                apruebe el pago.
              </p>
            </div>
          ) : (
            <div className="pago-nequi__subida">
              <label htmlFor="nequi-comprobante">
                Adjuntar comprobante (JPG, JPEG o PNG; máximo 5 MB)
              </label>
              <input
                id="nequi-comprobante"
                type="file"
                accept="image/jpeg,image/png,.jpg,.jpeg,.png"
                onChange={(e) => setArchivo(e.target.files?.[0] || null)}
              />
              <button
                type="button"
                className="pago-nequi__boton"
                disabled={!archivo || enviando}
                onClick={enviarComprobante}
              >
                {enviando ? "Enviando comprobante…" : "Enviar comprobante"}
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
