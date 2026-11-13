import { useEffect, useRef, useState } from "react";
import { useAuth } from "../context/AuthContext";
import {
  descargarDocumentoSoporte,
  editarDocumentoSoporte,
  eliminarDocumentoSoporte,
  fetchDocumentosAdmin,
  subirDocumentoSoporte,
} from "../api/soporte";
import { EXTENSIONES_DOCUMENTO, MAX_DOCUMENTO_MB, etiquetaTipoDocumento, formatearTamano } from "../utils/documentos";
import ModalConfirmacion from "./ModalConfirmacion";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";
import "../styles/PanelDocumentosSoporte.css";

const VACIO = { titulo: "", descripcion: "", activo: true, archivo: null };

function formatearFecha(iso) {
  if (!iso) return "";
  const f = new Date(iso);
  return Number.isNaN(f.getTime()) ? "" : f.toLocaleDateString("es-CO", { dateStyle: "medium" });
}

// Documentos descargables del Centro de ayuda (solo Super Administrador, dentro del Panel).
export default function PanelDocumentosSoporte({ selector = null }) {
  const { token } = useAuth();
  const [docs, setDocs] = useState([]);
  const [form, setForm] = useState(null); // { id?, titulo, descripcion, activo, archivo? }
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState(null);
  const [porEliminar, setPorEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const inputArchivo = useRef(null);

  const cargar = () =>
    fetchDocumentosAdmin(token)
      .then((r) => setDocs(Array.isArray(r) ? r : []))
      .catch((err) => setMensaje({ tipo: "error", texto: err.message || "No se pudieron cargar los documentos." }));

  useEffect(() => {
    if (token) cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  function elegirArchivo(e) {
    const archivo = e.target.files?.[0] || null;
    if (!archivo) return setForm((f) => ({ ...f, archivo: null }));
    const ext = archivo.name.split(".").pop().toLowerCase();
    if (!EXTENSIONES_DOCUMENTO.includes(ext)) {
      e.target.value = "";
      setForm((f) => ({ ...f, archivo: null }));
      return setMensaje({ tipo: "error", texto: "Formato no permitido. Sube un PDF, Word, Excel o PowerPoint." });
    }
    if (archivo.size > MAX_DOCUMENTO_MB * 1024 * 1024) {
      e.target.value = "";
      setForm((f) => ({ ...f, archivo: null }));
      return setMensaje({ tipo: "error", texto: `El archivo supera el máximo de ${MAX_DOCUMENTO_MB} MB.` });
    }
    setMensaje(null);
    // Si aún no hay título, se propone el nombre del archivo sin extensión.
    setForm((f) => ({ ...f, archivo, titulo: f.titulo || archivo.name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ") }));
  }

  async function guardar(e) {
    e.preventDefault();
    if (!form.titulo.trim()) return setMensaje({ tipo: "error", texto: "Escribe el título del documento." });
    if (!form.id && !form.archivo) return setMensaje({ tipo: "error", texto: "Selecciona el archivo que vas a subir." });
    setGuardando(true);
    setMensaje(null);
    try {
      if (form.id) {
        await editarDocumentoSoporte(token, form.id, {
          titulo: form.titulo.trim(),
          descripcion: form.descripcion.trim() || null,
          activo: form.activo,
        });
      } else {
        await subirDocumentoSoporte(token, {
          archivo: form.archivo,
          titulo: form.titulo.trim(),
          descripcion: form.descripcion.trim(),
          activo: form.activo,
        });
      }
      setForm(null);
      await cargar();
      setMensaje({ tipo: "ok", texto: form.id ? "Documento actualizado." : "Documento subido. Ya lo ven los usuarios en el Centro de ayuda." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo guardar el documento." });
    } finally {
      setGuardando(false);
    }
  }

  async function alternar(doc) {
    try {
      await editarDocumentoSoporte(token, doc.id, { activo: !doc.activo });
      await cargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo actualizar." });
    }
  }

  async function descargar(doc) {
    try {
      await descargarDocumentoSoporte(token, doc);
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo descargar." });
    }
  }

  async function confirmarEliminar() {
    if (!porEliminar) return;
    setEliminando(true);
    try {
      await eliminarDocumentoSoporte(token, porEliminar.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Documento eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar." });
    } finally {
      setEliminando(false);
      setPorEliminar(null);
    }
  }

  return (
    <>
      <section id="soporte" className="adm-card">
        <div className="adm-card__head">
          <div>
            <h2>Centro de ayuda</h2>
            <span>Documentos que los usuarios pueden descargar en la página de soporte.</span>
          </div>
          <div className="plan-form__acciones">
            {selector}
            <button type="button" className="adm-btn adm-btn--oscuro" onClick={() => { setMensaje(null); setForm({ ...VACIO }); }}>
              + Subir documento
            </button>
          </div>
        </div>

        <p className="docs-nota">
          El <strong>Manual rápido de enlaces</strong> y el <strong>Marco normativo</strong> vienen incluidos con la plataforma y siempre aparecen
          primero. Aquí administras los documentos adicionales.
        </p>

        {mensaje && <div className={`plan-mensaje plan-mensaje--${mensaje.tipo}`}>{mensaje.texto}</div>}

        {form && (
          <form className="adm-formulario" onSubmit={guardar} noValidate>
            <div className="plan-form__cabecera">
              <h3>{form.id ? "Editar documento" : "Subir documento"}</h3>
              <p>{form.id ? "Puedes cambiar el título, la descripción y la visibilidad. Para cambiar el archivo, súbelo de nuevo y elimina el anterior." : `PDF, Word, Excel o PowerPoint. Máximo ${MAX_DOCUMENTO_MB} MB.`}</p>
            </div>
            <div className="plan-form__campos">
              {!form.id && (
                <div className="plan-campo plan-campo--ancho">
                  Archivo
                  <label className="docs-archivo">
                    <input
                      ref={inputArchivo}
                      type="file"
                      accept={EXTENSIONES_DOCUMENTO.map((e) => `.${e}`).join(",")}
                      onChange={elegirArchivo}
                      aria-label="Archivo del documento"
                    />
                    <span className="docs-archivo__boton">Elegir archivo</span>
                    <span className="docs-archivo__nombre">
                      {form.archivo ? `${form.archivo.name} · ${formatearTamano(form.archivo.size)}` : "Ningún archivo seleccionado"}
                    </span>
                  </label>
                </div>
              )}
              <label className="plan-campo plan-campo--ancho">
                Título
                <input type="text" maxLength={200} value={form.titulo} onChange={cambiar("titulo")} />
              </label>
              <label className="plan-campo plan-campo--ancho">
                Descripción (opcional)
                <textarea rows={3} maxLength={500} value={form.descripcion} onChange={cambiar("descripcion")} />
                <span className="plan-campo__contador">{form.descripcion.length} / 500</span>
              </label>
            </div>
            <div className="plan-form__pie">
              <label className="plan-switch">
                <input type="checkbox" checked={form.activo} onChange={(e) => setForm((f) => ({ ...f, activo: e.target.checked }))} />
                <span className="plan-switch__pista" />
                Visible para los usuarios
              </label>
              <div className="plan-form__botones">
                <button type="button" className="adm-btn adm-btn--borde" onClick={() => setForm(null)} disabled={guardando}>
                  Cancelar
                </button>
                <button type="submit" className="adm-btn adm-btn--dorado" disabled={guardando}>
                  {guardando ? "Guardando..." : form.id ? "Guardar cambios" : "Subir"}
                </button>
              </div>
            </div>
          </form>
        )}

        <div className="adm-tabla-wrap" tabIndex={0} role="region" aria-label="Documentos del Centro de ayuda">
          <table className="adm-tabla">
            <caption className="sr-only">Documentos del Centro de ayuda</caption>
            <thead>
              <tr>
                <th scope="col">Documento</th>
                <th scope="col">Tipo</th>
                <th scope="col">Subido</th>
                <th scope="col">Estado</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id}>
                  <td>
                    <span className="adm-fuerte">{doc.titulo}</span>
                    <small className="docs-archivo-nombre">{doc.nombreArchivo}</small>
                  </td>
                  <td>
                    {etiquetaTipoDocumento(doc.extension)} · {formatearTamano(doc.tamano)}
                  </td>
                  <td>{formatearFecha(doc.creadoEn)}</td>
                  <td>
                    <span className={`adm-chip ${doc.activo ? "adm-chip--info" : "adm-chip--neutro"}`}>{doc.activo ? "Visible" : "Oculto"}</span>
                  </td>
                  <td>
                    <div className="adm-acciones">
                      <button type="button" className="adm-accion" onClick={() => descargar(doc)}>
                        ⭳ Descargar
                      </button>
                      <button
                        type="button"
                        className="adm-accion"
                        onClick={() => { setMensaje(null); setForm({ id: doc.id, titulo: doc.titulo, descripcion: doc.descripcion || "", activo: doc.activo }); }}
                      >
                        ✎ Editar
                      </button>
                      <button type="button" className="adm-accion" onClick={() => alternar(doc)}>
                        {doc.activo ? "Ocultar" : "Mostrar"}
                      </button>
                      <button type="button" className="adm-accion adm-accion--peligro" onClick={() => setPorEliminar(doc)}>
                        ✕ Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {docs.length === 0 && (
                <tr>
                  <td colSpan={5} className="adm-vacio">
                    Aún no has subido documentos adicionales. Usa "+ Subir documento".
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
      <ModalConfirmacion
        abierto={Boolean(porEliminar)}
        titulo="¿Eliminar documento?"
        mensaje={porEliminar ? `Se eliminará "${porEliminar.titulo}" y los usuarios ya no podrán descargarlo. Esta acción no se puede deshacer.` : ""}
        textoConfirmar="Sí, eliminar"
        textoCancelar="Cancelar"
        tipo="peligro"
        cargando={eliminando}
        onConfirmar={confirmarEliminar}
        onCancelar={() => {
          if (!eliminando) setPorEliminar(null);
        }}
      />
    </>
  );
}
