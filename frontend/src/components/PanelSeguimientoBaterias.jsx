import { useEffect, useMemo, useState } from "react";
import { descargarExportacionPanel, fetchSeguimientoBaterias } from "../api/panel";
import "../styles/PanelSeguimientoBaterias.css";

const PESOS = (n) => Number(n || 0).toLocaleString("es-CO");
const FECHA = (valor) => valor ? new Date(valor).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" }) : "—";
const ESTADOS = {
  DISPONIBLES: "Disponible",
  POR_AGOTARSE: "Por agotarse",
  AGOTADAS: "Agotadas",
  SIN_COMPRA: "Sin compra",
  SIN_COMPRA_PROPIA: "Sin compra propia",
  SALDO_COMPARTIDO: "Usa saldo de empresa",
  USA_SALDO_EMPRESA: "Usa saldo de empresa",
  EMPRESA_SIN_COMPRA: "Empresa sin compra",
  EMPRESA_AGOTADA: "Empresa agotada",
};

export default function PanelSeguimientoBaterias({ token }) {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [vista, setVista] = useState("empresas");
  const [busqueda, setBusqueda] = useState("");
  const [empresaFiltro, setEmpresaFiltro] = useState("TODAS");
  const [tipoFiltro, setTipoFiltro] = useState("TODOS");
  const [usuarioFiltro, setUsuarioFiltro] = useState("TODOS");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [exportando, setExportando] = useState(false);

  async function cargar() {
    setCargando(true);
    setError("");
    try {
      setDatos(await fetchSeguimientoBaterias(token));
    } catch (e) {
      setError(e.message || "No se pudo cargar el seguimiento de baterías.");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => { if (token) cargar(); }, [token]);

  async function exportar() {
    setExportando(true);
    try {
      await descargarExportacionPanel(token, "seguimiento_baterias");
    } catch (e) {
      setError(e.message || "No se pudo exportar el seguimiento.");
    } finally {
      setExportando(false);
    }
  }

  const q = busqueda.trim().toLocaleLowerCase("es");
  const empresas = useMemo(() => (datos?.empresas || []).filter((e) =>
    (!q || `${e.nombre} ${e.nit} ${e.responsable}`.toLocaleLowerCase("es").includes(q))
  ), [datos, q]);
  const usuarios = useMemo(() => (datos?.usuarios || []).filter((u) =>
    (empresaFiltro === "TODAS" || u.empresaId === empresaFiltro) &&
    (!q || `${u.nombre} ${u.correo} ${u.empresa} ${u.rol}`.toLocaleLowerCase("es").includes(q))
  ), [datos, q, empresaFiltro]);
  const movimientos = useMemo(() => (datos?.movimientos || []).filter((m) => {
    const fechaLocal = new Date(m.fecha).toLocaleDateString("en-CA", { timeZone: "America/Bogota" });
    return (empresaFiltro === "TODAS" || m.empresaId === empresaFiltro) &&
      (tipoFiltro === "TODOS" || m.tipo === tipoFiltro) &&
      (usuarioFiltro === "TODOS" || m.usuarioId === usuarioFiltro) &&
      (!desde || fechaLocal >= desde) && (!hasta || fechaLocal <= hasta) &&
      (!q || `${m.empresa} ${m.usuario} ${m.detalle} ${m.referencia}`.toLocaleLowerCase("es").includes(q));
  }), [datos, q, empresaFiltro, tipoFiltro, usuarioFiltro, desde, hasta]);

  const resumen = datos?.resumen || {};
  const metricas = [
    ["Baterías compradas", resumen.bateriasCompradas, "shopping-bag"],
    ["Baterías consumidas", resumen.bateriasConsumidas, "activity"],
    ["Disponibles", resumen.bateriasDisponibles, "battery-charging"],
    ["Compradas sin empresa", resumen.bateriasSinEmpresa, "alert-circle"],
    ["Empresas sin compra", resumen.empresasSinCompra, "building-2"],
    ["Empresas agotadas", resumen.empresasAgotadas, "battery-low"],
    ["Por agotarse (≤ 5)", resumen.empresasPorAgotarse, "alert-triangle"],
  ];

  return (
    <section className="adm-card adm-seguimiento-baterias">
      <div className="adm-card__head adm-seguimiento-baterias__head">
        <div>
          <h2>Seguimiento de baterías</h2>
          <span>Control de compras, consumo y disponibilidad por empresa y usuario.</span>
        </div>
        <div className="adm-seguimiento-baterias__acciones">
          <button type="button" className="adm-btn-secundario" onClick={cargar} disabled={cargando}>Actualizar</button>
          <button type="button" className="adm-btn-principal" onClick={exportar} disabled={exportando || cargando}>{exportando ? "Exportando…" : "Exportar Excel"}</button>
        </div>
      </div>

      {error && <p className="adm-seguimiento-baterias__error" role="alert">{error}</p>}

      <div className="adm-seguimiento-baterias__metricas">
        {metricas.map(([label, value]) => (
          <article className="adm-seguimiento-baterias__metrica" key={label}>
            <span>{label}</span>
            <strong>{cargando ? "…" : PESOS(value)}</strong>
          </article>
        ))}
      </div>

      <div className="adm-seguimiento-baterias__controles">
        <div className="adm-seguimiento-baterias__tabs" role="tablist" aria-label="Tipo de seguimiento">
          {[ ["empresas", "Por empresa"], ["usuarios", "Por usuario"], ["movimientos", "Movimientos"] ].map(([id, label]) => (
            <button key={id} type="button" role="tab" aria-selected={vista === id} className={vista === id ? "activo" : ""} onClick={() => setVista(id)}>{label}</button>
          ))}
        </div>
        <input type="search" className="adm-input" placeholder="Buscar empresa, usuario o movimiento…" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        {(vista === "usuarios" || vista === "movimientos") && (
          <select className="adm-input" value={empresaFiltro} onChange={(e) => setEmpresaFiltro(e.target.value)} aria-label="Filtrar por empresa">
            <option value="TODAS">Todas las empresas</option>
            {(datos?.empresas || []).map((e) => <option key={e.id} value={e.id}>{e.nombre}</option>)}
          </select>
        )}
        {vista === "movimientos" && (
          <>
            <select className="adm-input" value={tipoFiltro} onChange={(e) => setTipoFiltro(e.target.value)} aria-label="Filtrar tipo de movimiento">
              <option value="TODOS">Todos los movimientos</option>
              <option value="COMPRA">Compras aprobadas</option>
              <option value="CONSUMO">Baterías consumidas</option>
            </select>
            <select className="adm-input" value={usuarioFiltro} onChange={(e) => setUsuarioFiltro(e.target.value)} aria-label="Filtrar usuario">
              <option value="TODOS">Todos los usuarios</option>
              {Object.values((datos?.movimientos || []).reduce((acc, m) => { acc[m.usuarioId] = { id: m.usuarioId, nombre: m.usuario }; return acc; }, {})).sort((a, b) => a.nombre.localeCompare(b.nombre, "es")).map((u) => <option key={u.id} value={u.id}>{u.nombre}</option>)}
            </select>
            <label className="adm-seguimiento-baterias__fecha">Desde <input type="date" className="adm-input" value={desde} onChange={(e) => setDesde(e.target.value)} /></label>
            <label className="adm-seguimiento-baterias__fecha">Hasta <input type="date" className="adm-input" value={hasta} onChange={(e) => setHasta(e.target.value)} /></label>
          </>
        )}
      </div>

      {cargando ? <p className="adm-vacio">Cargando seguimiento…</p> : (
        <div className="adm-tabla-wrap" tabIndex={0}>
          {vista === "empresas" && (
            <table className="adm-tabla">
              <thead><tr><th>Empresa</th><th>Responsable SST</th><th>Usuarios</th><th>Compradas</th><th>Consumidas</th><th>Disponibles</th><th>Última compra</th><th>Estado</th></tr></thead>
              <tbody>{empresas.map((e) => <tr key={e.id}>
                <td><strong>{e.nombre}</strong><small className="adm-seguimiento-baterias__sub">NIT: {e.nit}</small></td>
                <td>{e.responsable}</td><td>{e.usuarios}</td><td>{PESOS(e.compradas)}</td><td>{PESOS(e.consumidas)}</td><td><strong>{PESOS(e.disponibles)}</strong></td><td>{FECHA(e.ultimaCompra)}</td>
                <td><span className={`adm-chip adm-seguimiento-baterias__estado adm-seguimiento-baterias__estado--${e.estado.toLowerCase()}`}>{ESTADOS[e.estado] || e.estado}</span></td>
              </tr>)}{empresas.length === 0 && <tr><td colSpan="8" className="adm-vacio">No hay empresas que coincidan con la búsqueda.</td></tr>}</tbody>
            </table>
          )}
          {vista === "usuarios" && (
            <table className="adm-tabla">
              <thead><tr><th>Usuario</th><th>Rol</th><th>Empresa</th><th>Compras propias</th><th>Baterías compradas</th><th>Consumo atribuible</th><th>Saldo empresa</th><th>Estado</th></tr></thead>
              <tbody>{usuarios.map((u) => <tr key={`${u.id}-${u.empresaId || "sin-empresa"}`}>
                <td><strong>{u.nombre}</strong><small className="adm-seguimiento-baterias__sub">{u.correo}</small></td><td>{u.rol === "EVALUADOR_SST" ? "Psicólogo" : u.rol === "RESPONSABLE_SST" ? "Responsable SST" : u.rol}</td><td>{u.empresa}</td><td>{u.compras}</td><td>{PESOS(u.compradas)}</td><td>{PESOS(u.consumidas)}</td><td>{PESOS(u.disponiblesEmpresa)}</td><td><span className="adm-chip">{ESTADOS[u.estado] || u.estado}</span></td>
              </tr>)}{usuarios.length === 0 && <tr><td colSpan="8" className="adm-vacio">No hay usuarios que coincidan con los filtros.</td></tr>}</tbody>
            </table>
          )}
          {vista === "movimientos" && (
            <table className="adm-tabla">
              <thead><tr><th>Fecha</th><th>Movimiento</th><th>Empresa</th><th>Usuario</th><th>Plan / detalle</th><th>Cantidad</th><th>Valor pagado</th><th>Referencia</th></tr></thead>
              <tbody>{movimientos.map((m) => <tr key={m.id}>
                <td>{FECHA(m.fecha)}</td><td><span className={`adm-chip ${m.tipo === "COMPRA" ? "adm-chip--info" : "adm-chip--aviso"}`}>{m.tipo === "COMPRA" ? "Compra aprobada" : "Consumo"}</span></td><td>{m.empresa}</td><td>{m.usuario}</td><td>{m.detalle}</td><td><strong>{m.cantidad > 0 ? `+${m.cantidad}` : m.cantidad}</strong></td><td>{m.valor ? `$${PESOS(m.valor)}` : "—"}</td><td className="adm-seguimiento-baterias__ref">{m.referencia}</td>
              </tr>)}{movimientos.length === 0 && <tr><td colSpan="8" className="adm-vacio">No hay movimientos para los filtros seleccionados.</td></tr>}</tbody>
            </table>
          )}
        </div>
      )}
      <p className="adm-seguimiento-baterias__nota">El consumo se registra una sola vez, al guardar la primera respuesta del paciente. Los enlaces creados o abiertos sin responder no descuentan baterías.</p>
    </section>
  );
}
