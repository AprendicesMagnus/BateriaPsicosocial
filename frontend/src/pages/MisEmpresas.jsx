import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import { useAuth } from "../context/AuthContext";
import { fetchMe } from "../api/auth";
import { fetchMisEmpresas, editarMiEmpresa, eliminarMiEmpresa } from "../api/perfil";
import {
  MAX_EMAIL_LENGTH,
  MAX_LUGAR_LENGTH,
  emailValido,
  filtrarLugar,
  lugarValido,
  normalizarEmail,
} from "../utils/validaciones";
import "../styles/app-shell.css";
import "../styles/MisEmpresas.css";

const SECTORES = ["Comercial", "Servicios", "Otros"];

function formatearFecha(fechaIso) {
  if (!fechaIso) return "—";
  return new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "long", year: "numeric" }).format(
    new Date(fechaIso)
  );
}

// Empresas antiguas pueden traer un sector que ya no existe ("Otro", "Energético"...).
function sectorParaFormulario(sector) {
  if (SECTORES.includes(sector)) return sector;
  return sector === "Otro" ? "Otros" : "";
}

export default function MisEmpresas() {
  const { token, actualizarUsuario } = useAuth();
  const location = useLocation();

  const [empresas, setEmpresas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [aviso, setAviso] = useState(location.state?.mensaje ?? "");

  // ---- edición ----
  const [editando, setEditando] = useState(null); // empresa en edición
  const [form, setForm] = useState({ sector: "", municipio: "", email: "" });
  const [intento, setIntento] = useState(false);
  const [errorForm, setErrorForm] = useState("");
  const [guardando, setGuardando] = useState(false);

  // ---- eliminación ----
  const [eliminando, setEliminando] = useState(null); // empresa a eliminar
  const [errorEliminar, setErrorEliminar] = useState("");
  const [borrando, setBorrando] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetchMisEmpresas(token)
      .then(setEmpresas)
      .catch((err) => setError(err.message || "No se pudieron cargar tus empresas."))
      .finally(() => setCargando(false));
  }, [token]);

  // ---------- editar ----------
  function abrirEdicion(empresa) {
    setErrorForm("");
    setIntento(false);
    setForm({
      sector: sectorParaFormulario(empresa.sector),
      municipio: empresa.municipio ?? "",
      email: empresa.email ?? "",
    });
    setEditando(empresa);
  }

  const erroresForm = {
    sector: !form.sector ? "Selecciona una opción." : "",
    municipio: !form.municipio.trim()
      ? "Este campo es obligatorio."
      : !lugarValido(form.municipio.trim())
      ? "Solo letras, espacios, punto y guion (entre 2 y 80 caracteres)."
      : "",
    email: !form.email.trim()
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(form.email))
      ? "Ingresa un correo válido."
      : "",
  };

  async function guardarEdicion(e) {
    e.preventDefault();
    setErrorForm("");
    setIntento(true);
    if (Object.values(erroresForm).some(Boolean)) return;

    setGuardando(true);
    try {
      const actualizada = await editarMiEmpresa(token, editando.id, {
        sector: form.sector,
        municipio: form.municipio.trim(),
        email: normalizarEmail(form.email),
      });
      setEmpresas((lista) => lista.map((emp) => (emp.id === actualizada.id ? actualizada : emp)));
      setEditando(null);
      setAviso("Empresa actualizada correctamente.");
    } catch (err) {
      setErrorForm(err.message || "No se pudo actualizar la empresa.");
    } finally {
      setGuardando(false);
    }
  }

  // ---------- eliminar ----------
  async function confirmarEliminacion() {
    setErrorEliminar("");
    setBorrando(true);
    try {
      await eliminarMiEmpresa(token, eliminando.id);
      setEmpresas((lista) => lista.filter((emp) => emp.id !== eliminando.id));
      setEliminando(null);
      setAviso("Empresa eliminada correctamente.");
      // Si el usuario estaba vinculado a esa empresa, el backend lo desvincula: se refresca.
      fetchMe(token)
        .then((data) => actualizarUsuario(data.usuario))
        .catch(() => {});
    } catch (err) {
      setErrorEliminar(err.message || "No se pudo eliminar la empresa.");
    } finally {
      setBorrando(false);
    }
  }

  const campoClase = (campo) =>
    `field__input ${intento && erroresForm[campo] ? "field__input--invalid" : ""}`.trim();

  return (
    <div className="app-shell-page">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content">
          <nav className="app-breadcrumb">
            Empresas <span>›</span> Mis empresas
          </nav>
          <h1 className="app-title">Mis Empresas</h1>
          <p className="app-subtitle">Empresas que has registrado con tu cuenta.</p>

          {aviso && <div className="mis-empresas-ok">{aviso}</div>}
          {error && <div className="mis-empresas-error">{error}</div>}

          <div className="app-card mis-empresas-card">
            {cargando ? (
              <p className="mis-empresas-vacio">Cargando empresas...</p>
            ) : empresas.length === 0 ? (
              <div className="mis-empresas-vacio">
                <p>Todavía no has creado ninguna empresa.</p>
                <Link to="/verificar-nit" className="btn-primary mis-empresas-btn">
                  Crear empresa
                </Link>
              </div>
            ) : (
              <div className="mis-empresas-tabla-wrap">
                <table className="mis-empresas-tabla">
                  <thead>
                    <tr>
                      <th>Razón social</th>
                      <th>NIT</th>
                      <th>Sector</th>
                      <th>Ciudad</th>
                      <th>Creada</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {empresas.map((empresa) => (
                      <tr key={empresa.id}>
                        <td>{empresa.nombre}</td>
                        <td>{empresa.nit}</td>
                        <td>{empresa.sector ?? "—"}</td>
                        <td>{empresa.municipio ?? "—"}</td>
                        <td>{formatearFecha(empresa.creadoEn)}</td>
                        <td>
                          <div className="mis-empresas-acciones">
                            <button
                              type="button"
                              className="mis-empresas-accion"
                              onClick={() => abrirEdicion(empresa)}
                              aria-label={`Editar ${empresa.nombre}`}
                            >
                              Editar
                            </button>
                            <button
                              type="button"
                              className="mis-empresas-accion mis-empresas-accion--peligro"
                              onClick={() => {
                                setErrorEliminar("");
                                setEliminando(empresa);
                              }}
                              aria-label={`Eliminar ${empresa.nombre}`}
                            >
                              Eliminar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ===================== MODAL EDITAR ===================== */}
      {editando && (
        <div className="mis-empresas-fondo" role="dialog" aria-modal="true" aria-labelledby="editar-titulo">
          <form className="mis-empresas-modal" onSubmit={guardarEdicion} noValidate>
            <h2 id="editar-titulo">Editar empresa</h2>

            <label className="field">
              <span className="field__label">NIT (no se puede modificar)</span>
              <input className="field__input" value={editando.nit} disabled />
            </label>

            <label className="field">
              <span className="field__label">Razón social (no se puede modificar)</span>
              <input className="field__input" value={editando.nombre} disabled />
            </label>

            <label className="field">
              <span className="field__label">Sector económico</span>
              <select
                className={campoClase("sector")}
                value={form.sector}
                onChange={(e) => setForm((f) => ({ ...f, sector: e.target.value }))}
              >
                <option value="" disabled>
                  Selecciona un sector
                </option>
                {SECTORES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              {intento && erroresForm.sector && <span className="field__error">{erroresForm.sector}</span>}
            </label>

            <label className="field">
              <span className="field__label">Ciudad / Municipio</span>
              <input
                className={campoClase("municipio")}
                maxLength={MAX_LUGAR_LENGTH}
                value={form.municipio}
                onChange={(e) =>
                  setForm((f) => ({ ...f, municipio: filtrarLugar(e.target.value, MAX_LUGAR_LENGTH) }))
                }
              />
              {intento && erroresForm.municipio && <span className="field__error">{erroresForm.municipio}</span>}
            </label>

            <label className="field">
              <span className="field__label">Correo institucional de la empresa</span>
              <input
                className={campoClase("email")}
                type="email"
                maxLength={MAX_EMAIL_LENGTH}
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              />
              {intento && erroresForm.email && <span className="field__error">{erroresForm.email}</span>}
            </label>

            {errorForm && <div className="mis-empresas-error">{errorForm}</div>}

            <div className="mis-empresas-modal-acciones">
              <button type="submit" className="btn-primary mis-empresas-btn-modal" disabled={guardando}>
                {guardando ? "Guardando..." : "Guardar cambios"}
              </button>
              <button
                type="button"
                className="app-btn-secondary"
                onClick={() => setEditando(null)}
                disabled={guardando}
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ===================== MODAL ELIMINAR ===================== */}
      {eliminando && (
        <div className="mis-empresas-fondo" role="alertdialog" aria-modal="true" aria-labelledby="eliminar-titulo">
          <div className="mis-empresas-modal">
            <h2 id="eliminar-titulo">Eliminar empresa</h2>
            <p className="mis-empresas-texto">
              ¿Seguro que quieres eliminar <strong>{eliminando.nombre}</strong> (NIT {eliminando.nit})? Esta acción
              no se puede deshacer y también se eliminarán los usuarios responsables creados para esta empresa.
            </p>
            <p className="mis-empresas-texto">
              Solo se pueden eliminar empresas que todavía no tienen evaluaciones ni compras.
            </p>

            {errorEliminar && <div className="mis-empresas-error">{errorEliminar}</div>}

            <div className="mis-empresas-modal-acciones">
              <button
                type="button"
                className="mis-empresas-btn-peligro"
                onClick={confirmarEliminacion}
                disabled={borrando}
              >
                {borrando ? "Eliminando..." : "Sí, eliminar"}
              </button>
              <button
                type="button"
                className="app-btn-secondary"
                onClick={() => setEliminando(null)}
                disabled={borrando}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}