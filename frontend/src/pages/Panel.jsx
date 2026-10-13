import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  HiOutlineLink,
  HiOutlineLockClosed,
  HiOutlineCheckCircle,
  HiOutlineUser,
} from "react-icons/hi";
import { useAuth } from "../context/AuthContext";
import ProfileMenu from "../components/ProfileMenu";
import { fetchPanel } from "../api/panel";
import "../styles/dashboard.css";
import "../styles/Panel.css";
import BotonRegresar from "../components/BotonRegresar";
import Paginador from "../components/Paginador";
import { usePaginacion } from "../hooks/usePaginacion";

/* =========================================================
   CONFIGURACIÓN DE LA VISTA
   Los datos vienen de GET /api/panel (solo Super Administrador).
========================================================= */

// Código de rol (BD) -> etiqueta y sufijo de clase CSS (adm-chip--rol-...)
const ROLES = {
  SUPER_ADMINISTRADOR: { label: "Super Admin", clase: "superadmin" },
  EVALUADOR_SST: { label: "Psicólogo", clase: "psicologo" },
  RESPONSABLE_SST: { label: "Responsable SST", clase: "sst" },
  JEFE: { label: "Jefe", clase: "jefe" },
  TRABAJADOR: { label: "Trabajador", clase: "trabajador" },
};

// Estado (BD) -> etiqueta y sufijo de clase CSS (adm-chip--...)
const ESTADOS = {
  ACTIVO: { label: "Verificado", clase: "info" },
  PENDIENTE_CODIGO: { label: "Pendiente código", clase: "aviso" },
  INACTIVO: { label: "Desactivado", clase: "neutro" },
  PAGADA: { label: "Aprobado", clase: "info" },
  PENDIENTE: { label: "Pendiente", clase: "aviso" },
  RECHAZADA: { label: "Rechazado", clase: "peligro" },
};

// Tipo de evento de auditoría -> ícono y color
const TIPO_AUDITORIA = {
  Resultados: { icono: HiOutlineLockClosed, clase: "psicologo" },
  Consentimientos: { icono: HiOutlineCheckCircle, clase: "info" },
  Usuarios: { icono: HiOutlineUser, clase: "neutro" },
  Enlaces: { icono: HiOutlineLink, clase: "peligro" },
};

// Texto legible para las acciones registradas en auditoría
const TEXTO_ACCION = {
  LOGIN: "inició sesión",
  LOGIN_GOOGLE: "inició sesión con Google",
  CREAR_USUARIO: "creó un usuario",
  ACTUALIZAR_USUARIO: "actualizó un usuario",
  DESACTIVAR_USUARIO: "desactivó un usuario",
  CAMBIAR_ROL_USUARIO: "cambió el rol de un usuario",
  EDITAR_PERFIL: "editó su perfil",
  CAMBIAR_PASSWORD_PERFIL: "cambió su contraseña",
  CREAR_ENLACE_PACIENTES: "creó un enlace de pacientes",
  ELIMINAR_ENLACE_PACIENTES: "eliminó un enlace de pacientes",
  CREAR_EVALUACION: "creó una evaluación",
  INICIAR_EVALUACION: "inició una evaluación",
  FINALIZAR_EVALUACION: "finalizó una evaluación",
  INFORME_INDIVIDUAL_GENERADO: "consultó un resultado individual",
  INFORME_AGRUPADO_GENERADO: "descargó un informe agregado",
};

const FILTROS = ["Todo", "Resultados", "Usuarios", "Enlaces"];
const POR_PAGINA = 10; // registros que se muestran a la vez en cada tabla

const rol = (codigo) => ROLES[codigo] ?? { label: codigo, clase: "trabajador" };
const estado = (codigo) => ESTADOS[codigo] ?? { label: codigo, clase: "neutro" };

// Un usuario activo que aún no verificó su correo se muestra como "Pendiente código"
const estadoUsuario = (u) =>
  u.estado === "ACTIVO" && !u.emailVerificado ? "PENDIENTE_CODIGO" : u.estado;

function accionUsuario(u) {
  if (u.estado === "INACTIVO") return "Reactivar";
  if (!u.emailVerificado) return "Reenviar credenciales";
  return "Editar";
}

const formatoFecha = (iso) =>
  iso
    ? new Date(iso).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })
    : "Nunca";

const formatoPesos = (valor) =>
  Number(valor || 0).toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  });

const porcentaje = (parte, total) => (total ? Math.round((parte / total) * 100) : 0);

export default function Panel() {
  const navigate = useNavigate();
  const { token, cerrarSesion } = useAuth();
  const [busqueda, setBusqueda] = useState("");
  const [filtroAuditoria, setFiltroAuditoria] = useState("Todo");
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    let activo = true;
    setCargando(true);
    fetchPanel(token)
      .then((res) => activo && setDatos(res))
      .catch((err) => activo && setError(err.message))
      .finally(() => activo && setCargando(false));
    return () => {
      activo = false;
    };
  }, [token]);

  function handleLogout() {
    cerrarSesion();
    navigate("/");
  }

  const usuarios = datos?.usuarios ?? [];
  const empresas = datos?.empresas ?? [];
  const compras = datos?.compras ?? [];
  const auditoria = datos?.auditoria ?? [];
  const saldo = datos?.saldo ?? { compradas: 0, usadas: 0 };

  // Búsqueda simple por nombre, correo, empresa o NIT
  const texto = busqueda.trim().toLowerCase();
  const coincide = (...campos) =>
    !texto || campos.some((c) => String(c ?? "").toLowerCase().includes(texto));

  const usuariosFiltrados = usuarios.filter((u) => coincide(u.nombre, u.correo, u.empresa));
  const empresasFiltradas = empresas.filter((e) => coincide(e.nombre, e.nit, e.responsable));

  const auditoriaFiltrada =
    filtroAuditoria === "Todo"
      ? auditoria
      : auditoria.filter((a) => a.tipo === filtroAuditoria);

  // Paginación (10 por página). Vuelve a la página 1 al buscar o cambiar de filtro.
  const pagUsuarios = usePaginacion(usuariosFiltrados, POR_PAGINA, [texto]);
  const pagEmpresas = usePaginacion(empresasFiltradas, POR_PAGINA, [texto]);
  const pagAuditoria = usePaginacion(auditoriaFiltrada, POR_PAGINA, [filtroAuditoria]);

  const disponibles = saldo.compradas - saldo.usadas;
  const porcentajeUsado = porcentaje(saldo.usadas, saldo.compradas);

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div
          className="sidebar__logo"
          onClick={() => navigate("/Inicio")}
          style={{ cursor: "pointer" }}
          role="button"
          aria-label="Ir al inicio"
        >
          <img src="/logob1.png" alt="Magnus" style={{ height: 70, marginRight: "auto" }} />
        </div>

        <nav className="sidebar__menu">
          <button className="menu-item" type="button" onClick={handleLogout}>
            <span>✕</span>
            Cerrar sesión
          </button>
        </nav>
      </aside>

      {/* =====================================================
          CONTENIDO
      ====================================================== */}
      <main className="adm adm-main">
        <BotonRegresar tono="oscuro" />
        <header className="adm-header">
          <div>
            <h1>Panel de administración</h1>
            <p>Usuarios, empresas, compras y auditoría en un solo lugar.</p>
          </div>

          <div className="adm-header__acciones">
            <label htmlFor="adm-buscar" className="adm-sr-only">Buscar</label>
            <input
              id="adm-buscar"
              type="search"
              className="adm-input"
              placeholder="Buscar usuario, empresa o NIT"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
            />
            <ProfileMenu />
          </div>
        </header>

        {cargando && <p className="adm-vacio">Cargando panel…</p>}
        {error && <p className="adm-vacio">{error}</p>}

        {!cargando && !error && (
          <>
            {/* ---------- USUARIOS Y ROLES ---------- */}
            <section id="usuarios" className="adm-card">
              <div className="adm-card__head">
                <div>
                  <h2>Usuarios y roles</h2>
                  <span>Registrados con correo o Google. El Responsable SST se crea al registrar una empresa.</span>
                </div>
                <button type="button" className="adm-btn adm-btn--oscuro">+ Invitar usuario</button>
              </div>

              <div className="adm-tabla-wrap">
                <table className="adm-tabla adm-tabla--ancha">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Rol</th>
                      <th>Empresa</th>
                      <th>Registro</th>
                      <th>Estado</th>
                      <th>Último acceso</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pagUsuarios.items.map((u) => {
                      const r = rol(u.rol);
                      const est = estado(estadoUsuario(u));
                      return (
                        <tr key={u.id}>
                          <td>
                            <div className="adm-celda-doble">
                              <strong>{u.nombre}</strong>
                              <span>{u.correo}</span>
                            </div>
                          </td>
                          <td><span className={`adm-chip adm-chip--rol-${r.clase}`}>{r.label}</span></td>
                          <td>{u.empresa}</td>
                          <td>{u.registro}</td>
                          <td><span className={`adm-chip adm-chip--${est.clase}`}>{est.label}</span></td>
                          <td className="adm-muted">{formatoFecha(u.ultimoAcceso)}</td>
                          <td><button type="button" className="adm-link">{accionUsuario(u)}</button></td>
                        </tr>
                      );
                    })}
                    {usuariosFiltrados.length === 0 && (
                      <tr><td colSpan={7} className="adm-vacio">No hay usuarios que coincidan con la búsqueda.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>

              <Paginador paginacion={pagUsuarios} />
            </section>

            {/* ---------- EMPRESAS ---------- */}
            <div className="adm-dos-columnas">
              <section id="empresas" className="adm-card">
                <div className="adm-card__head">
                  <div>
                    <h2>Empresas</h2>
                    <span>Con su Responsable SST y evaluaciones usadas.</span>
                  </div>
                  <button type="button" className="adm-btn adm-btn--borde" onClick={() => navigate("/verificar-nit")}>
                    + Crear empresa
                  </button>
                </div>

                <div className="adm-tabla-wrap">
                  <table className="adm-tabla">
                    <thead>
                      <tr>
                        <th>Empresa</th>
                        <th>Responsable SST</th>
                        <th>Encuestas</th>
                        <th>Evaluaciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pagEmpresas.items.map((e) => (
                        <tr key={e.id}>
                          <td>
                            <div className="adm-celda-doble">
                              <strong>{e.nombre}</strong>
                              <span>NIT {e.nit}</span>
                            </div>
                          </td>
                          <td>{e.responsable}</td>
                          <td>{e.encuestas}</td>
                          <td className="adm-celda-barra">
                            <span className="adm-muted adm-pequeno">{e.usadas} de {e.compradas} usadas</span>
                            <div className="adm-barra">
                              <div
                                className="adm-barra__relleno"
                                style={{ width: `${Math.min(porcentaje(e.usadas, e.compradas), 100)}%` }}
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                      {empresasFiltradas.length === 0 && (
                        <tr><td colSpan={4} className="adm-vacio">No hay empresas que coincidan.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                <Paginador paginacion={pagEmpresas} />
              </section>
            </div>

            {/* ---------- COMPRAS ---------- */}
            <section id="compras" className="adm-card">
              <div className="adm-card__head">
                <div>
                  <h2>Compras realizadas por las empresas</h2>
                  <span>Evaluaciones compradas con Visa, Mastercard o PSE.</span>
                </div>
              </div>

              <div className="adm-compras">
                <div className="adm-saldo">
                  <span className="adm-saldo__titulo">Saldo de evaluaciones</span>
                  <div className="adm-saldo__numero">
                    <strong>{disponibles}</strong>
                    <span>disponibles</span>
                  </div>
                  <div className="adm-saldo__barra">
                    <div className="adm-saldo__relleno" style={{ width: `${Math.min(porcentajeUsado, 100)}%` }} />
                  </div>
                  <div className="adm-saldo__pie">
                    <span>{saldo.usadas} usadas</span>
                    <span>{saldo.compradas} compradas</span>
                  </div>
                </div>

                <div className="adm-tabla-wrap">
                  <table className="adm-tabla">
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th>Empresa</th>
                        <th>Cantidad</th>
                        <th>Medio de pago</th>
                        <th>Valor</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {compras.map((c) => {
                        const est = estado(c.estado);
                        return (
                          <tr key={c.id}>
                            <td className="adm-muted">{formatoFecha(c.fecha)}</td>
                            <td><strong className="adm-fuerte">{c.empresa}</strong></td>
                            <td>{c.cantidad} evaluaciones</td>
                            <td>{c.medio}</td>
                            <td>{formatoPesos(c.valor)}</td>
                            <td><span className={`adm-chip adm-chip--${est.clase}`}>{est.label}</span></td>
                          </tr>
                        );
                      })}
                      {compras.length === 0 && (
                        <tr><td colSpan={6} className="adm-vacio">Aún no hay compras registradas.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* ---------- AUDITORÍA ---------- */}
            <section id="auditoria" className="adm-card">
              <div className="adm-card__head">
                <div>
                  <h2>Auditoría y privacidad</h2>
                  <span>Registro de accesos, consentimientos y cambios. Ley 1581 de 2012.</span>
                </div>
                <div className="adm-filtros">
                  {FILTROS.map((f) => (
                    <button
                      key={f}
                      type="button"
                      className={`adm-filtro ${filtroAuditoria === f ? "is-active" : ""}`}
                      aria-pressed={filtroAuditoria === f}
                      onClick={() => setFiltroAuditoria(f)}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>

              <ul className="adm-timeline">
                {pagAuditoria.items.map((a) => {
                  const { icono: Icono, clase } = TIPO_AUDITORIA[a.tipo] ?? TIPO_AUDITORIA.Usuarios;
                  return (
                    <li className="adm-timeline__item" key={a.id}>
                      <div className={`adm-timeline__icono adm-chip--${clase}`}>
                        <Icono size={18} />
                      </div>
                      <div className="adm-timeline__texto">
                        <span><strong>{a.usuario}</strong> {TEXTO_ACCION[a.accion] ?? a.accion}</span>
                        {a.detalle && <span className="adm-muted adm-pequeno">{a.detalle}</span>}
                      </div>
                      <span className={`adm-chip adm-chip--${clase}`}>{a.tipo}</span>
                      <span className="adm-timeline__fecha">{formatoFecha(a.fecha)}</span>
                    </li>
                  );
                })}
                {auditoriaFiltrada.length === 0 && (
                  <li className="adm-vacio">No hay eventos para este filtro.</li>
                )}
              </ul>

              <Paginador paginacion={pagAuditoria} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}