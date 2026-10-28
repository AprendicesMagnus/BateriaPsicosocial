import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { descargarExportacionPanel, fetchHistorialComprasTienda } from "../api/panel";
import "../styles/PanelHistorialCompras.css";

const formatoFecha = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "2-digit", year: "numeric" })
    : "—";

const formatoHora = (iso) =>
  iso
    ? new Date(iso).toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "—";

const formatoPesos = (valor) =>
  Number(valor || 0).toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  });

const etiquetaEstado = (estado) => ({
  PAGADA: "Aprobada",
  PAGADO: "Aprobada",
  PENDIENTE: "Pendiente",
  RECHAZADO: "Rechazada",
  RECHAZADA: "Rechazada",
  EXPIRADA: "Expirada",
  CANCELADA: "Cancelada",
  ANULADO: "Anulada",
  ERROR: "Error",
}[estado] || estado || "—");

export default function PanelHistorialCompras() {
  const { token } = useAuth();
  const [compras, setCompras] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [exportando, setExportando] = useState(false);

  useEffect(() => {
    let activo = true;
    setCargando(true);
    fetchHistorialComprasTienda(token)
      .then((res) => activo && setCompras(Array.isArray(res) ? res : []))
      .catch((err) => activo && setError(err.message || "No fue posible cargar el historial de compras."))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, [token]);

  async function exportar() {
    setExportando(true);
    try {
      await descargarExportacionPanel(token, "historial_compras");
    } catch (err) {
      setError(err.message || "No fue posible exportar el historial de compras.");
    } finally {
      setExportando(false);
    }
  }

  return (
    <section className="adm-card historial-compras">
      <div className="adm-card__head">
        <div>
          <h2>Historial de compras</h2>
          <span>Todas las compras registradas de planes de baterías y productos.</span>
        </div>
        <button
          type="button"
          className="adm-btn adm-btn--borde"
          disabled={exportando || cargando}
          onClick={exportar}
        >
          {exportando ? "Exportando..." : "Exportar a Excel"}
        </button>
      </div>

      {error && <p className="historial-compras__error">{error}</p>}
      {cargando ? (
        <p className="adm-vacio">Cargando historial de compras…</p>
      ) : (
        <div className="adm-tabla-wrap">
          <table className="adm-tabla">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Nombre del comprador</th>
                <th>Empresa</th>
                <th>Tipo</th>
                <th>Detalle</th>
                <th>Valor</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {compras.map((compra) => (
                <tr key={`${compra.tipo}-${compra.id}`}>
                  <td className="adm-muted">{formatoFecha(compra.fecha)}</td>
                  <td className="adm-muted">{formatoHora(compra.fecha)}</td>
                  <td><strong className="adm-fuerte">{compra.nombre}</strong></td>
                  <td>{compra.empresa}</td>
                  <td>{compra.tipo}</td>
                  <td>{compra.detalle}</td>
                  <td>{formatoPesos(compra.total)}</td>
                  <td><span className="adm-chip adm-chip--info">{etiquetaEstado(compra.estado)}</span></td>
                </tr>
              ))}
              {compras.length === 0 && (
                <tr><td colSpan={8} className="adm-vacio">Aún no hay compras registradas.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
