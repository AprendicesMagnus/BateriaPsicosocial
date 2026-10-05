import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  HiOutlineLink,
  HiOutlineUserCircle,
  HiOutlineLockClosed,
  HiOutlineCheckCircle,
  HiOutlineUser,
} from "react-icons/hi";
import { useAuth } from "../context/AuthContext";
import "../styles/dashboard.css";
import "../styles/Panel.css";
import BotonRegresar from "../components/BotonRegresar";

/* =========================================================
   DATOS DE EJEMPLO
   Reemplázalos por las respuestas de tu backend
   (usuarios, empresas, enlaces, compras y auditoría).
========================================================= */

const USUARIOS = [
  { id: 1, nombre: "Laura Méndez", correo: "laura.mendez@correo.co", rol: "Psicólogo", empresa: "—", registro: "Google", estado: "Verificado", acceso: "Hoy, 2:14 p. m.", accion: "Editar" },
  { id: 2, nombre: "Andrés Polanía", correo: "apolania@correo.co", rol: "Administrador", empresa: "Distribuidora Huila", registro: "Correo", estado: "Verificado", acceso: "Ayer", accion: "Editar" },
  { id: 3, nombre: "Carolina Ramos", correo: "sst@ferreteriaopita.co", rol: "Responsable SST", empresa: "Ferretería Opita", registro: "Automático", estado: "Pendiente código", acceso: "Nunca", accion: "Reenviar credenciales" },
  { id: 4, nombre: "Julián Cuéllar", correo: "jcuellar@correo.co", rol: "Jefe", empresa: "Café del Sur", registro: "Correo", estado: "Verificado", acceso: "Hace 3 días", accion: "Editar" },
  { id: 5, nombre: "Marta Perdomo", correo: "mperdomo@correo.co", rol: "Trabajador", empresa: "Café del Sur", registro: "Correo", estado: "Desactivado", acceso: "Hace 2 meses", accion: "Reactivar" },
  { id: 6, nombre: "Diego Ibáñez", correo: "admin@magnus.co", rol: "Super Admin", empresa: "Plataforma", registro: "Correo", estado: "Verificado", acceso: "Ahora", accion: "Ver" },
];

const EMPRESAS = [
  { nit: "900.123.456-7", nombre: "Distribuidora Huila S.A.S.", responsable: "Paola Trujillo", encuestas: 46, usadas: 46, compradas: 60 },
  { nit: "901.555.210-3", nombre: "Ferretería Opita", responsable: "Carolina Ramos", encuestas: 0, usadas: 0, compradas: 20 },
  { nit: "800.987.332-1", nombre: "Café del Sur", responsable: "Hernán Vargas", encuestas: 28, usadas: 28, compradas: 30 },
  { nit: "900.741.852-0", nombre: "Transportes Neiva", responsable: "Sandra Rojas", encuestas: 73, usadas: 73, compradas: 120 },
  { nit: "901.320.774-9", nombre: "Clínica Andes", responsable: "Luis Muñoz", encuestas: 112, usadas: 112, compradas: 150 },
];

const ENLACES = [
  { id: 1, psicologo: "Laura Méndez", empresa: "Clínica Andes", completados: 34, abiertos: 41, vence: "15 oct 2026", estado: "Activo", accion: "Copiar enlace" },
  { id: 2, psicologo: "Laura Méndez", empresa: "Café del Sur", completados: 12, abiertos: 12, vence: "28 sep 2026", estado: "Vencido", accion: "Extender" },
  { id: 3, psicologo: "Felipe Charry", empresa: "Transportes Neiva", completados: 9, abiertos: 22, vence: "Mañana", estado: "Activo", accion: "Copiar enlace" },
  { id: 4, psicologo: "Felipe Charry", empresa: "Distribuidora Huila", completados: 3, abiertos: 5, vence: "—", estado: "Revocado", accion: "Ver motivo" },
  { id: 5, psicologo: "Ana Losada", empresa: "Ferretería Opita", completados: 0, abiertos: 0, vence: "30 oct 2026", estado: "Activo", accion: "Copiar enlace" },
];

const SALDO = { compradas: 500, usadas: 312 };

const COMPRAS = [
  { id: 1, fecha: "01 oct 2026", empresa: "Clínica Andes", cantidad: 50, medio: "PSE", valor: "[VALOR]", estado: "Aprobado" },
  { id: 2, fecha: "27 sep 2026", empresa: "Transportes Neiva", cantidad: 60, medio: "Visa •••• 4821", valor: "[VALOR]", estado: "Aprobado" },
  { id: 3, fecha: "20 sep 2026", empresa: "Ferretería Opita", cantidad: 20, medio: "PSE", valor: "[VALOR]", estado: "Pendiente" },
  { id: 4, fecha: "12 sep 2026", empresa: "Café del Sur", cantidad: 30, medio: "Mastercard •••• 1290", valor: "[VALOR]", estado: "Rechazado" },
  { id: 5, fecha: "03 sep 2026", empresa: "Distribuidora Huila", cantidad: 60, medio: "Visa •••• 7713", valor: "[VALOR]", estado: "Aprobado" },
];

const AUDITORIA = [
  { id: 1, usuario: "Laura Méndez", accion: "consultó un resultado individual", detalle: "Clínica Andes · Intralaboral Forma A · participante #A-0192", tipo: "Resultados", fecha: "Hoy, 2:14 p. m." },
  { id: 2, usuario: "Participante anónimo", accion: "aceptó el consentimiento informado", detalle: "Enlace de Laura Méndez · Clínica Andes", tipo: "Consentimientos", fecha: "Hoy, 1:50 p. m." },
  { id: 3, usuario: "Diego Ibáñez", accion: "desactivó a Marta Perdomo", detalle: "Rol Trabajador · Café del Sur", tipo: "Usuarios", fecha: "Ayer, 5:02 p. m." },
  { id: 4, usuario: "Felipe Charry", accion: "revocó un enlace de pacientes", detalle: "Distribuidora Huila · compartido por error", tipo: "Enlaces", fecha: "Ayer, 11:20 a. m." },
  { id: 5, usuario: "Andrés Polanía", accion: "descargó un informe agregado", detalle: "Distribuidora Huila · 46 participantes", tipo: "Resultados", fecha: "30 sep, 9:15 a. m." },
  { id: 6, usuario: "Sistema", accion: "creó el usuario Responsable SST", detalle: "Ferretería Opita · NIT 901.555.210-3 verificado", tipo: "Usuarios", fecha: "20 sep, 4:41 p. m." },
];

/* =========================================================
   CONFIGURACIÓN DE LA VISTA
========================================================= */

// Rol -> sufijo de clase CSS (adm-chip--rol-...)
const CLASE_ROL = {
  "Super Admin": "superadmin",
  Administrador: "admin",
  Psicólogo: "psicologo",
  Jefe: "jefe",
  "Responsable SST": "sst",
  Trabajador: "trabajador",
};

// Estado -> sufijo de clase CSS (adm-chip--...)
const CLASE_ESTADO = {
  Verificado: "info",
  Activo: "info",
  Aprobado: "info",
  "Pendiente código": "aviso",
  Pendiente: "aviso",
  Desactivado: "neutro",
  Vencido: "neutro",
  Revocado: "peligro",
  Rechazado: "peligro",
};

// Tipo de evento de auditoría -> ícono y color
const TIPO_AUDITORIA = {
  Resultados: { icono: HiOutlineLockClosed, clase: "psicologo" },
  Consentimientos: { icono: HiOutlineCheckCircle, clase: "info" },
  Usuarios: { icono: HiOutlineUser, clase: "neutro" },
  Enlaces: { icono: HiOutlineLink, clase: "peligro" },
};

const FILTROS = ["Todo", "Resultados", "Consentimientos", "Usuarios", "Enlaces"];

export default function Panel() {
  const navigate = useNavigate();
  const { cerrarSesion } = useAuth();
  const [busqueda, setBusqueda] = useState("");
  const [filtroAuditoria, setFiltroAuditoria] = useState("Todo");

  function handleLogout() {
    cerrarSesion();
    navigate("/");
  }

  // Búsqueda simple por nombre, correo, empresa o NIT
  const texto = busqueda.trim().toLowerCase();
  const coincide = (...campos) =>
    !texto || campos.some((c) => String(c).toLowerCase().includes(texto));

  const usuariosFiltrados = USUARIOS.filter((u) => coincide(u.nombre, u.correo, u.empresa));
  const empresasFiltradas = EMPRESAS.filter((e) => coincide(e.nombre, e.nit, e.responsable));

  const auditoriaFiltrada =
    filtroAuditoria === "Todo"
      ? AUDITORIA
      : AUDITORIA.filter((a) => a.tipo === filtroAuditoria);

  const disponibles = SALDO.compradas - SALDO.usadas;
  const porcentajeUsado = Math.round((SALDO.usadas / SALDO.compradas) * 100);





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
            <p>Usuarios, empresas, enlaces de pacientes, compras y auditoría en un solo lugar.</p>
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
            <button
              type="button"
              className="adm-avatar"
              aria-label="Perfil del administrador"
              onClick={() => navigate("/perfil")}
            >
              <HiOutlineUserCircle size={26} />
            </button>
          </div>
        </header>

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
                {usuariosFiltrados.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <div className="adm-celda-doble">
                        <strong>{u.nombre}</strong>
                        <span>{u.correo}</span>
                      </div>
                    </td>
                    <td><span className={`adm-chip adm-chip--rol-${CLASE_ROL[u.rol]}`}>{u.rol}</span></td>
                    <td>{u.empresa}</td>
                    <td>{u.registro}</td>
                    <td><span className={`adm-chip adm-chip--${CLASE_ESTADO[u.estado]}`}>{u.estado}</span></td>
                    <td className="adm-muted">{u.acceso}</td>
                    <td><button type="button" className="adm-link">{u.accion}</button></td>
                  </tr>
                ))}
                {usuariosFiltrados.length === 0 && (
                  <tr><td colSpan={7} className="adm-vacio">No hay usuarios que coincidan con la búsqueda.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* ---------- EMPRESAS + ENLACES ---------- */}
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
                  {empresasFiltradas.map((e) => (
                    <tr key={e.nit}>
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
                            style={{ width: `${Math.round((e.usadas / e.compradas) * 100)}%` }}
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
                <div className="adm-saldo__relleno" style={{ width: `${porcentajeUsado}%` }} />
              </div>
              <div className="adm-saldo__pie">
                <span>{SALDO.usadas} usadas</span>
                <span>{SALDO.compradas} compradas</span>
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
                  {COMPRAS.map((c) => (
                    <tr key={c.id}>
                      <td className="adm-muted">{c.fecha}</td>
                      <td><strong className="adm-fuerte">{c.empresa}</strong></td>
                      <td>{c.cantidad} evaluaciones</td>
                      <td>{c.medio}</td>
                      <td>{c.valor}</td>
                      <td><span className={`adm-chip adm-chip--${CLASE_ESTADO[c.estado]}`}>{c.estado}</span></td>
                    </tr>
                  ))}
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
            {auditoriaFiltrada.map((a) => {
              const { icono: Icono, clase } = TIPO_AUDITORIA[a.tipo];
              return (
                <li className="adm-timeline__item" key={a.id}>
                  <div className={`adm-timeline__icono adm-chip--${clase}`}>
                    <Icono size={18} />
                  </div>
                  <div className="adm-timeline__texto">
                    <span><strong>{a.usuario}</strong> {a.accion}</span>
                    <span className="adm-muted adm-pequeno">{a.detalle}</span>
                  </div>
                  <span className={`adm-chip adm-chip--${clase}`}>{a.tipo}</span>
                  <span className="adm-timeline__fecha">{a.fecha}</span>
                </li>
              );
            })}
          </ul>
        </section>
      </main>
    </div>
  );
}