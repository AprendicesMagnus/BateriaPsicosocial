import { useEffect, useState } from "react";
import { etiquetaRol } from "../utils/roles";
import { useAuth } from "../context/AuthContext";
import AppTopbar from "../components/AppTopbar";
import "../styles/app-shell.css";
import "../styles/Perfil.css";
import { request, urlArchivo } from "../api/client";
import { editarPerfil, cambiarPassword, fetchDirectorio } from "../api/perfil";
import {
  TEXTO_AYUDA_PASSWORD,
  filtrarNombrePersona,
  nombrePersonaValido,
  passwordValida,
} from "../utils/validaciones";

const TIPOS_FOTO = ["image/jpeg", "image/png", "image/webp"];
const MAX_FOTO_BYTES = 2 * 1024 * 1024; // 2 MB (el backend valida lo mismo)
const POR_PAGINA_DIRECTORIO = 10;

function formatearFecha(fechaIso) {
  if (!fechaIso) return "—";
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(fechaIso));
}

function ReceiptIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path
        d="M6 3h12v18l-2.5-1.5L13 21l-2.5-1.5L8 21l-2-1.5V3Z"
        strokeLinejoin="round"
      />
      <path d="M9 8h6M9 12h6M9 16h3" strokeLinecap="round" />
    </svg>
  );
}

export default function Perfil() {
  const { usuario, token, actualizarUsuario } = useAuth();
  const [compras, setCompras] = useState([]);
  const [loadingCompras, setLoadingCompras] = useState(false);
  const [errorCompras, setErrorCompras] = useState(null);

  // ---- edición de perfil / contraseña ----
  const [modo, setModo] = useState(null); // null | "perfil" | "password"
  const [guardando, setGuardando] = useState(false);
  const [errorForm, setErrorForm] = useState("");
  const [mensajeOk, setMensajeOk] = useState("");

  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");
  const [foto, setFoto] = useState(null);
  const [fotoPreview, setFotoPreview] = useState(null);

  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordConfirmar, setPasswordConfirmar] = useState("");

  // ---- directorio (solo Super Administrador) ----
  const esSuperAdmin = usuario?.rol === "SUPER_ADMINISTRADOR";
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(0);
  const [directorio, setDirectorio] = useState({ total: 0, items: [] });
  const [loadingDirectorio, setLoadingDirectorio] = useState(false);
  const [errorDirectorio, setErrorDirectorio] = useState("");

  useEffect(() => {
    if (usuario?.id && token) {
      setLoadingCompras(true);
      request(`/usuarios/${usuario.id}/compras`, { token })
        .then((data) => setCompras(data))
        .catch((err) => setErrorCompras(err.message))
        .finally(() => setLoadingCompras(false));
    }
  }, [usuario?.id, token]);

  useEffect(() => {
    if (!esSuperAdmin || !token) return undefined;
    const espera = setTimeout(() => {
      setLoadingDirectorio(true);
      setErrorDirectorio("");
      fetchDirectorio(token, {
        q: busqueda.trim(),
        limite: POR_PAGINA_DIRECTORIO,
        desplazamiento: pagina * POR_PAGINA_DIRECTORIO,
      })
        .then(setDirectorio)
        .catch((err) => setErrorDirectorio(err.message || "No se pudo cargar el listado."))
        .finally(() => setLoadingDirectorio(false));
    }, 300);
    return () => clearTimeout(espera);
  }, [esSuperAdmin, token, busqueda, pagina]);

  // Libera la URL temporal de la vista previa de la foto.
  useEffect(() => {
    return () => {
      if (fotoPreview) URL.revokeObjectURL(fotoPreview);
    };
  }, [fotoPreview]);

  const nombreUsuario = usuario
    ? `${usuario.nombre ?? ""} ${usuario.apellido ?? ""}`.trim()
    : "Usuario";
  const rolUsuario = etiquetaRol(usuario?.rol) || "Sin rol asignado";
  const correoUsuario = usuario?.email ?? usuario?.correo ?? "—";
  const empresaUsuario = usuario?.empresa ?? "—";
  const iniciales =
    nombreUsuario
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  // Regla de 15 días: el backend calcula la fecha; el Super Administrador nunca queda bloqueado.
  const proximaEdicion = usuario?.proximaEdicionPerfil ?? null;
  const edicionBloqueada = Boolean(proximaEdicion) && !esSuperAdmin;

  function abrirEdicionPerfil() {
    setMensajeOk("");
    setErrorForm("");
    setNombre(usuario?.nombre ?? "");
    setApellido(usuario?.apellido ?? "");
    setFoto(null);
    setFotoPreview(null);
    setModo("perfil");
  }

  function abrirCambioPassword() {
    setMensajeOk("");
    setErrorForm("");
    setPasswordActual("");
    setPasswordNueva("");
    setPasswordConfirmar("");
    setModo("password");
  }

  function cancelar() {
    setModo(null);
    setErrorForm("");
    setFoto(null);
    setFotoPreview(null);
  }

  function handleFoto(e) {
    const archivo = e.target.files?.[0];
    setErrorForm("");
    if (!archivo) return;
    if (!TIPOS_FOTO.includes(archivo.type)) {
      setErrorForm("La foto debe ser JPG, PNG o WEBP.");
      e.target.value = "";
      return;
    }
    if (archivo.size > MAX_FOTO_BYTES) {
      setErrorForm("La foto no puede superar los 2 MB.");
      e.target.value = "";
      return;
    }
    setFoto(archivo);
    setFotoPreview(URL.createObjectURL(archivo));
  }

  async function guardarPerfil(e) {
    e.preventDefault();
    setErrorForm("");

    const nombreLimpio = nombre.trim();
    const apellidoLimpio = apellido.trim();
    if (!nombrePersonaValido(nombreLimpio, 100)) {
      setErrorForm("El nombre solo puede tener letras y espacios (mínimo 2 caracteres).");
      return;
    }
    if (!nombrePersonaValido(apellidoLimpio, 100)) {
      setErrorForm("El apellido solo puede tener letras y espacios (mínimo 2 caracteres).");
      return;
    }

    const cambios = {};
    if (nombreLimpio !== usuario.nombre) cambios.nombre = nombreLimpio;
    if (apellidoLimpio !== usuario.apellido) cambios.apellido = apellidoLimpio;
    if (foto) cambios.foto = foto;
    if (Object.keys(cambios).length === 0) {
      setErrorForm("No hiciste ningún cambio.");
      return;
    }

    setGuardando(true);
    try {
      const res = await editarPerfil(token, cambios);
      actualizarUsuario(res.usuario);
      setModo(null);
      setFoto(null);
      setFotoPreview(null);
      setMensajeOk("Tu perfil se actualizó correctamente.");
    } catch (err) {
      setErrorForm(err.message || "No se pudo actualizar el perfil.");
    } finally {
      setGuardando(false);
    }
  }

  async function guardarPassword(e) {
    e.preventDefault();
    setErrorForm("");

    if (!passwordActual) {
      setErrorForm("Ingresa tu contraseña actual.");
      return;
    }
    if (!passwordValida(passwordNueva)) {
      setErrorForm(TEXTO_AYUDA_PASSWORD);
      return;
    }
    if (passwordNueva === passwordActual) {
      setErrorForm("La nueva contraseña debe ser distinta de la actual.");
      return;
    }
    if (passwordNueva !== passwordConfirmar) {
      setErrorForm("La confirmación no coincide con la nueva contraseña.");
      return;
    }

    setGuardando(true);
    try {
      const res = await cambiarPassword(token, { passwordActual, passwordNueva });
      actualizarUsuario(res.usuario);
      setModo(null);
      setMensajeOk("Tu contraseña se actualizó correctamente.");
    } catch (err) {
      setErrorForm(err.message || "No se pudo cambiar la contraseña.");
    } finally {
      setGuardando(false);
    }
  }

  const totalPaginas = Math.max(1, Math.ceil(directorio.total / POR_PAGINA_DIRECTORIO));
  const fotoMostrada = fotoPreview || urlArchivo(usuario?.fotoUrl);

  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <nav className="app-breadcrumb">
            Mi cuenta <span>›</span> Perfil
          </nav>
          <h1 className="app-title">Mi Perfil</h1>
          <p className="app-subtitle">Consulta y administra la información de tu cuenta.</p>

          <div className="perfil-layout">
            <div className="app-card perfil-card">
              <div className="perfil-header">
                {fotoMostrada ? (
                  <img
                    src={fotoMostrada}
                    alt={nombreUsuario}
                    className="perfil-avatar perfil-avatar--foto"
                  />
                ) : (
                  <div className="perfil-avatar">{iniciales}</div>
                )}
                <div>
                  <h2 className="perfil-nombre">{nombreUsuario}</h2>
                  <span className="perfil-rol">{rolUsuario}</span>
                </div>
              </div>

              <div className="perfil-divider" />

              {mensajeOk && <div className="perfil-ok">{mensajeOk}</div>}

              {modo === "perfil" && (
                <form className="perfil-form" onSubmit={guardarPerfil} noValidate>
                  <div className="perfil-form-row">
                    <label className="field">
                      <span className="field__label">Nombre</span>
                      <input
                        className="field__input"
                        maxLength={100}
                        value={nombre}
                        onChange={(e) => setNombre(filtrarNombrePersona(e.target.value, 100))}
                      />
                    </label>
                    <label className="field">
                      <span className="field__label">Apellido</span>
                      <input
                        className="field__input"
                        maxLength={100}
                        value={apellido}
                        onChange={(e) => setApellido(filtrarNombrePersona(e.target.value, 100))}
                      />
                    </label>
                  </div>

                  <label className="field">
                    <span className="field__label">Foto de perfil (JPG, PNG o WEBP, máx. 2 MB)</span>
                    <input
                      className="field__input"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleFoto}
                    />
                  </label>

                  {!esSuperAdmin && (
                    <p className="perfil-aviso">
                      Solo puedes editar tu perfil una vez cada 15 días.
                    </p>
                  )}
                  {errorForm && <div className="perfil-error">{errorForm}</div>}

                  <div className="perfil-form-actions">
                    <button type="submit" className="btn-primary perfil-btn" disabled={guardando}>
                      {guardando ? "Guardando..." : "Guardar cambios"}
                    </button>
                    <button type="button" className="app-btn-secondary" onClick={cancelar} disabled={guardando}>
                      Cancelar
                    </button>
                  </div>
                </form>
              )}

              {modo === "password" && (
                <form className="perfil-form" onSubmit={guardarPassword} noValidate>
                  <label className="field">
                    <span className="field__label">Contraseña actual</span>
                    <input
                      className="field__input"
                      type="password"
                      maxLength={72}
                      autoComplete="current-password"
                      value={passwordActual}
                      onChange={(e) => setPasswordActual(e.target.value.slice(0, 72))}
                    />
                  </label>
                  <div className="perfil-form-row">
                    <label className="field">
                      <span className="field__label">Nueva contraseña</span>
                      <input
                        className="field__input"
                        type="password"
                        maxLength={72}
                        autoComplete="new-password"
                        value={passwordNueva}
                        onChange={(e) => setPasswordNueva(e.target.value.slice(0, 72))}
                      />
                    </label>
                    <label className="field">
                      <span className="field__label">Confirmar contraseña</span>
                      <input
                        className="field__input"
                        type="password"
                        maxLength={72}
                        autoComplete="new-password"
                        value={passwordConfirmar}
                        onChange={(e) => setPasswordConfirmar(e.target.value.slice(0, 72))}
                      />
                    </label>
                  </div>

                  <p className="perfil-aviso">{TEXTO_AYUDA_PASSWORD}</p>
                  {errorForm && <div className="perfil-error">{errorForm}</div>}

                  <div className="perfil-form-actions">
                    <button type="submit" className="btn-primary perfil-btn" disabled={guardando}>
                      {guardando ? "Guardando..." : "Cambiar contraseña"}
                    </button>
                    <button type="button" className="app-btn-secondary" onClick={cancelar} disabled={guardando}>
                      Cancelar
                    </button>
                  </div>
                </form>
              )}

              {modo === null && (
                <>
                  <div className="perfil-grid">
                    <div className="perfil-field">
                      <span className="perfil-field-label">Nombre</span>
                      <span className="perfil-field-value">{usuario?.nombre ?? "—"}</span>
                    </div>
                    <div className="perfil-field">
                      <span className="perfil-field-label">Apellido</span>
                      <span className="perfil-field-value">{usuario?.apellido ?? "—"}</span>
                    </div>
                    <div className="perfil-field">
                      <span className="perfil-field-label">Correo electrónico</span>
                      <span className="perfil-field-value">{correoUsuario}</span>
                    </div>
                    <div className="perfil-field">
                      <span className="perfil-field-label">Rol</span>
                      <span className="perfil-field-value">{rolUsuario}</span>
                    </div>
                    <div className="perfil-field">
                      <span className="perfil-field-label">Empresa</span>
                      <span className="perfil-field-value">{empresaUsuario}</span>
                    </div>
                  </div>

                  <div className="perfil-actions">
                    <button
                      type="button"
                      className="app-btn-secondary"
                      onClick={abrirEdicionPerfil}
                      disabled={edicionBloqueada}
                    >
                      Editar perfil
                    </button>
                    <button
                      type="button"
                      className="app-btn-secondary"
                      onClick={abrirCambioPassword}
                      disabled={edicionBloqueada}
                    >
                      Cambiar contraseña
                    </button>
                  </div>

                  {edicionBloqueada && (
                    <p className="perfil-aviso">
                      Solo puedes editar tu perfil una vez cada 15 días. Podrás hacerlo de nuevo el{" "}
                      {formatearFecha(proximaEdicion)}.
                    </p>
                  )}
                </>
              )}
            </div>

            {/* ===================== HISTORIAL DE COMPRAS ===================== */}
            <div className="app-card compras-card">
              <h2 className="compras-titulo">Historial de compras</h2>
              <p className="compras-subtitulo">Baterías de riesgo psicosocial compradas</p>

              {loadingCompras && <p style={{ fontSize: "14px", color: "#64748b" }}>Cargando compras...</p>}
              {errorCompras && <p style={{ fontSize: "14px", color: "#b91c1c" }}>{errorCompras}</p>}

              {!loadingCompras && compras.length > 0 ? (
                <div className="compras-list">
                  {compras.map((compra) => (
                    <div className="compras-row" key={compra.id}>
                      <span className="compras-row-icon">
                        <ReceiptIcon />
                      </span>
                      <div className="compras-row-main">
                        <span className="compras-row-qty">
                          {compra.cantidad} {compra.cantidad === 1 ? "batería" : "baterías"} ({compra.estado})
                        </span>
                        <span className="compras-row-date">{formatearFecha(compra.fecha)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : !loadingCompras && (
                <div className="compras-empty">
                  <p>Aún no has comprado ninguna batería.</p>
                </div>
              )}
            </div>
          </div>

          {/* ============ USUARIOS REGISTRADOS (solo Super Administrador) ============ */}
          {esSuperAdmin && (
            <div className="app-card directorio-card">
              <div className="directorio-encabezado">
                <div>
                  <h2 className="compras-titulo">Usuarios registrados</h2>
                  <p className="compras-subtitulo">{directorio.total} en total</p>
                </div>
                <input
                  className="field__input directorio-busqueda"
                  type="search"
                  placeholder="Buscar por nombre o correo"
                  maxLength={100}
                  value={busqueda}
                  onChange={(e) => {
                    setBusqueda(e.target.value);
                    setPagina(0);
                  }}
                />
              </div>

              {errorDirectorio && <p className="perfil-error">{errorDirectorio}</p>}

              <div className="directorio-tabla-wrap">
                <table className="directorio-tabla">
                  <thead>
                    <tr>
                      <th>Nombre completo</th>
                      <th>Correo electrónico</th>
                      <th>Rol</th>
                    </tr>
                  </thead>
                  <tbody>
                    {directorio.items.map((u) => (
                      <tr key={u.email}>
                        <td>{u.nombreCompleto}</td>
                        <td>{u.email}</td>
                        <td>{etiquetaRol(u.rol)}</td>
                      </tr>
                    ))}
                    {!loadingDirectorio && directorio.items.length === 0 && (
                      <tr>
                        <td colSpan={3} className="directorio-vacio">
                          No se encontraron usuarios.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="directorio-paginacion">
                <button
                  type="button"
                  className="app-btn-secondary"
                  onClick={() => setPagina((p) => Math.max(0, p - 1))}
                  disabled={pagina === 0 || loadingDirectorio}
                >
                  Anterior
                </button>
                <span>
                  Página {pagina + 1} de {totalPaginas}
                </span>
                <button
                  type="button"
                  className="app-btn-secondary"
                  onClick={() => setPagina((p) => p + 1)}
                  disabled={pagina + 1 >= totalPaginas || loadingDirectorio}
                >
                  Siguiente
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
