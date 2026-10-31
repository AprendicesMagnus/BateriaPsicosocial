import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { descargarExportacionPanel, fetchVentasProductos } from "../api/panel";
import "../styles/PanelAcciones.css";
import "../styles/PanelVentasProductos.css";

const cop = (n) => Number(n || 0).toLocaleString("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const etiquetas = { PENDIENTE: "Pendientes", PAGADA: "Pagados", ENVIADO: "Enviados", ENTREGADO: "Entregados", CANCELADA: "Cancelados", RECHAZADO: "Pago rechazado", EXPIRADA: "Expirados", ERROR: "Error" };

export default function PanelVentasProductos() {
  const { token } = useAuth();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(true);
  const [exportando, setExportando] = useState(false);
  useEffect(() => {
    let vigente = true;
    fetchVentasProductos(token).then((r) => vigente && setDatos(r)).catch((e) => vigente && setError(e.message || "No se pudieron cargar las ventas."))
      .finally(() => vigente && setCargando(false));
    return () => { vigente = false; };
  }, [token]);
  async function exportar() {
    setExportando(true);
    try { await descargarExportacionPanel(token, "historial_compras"); }
    catch (e) { setError(e.message || "No se pudo exportar el informe."); }
    finally { setExportando(false); }
  }
  return <section className="adm-card">
    <div className="adm-card__head"><div><h2>Panel de ventas</h2><span>Resumen de ingresos y movimiento de pedidos de productos.</span></div><button className="adm-btn adm-btn--borde" disabled={exportando} onClick={exportar}>{exportando ? "Exportando…" : "Exportar a Excel"}</button></div>
    {error && <p role="alert" className="plan-mensaje plan-mensaje--error">{error}</p>}
    {cargando ? <p className="adm-vacio">Cargando estadísticas…</p> : datos && <>
      <div className="ventas-resumen">
        <article><span>Ingresos totales</span><strong>{cop(datos.ingresosTotales)}</strong></article>
        <article><span>Ingresos del mes</span><strong>{cop(datos.ingresosMes)}</strong></article>
        <article><span>Pedidos pendientes</span><strong>{datos.pedidosPorEstado?.PENDIENTE || 0}</strong></article>
        <article><span>Pedidos cancelados</span><strong>{datos.pedidosPorEstado?.CANCELADA || 0}</strong></article>
      </div>
      <h3>Ingresos por mes</h3><div className="adm-tabla-wrap"><table className="adm-tabla"><thead><tr><th>Mes</th><th>Ingresos confirmados</th></tr></thead><tbody>{(datos.ingresosPorMes || []).map((p) => <tr key={p.mes}><td>{p.mes}</td><td>{cop(p.ingresos)}</td></tr>)}{!datos.ingresosPorMes?.length && <tr><td colSpan="2" className="adm-vacio">Aún no hay ingresos confirmados.</td></tr>}</tbody></table></div>
      <h3>Pedidos por estado</h3><div className="adm-tabla-wrap"><table className="adm-tabla"><thead><tr><th>Estado</th><th>Cantidad</th></tr></thead><tbody>{Object.entries(datos.pedidosPorEstado || {}).map(([estado, cantidad]) => <tr key={estado}><td>{etiquetas[estado] || estado}</td><td>{cantidad}</td></tr>)}{!Object.keys(datos.pedidosPorEstado || {}).length && <tr><td colSpan="2" className="adm-vacio">No hay pedidos registrados.</td></tr>}</tbody></table></div>
      <h3>Productos más vendidos</h3><div className="adm-tabla-wrap"><table className="adm-tabla"><thead><tr><th>Producto</th><th>Unidades vendidas</th><th>Ventas</th></tr></thead><tbody>{(datos.productosMasVendidos || []).map((p) => <tr key={p.producto}><td>{p.producto}</td><td>{p.unidades}</td><td>{cop(p.total)}</td></tr>)}{!datos.productosMasVendidos?.length && <tr><td colSpan="3" className="adm-vacio">Aún no hay ventas confirmadas.</td></tr>}</tbody></table></div>
    </>}
  </section>;
}
