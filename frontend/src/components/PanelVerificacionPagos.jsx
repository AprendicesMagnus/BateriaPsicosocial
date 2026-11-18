import { useEffect, useState } from "react";
import { request, API_URL } from "../api/client";
import { useAuth } from "../context/AuthContext";
import "../styles/PanelVerificacionPagos.css";

const pesos = (n) => Number(n || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function PanelVerificacionPagos() {
  const { token } = useAuth();
  const [estado, setEstado] = useState("PENDIENTE_VERIFICACION");
  const [pagos, setPagos] = useState([]);
  const [qr, setQr] = useState(null);
  const [configuracion, setConfiguracion] = useState({ llave: "", titular: "" });
  const [cargandoConfig, setCargandoConfig] = useState(true);
  const [guardandoConfig, setGuardandoConfig] = useState(false);
  const [mensajeConfig, setMensajeConfig] = useState("");
  const [errorConfig, setErrorConfig] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState("");

  async function cargar() {
    setCargando(true); setError("");
    try { setPagos(await request(`/pagos-nequi/administracion?estado=${estado}`, { token })); }
    catch (e) { setError(e.message); }
    finally { setCargando(false); }
  }
  useEffect(() => { cargar(); }, [estado, token]);

  async function cargarConfiguracion() {
    setCargandoConfig(true);
    setErrorConfig("");
    try {
      const data = await request("/pagos-nequi/configuracion", { token });
      setConfiguracion({ llave: data.llave || "", titular: data.titular || "" });
    } catch (e) {
      setErrorConfig(e.message || "No se pudo cargar la configuración de Nequi.");
    } finally {
      setCargandoConfig(false);
    }
  }

  useEffect(() => { cargarConfiguracion(); }, [token]);

  async function guardarConfiguracion(e) {
    e.preventDefault();
    setGuardandoConfig(true);
    setErrorConfig("");
    setMensajeConfig("");
    try {
      const data = await request("/pagos-nequi/configuracion", {
        method: "PUT",
        body: {
          llave: configuracion.llave.trim(),
          titular: configuracion.titular.trim(),
        },
        token,
      });
      setConfiguracion({ llave: data.llave, titular: data.titular });
      setMensajeConfig("Los datos de Nequi se actualizaron correctamente y se mostrarán en ambos procesos de pago.");
    } catch (e) {
      setErrorConfig(e.message || "No se pudo guardar la configuración de Nequi.");
    } finally {
      setGuardandoConfig(false);
    }
  }

  async function guardarQr() {
    if (!qr) return;
    const body = new FormData(); body.append("file", qr);
    setOcupado("qr"); setError("");
    try { await request("/pagos-nequi/qr", { method: "PUT", body, token }); setQr(null); }
    catch (e) { setError(e.message); }
    finally { setOcupado(""); }
  }

  async function verComprobante(item) {
    try {
      const response = await fetch(`${API_URL}/pagos-nequi/comprobante/${item.tipo}/${item.compraId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) throw new Error("No fue posible abrir el comprobante.");
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.target = "_blank"; link.rel = "noreferrer"; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (e) { setError(e.message); }
  }

  async function revisar(item, accion) {
    let observaciones = "";
    if (accion === "rechazar") {
      observaciones = window.prompt("Indica el motivo del rechazo:")?.trim() || "";
      if (!observaciones) return;
    }
    const key = `${item.tipo}-${item.compraId}`; setOcupado(key); setError("");
    try {
      const suffix = accion === "rechazar" ? `?observaciones=${encodeURIComponent(observaciones)}` : "";
      await request(`/pagos-nequi/administracion/${item.tipo}/${item.compraId}/${accion}${suffix}`, { method: "POST", token });
      await cargar();
    } catch (e) { setError(e.message); }
    finally { setOcupado(""); }
  }

  return <section className="adm-card verificacion-pagos">
    <div className="adm-card__head"><div><h2>Verificación de pagos Nequi</h2><span>Revisa los comprobantes antes de habilitar baterías o confirmar pedidos.</span></div></div>
    <div className="verificacion-pagos__qr"><div><strong>Código QR de Nequi Negocios</strong><p>Actualiza la imagen utilizada en los pagos de baterías y productos.</p></div><input type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" onChange={(e) => setQr(e.target.files?.[0] || null)} /><button type="button" className="adm-btn adm-btn--borde" disabled={!qr || ocupado === "qr"} onClick={guardarQr}>{ocupado === "qr" ? "Guardando…" : "Actualizar QR"}</button></div>
    <form className="verificacion-pagos__configuracion" onSubmit={guardarConfiguracion}>
      <div className="verificacion-pagos__configuracion-head">
        <div>
          <h3>Datos de la cuenta Nequi</h3>
          <p>Estos datos aparecen junto al QR en los pagos de baterías y productos.</p>
        </div>
      </div>
      {errorConfig && <p className="verificacion-pagos__error" role="alert">{errorConfig}</p>}
      {mensajeConfig && <p className="verificacion-pagos__exito" role="status">{mensajeConfig}</p>}
      <div className="verificacion-pagos__campos-config">
        <label>
          Llave Bre-B
          <input
            type="text"
            value={configuracion.llave}
            onChange={(e) => setConfiguracion((actual) => ({ ...actual, llave: e.target.value }))}
            maxLength={60}
            placeholder="Ej. 322 712 2675"
            autoComplete="off"
            disabled={cargandoConfig || guardandoConfig}
            required
          />
        </label>
        <label>
          Nombre del titular
          <input
            type="text"
            value={configuracion.titular}
            onChange={(e) => setConfiguracion((actual) => ({ ...actual, titular: e.target.value }))}
            maxLength={100}
            placeholder="Nombre de quien recibe el pago"
            autoComplete="off"
            disabled={cargandoConfig || guardandoConfig}
            required
          />
        </label>
      </div>
      <div className="verificacion-pagos__configuracion-pie">
        <small>La actualización se guarda en el backend y no modifica los comprobantes ni las compras anteriores.</small>
        <button type="submit" className="adm-btn adm-btn--oscuro" disabled={cargandoConfig || guardandoConfig || !configuracion.llave.trim() || !configuracion.titular.trim()}>
          {cargandoConfig ? "Cargando datos…" : guardandoConfig ? "Guardando…" : "Guardar datos de Nequi"}
        </button>
      </div>
    </form>
    <div className="verificacion-pagos__filtros"><label htmlFor="estado-pagos-nequi">Mostrar</label><select id="estado-pagos-nequi" value={estado} onChange={(e) => setEstado(e.target.value)}><option value="PENDIENTE_VERIFICACION">Pendientes de verificación</option><option value="APROBADO">Pagos aprobados</option><option value="RECHAZADO">Pagos rechazados</option></select><button type="button" className="adm-btn adm-btn--borde" onClick={cargar}>Actualizar</button></div>
    {error && <p className="verificacion-pagos__error">{error}</p>}
    {cargando ? <p className="adm-vacio">Cargando pagos…</p> : !pagos.length ? <p className="adm-vacio">No hay pagos en este estado.</p> : <div className="verificacion-pagos__lista">{pagos.map((item) => <article className="verificacion-pagos__item" key={`${item.tipo}-${item.compraId}`}>
      <div className="verificacion-pagos__datos"><strong>{item.usuario}</strong><span>{item.tipo === "bateria" ? "Baterías" : "Productos"} · {item.producto}</span><span>Empresa: {item.empresa || "Sin empresa asociada"}</span><span>{new Date(item.fecha).toLocaleString("es-CO")}</span><b>{pesos(item.total)}</b><small>Referencia: {item.pago.referencia}</small>{item.pago.observaciones && <p>Observación: {item.pago.observaciones}</p>}{item.pago.revisadoPor && <small>Revisado por {item.pago.revisadoPor} · {new Date(item.pago.revisadoEn).toLocaleString("es-CO")}</small>}</div>
      {item.pago.comprobanteUrl && <button type="button" className="verificacion-pagos__comprobante" onClick={() => verComprobante(item)}>Ver comprobante</button>}
      {estado === "PENDIENTE_VERIFICACION" && <div className="verificacion-pagos__acciones"><button type="button" disabled={Boolean(ocupado)} onClick={() => revisar(item, "aprobar")}>Aprobar pago</button><button type="button" disabled={Boolean(ocupado)} onClick={() => revisar(item, "rechazar")}>Rechazar</button></div>}
    </article>)}</div>}
  </section>;
}
