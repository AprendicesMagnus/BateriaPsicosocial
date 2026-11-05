import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { crearContenido, editarContenido, eliminarContenido, fetchContenidoAdmin } from "../api/soporte";
import PanelMensajesSoporte from "./PanelMensajesSoporte";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";
import ModalConfirmacion from "./ModalConfirmacion";

const SECCIONES = [
  { clave: "faq", label: "Preguntas frecuentes", conTitulo: true },
  { clave: "guia_SUPER_ADMINISTRADOR", label: "Guía: Super Administrador" },
  { clave: "guia_JEFE", label: "Guía: Jefe" },
  { clave: "guia_ADMINISTRADOR", label: "Guía: Administrador" },
  { clave: "guia_EVALUADOR_SST", label: "Guía: Psicólogo" },
  { clave: "guia_RESPONSABLE_SST", label: "Guía: Responsable SST" },
  { clave: "riesgo", label: "Cómo interpretar los resultados", conTitulo: true },
  { clave: "glosario", label: "Glosario", conTitulo: true },
  { clave: "novedades", label: "Novedades y avisos", conTitulo: true },
  { clave: "atencion", label: "Horarios y canales de atención", conTitulo: true },
  { clave: "mensajes", label: "Mensajes de soporte (usuarios)" },
];

// Administración del contenido del Centro de ayuda (solo Super Administrador, dentro del Panel).
export default function PanelSoporte() {
  const { token } = useAuth();
  const [items, setItems] = useState([]);
  const location = useLocation();
  const [seccion, setSeccion] = useState(location.state?.vista === "mensajes" ? "mensajes" : "faq");
  const [form, setForm] = useState(null); // {id?, titulo, texto, orden, activo}
  const [guardando, setGuardando] = useState(false);
  const [itemPorEliminar, setItemPorEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  const info = SECCIONES.find((s) => s.clave === seccion);
  const cargar = () =>
    fetchContenidoAdmin(token)
      .then(setItems)
      .catch((err) => setMensaje({ tipo: "error", texto: err.message || "No se pudo cargar el contenido." }));

  useEffect(() => {
    if (token) cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const lista = items.filter((i) => i.seccion === seccion);

  async function guardar(e) {
    e.preventDefault();
    if (form.texto.trim().length < 2) return setMensaje({ tipo: "error", texto: "Escribe el texto." });
    if (info.conTitulo && !form.titulo.trim()) return setMensaje({ tipo: "error", texto: "Escribe el título." });
    const cuerpo = {
      titulo: info.conTitulo ? form.titulo.trim() : null,
      texto: form.texto.trim(),
      orden: form.orden === "" ? undefined : Number(form.orden),
      activo: form.activo,
    };
    setGuardando(true);
    setMensaje(null);
    try {
      if (form.id) await editarContenido(token, form.id, cuerpo);
      else await crearContenido(token, { ...cuerpo, seccion });
      setForm(null);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Contenido guardado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo guardar." });
    } finally {
      setGuardando(false);
    }
  }

  async function alternar(item) {
    try {
      await editarContenido(token, item.id, { activo: !item.activo });
      await cargar();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo actualizar." });
    }
  }

  function eliminar(item) {
    setItemPorEliminar(item);
  }

  async function confirmarEliminarItem() {
    if (!itemPorEliminar) return;
    setEliminando(true);
    try {
      await eliminarContenido(token, itemPorEliminar.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Elemento eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar." });
    } finally {
      setEliminando(false);
      setItemPorEliminar(null);
    }
  }

  /*
  async function eliminarItemAntiguo(item) {
    // confirmacion reemplazada por ModalConfirmacion
    try {
      await eliminarContenido(token, item.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Elemento eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar." });
    }
  }

  */
  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  // Mismo selector para el contenido editable y para los mensajes de los usuarios.
  const selectorSeccion = (
    <select className="adm-input" value={seccion} onChange={(e) => { setSeccion(e.target.value); setForm(null); setMensaje(null); }}>
      {SECCIONES.map((s) => (
        <option key={s.clave} value={s.clave}>
          {s.label}
        </option>
      ))}
    </select>
  );

  if (seccion === "mensajes") return <PanelMensajesSoporte selector={selectorSeccion} />;

  return (
    <>
      <section id="soporte" className="adm-card">
      <div className="adm-card__head">
        <div>
          <h2>Centro de ayuda</h2>
          <span>Edita lo que ven los usuarios en la página de soporte.</span>
        </div>
        <div className="plan-form__acciones">
          {selectorSeccion}
          <button type="button" className="adm-btn adm-btn--oscuro" onClick={() => setForm({ titulo: "", texto: "", orden: "", activo: true })}>
            + Agregar
          </button>
        </div>
      </div>

      {mensaje && <div className={`plan-mensaje plan-mensaje--${mensaje.tipo}`}>{mensaje.texto}</div>}

      {form && (
        <form className="adm-formulario" onSubmit={guardar} noValidate>
          <div className="plan-form__cabecera">
            <h3>{form.id ? "Editar" : "Agregar"} · {info.label}</h3>
            <p>Esto es lo que verán los usuarios en la página de soporte.</p>
          </div>
          <div className="plan-form__campos">
            {info.conTitulo && (
              <label className="plan-campo plan-campo--ancho">
                {seccion === "faq" ? "Pregunta" : "Título"}
                <input type="text" maxLength={200} value={form.titulo} onChange={cambiar("titulo")} />
              </label>
            )}
            <label className="plan-campo plan-campo--ancho">
              {seccion === "faq" ? "Respuesta" : info.conTitulo ? "Texto" : "Paso"}
              <textarea rows={4} maxLength={2000} value={form.texto} onChange={cambiar("texto")} />
              <span className="plan-campo__contador">{form.texto.length} / 2000</span>
            </label>
            <label className="plan-campo">
              Orden
              <input type="number" min={0} placeholder="Al final" value={form.orden} onChange={cambiar("orden")} />
              <small>Vacío = se agrega al final.</small>
            </label>
          </div>
          <div className="plan-form__pie">
            <label className="plan-switch">
              <input type="checkbox" checked={form.activo} onChange={(e) => setForm((f) => ({ ...f, activo: e.target.checked }))} />
              <span className="plan-switch__pista" />
              Visible
            </label>
            <div className="plan-form__botones">
              <button type="button" className="adm-btn adm-btn--borde" onClick={() => setForm(null)} disabled={guardando}>
                Cancelar
              </button>
              <button type="submit" className="adm-btn adm-btn--dorado" disabled={guardando}>
                {guardando ? "Guardando..." : form.id ? "Guardar cambios" : "Agregar"}
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="adm-tabla-wrap">
        <table className="adm-tabla">
          <thead>
            <tr>
              <th>Orden</th>
              <th>{info.conTitulo ? "Título" : "Paso"}</th>
              {info.conTitulo && <th>Texto</th>}
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((item) => (
              <tr key={item.id}>
                <td>{item.orden}</td>
                <td className={info.conTitulo ? "adm-fuerte" : ""}>{info.conTitulo ? item.titulo : item.texto}</td>
                {info.conTitulo && <td style={{ maxWidth: 360 }}>{item.texto.length > 110 ? `${item.texto.slice(0, 110)}…` : item.texto}</td>}
                <td>
                  <span className={`adm-chip ${item.activo ? "adm-chip--info" : "adm-chip--neutro"}`}>{item.activo ? "Visible" : "Oculto"}</span>
                </td>
                <td>
                  <div className="adm-acciones">
                    <button type="button" className="adm-accion" onClick={() => setForm({ id: item.id, titulo: item.titulo ?? "", texto: item.texto, orden: String(item.orden), activo: item.activo })}>
                      ✎ Editar
                    </button>
                    <button type="button" className="adm-accion" onClick={() => alternar(item)}>
                      {item.activo ? "Ocultar" : "Mostrar"}
                    </button>
                    <button type="button" className="adm-accion adm-accion--peligro" onClick={() => eliminar(item)}>
                      ✕ Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {lista.length === 0 && (
              <tr>
                <td colSpan={5} className="adm-vacio">
                  Esta sección aún no tiene elementos. Usa "+ Agregar".
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
    <ModalConfirmacion
      abierto={Boolean(itemPorEliminar)}
      titulo="¿Eliminar elemento?"
      mensaje={
        itemPorEliminar?.titulo
          ? `Se eliminará "${itemPorEliminar.titulo}". Esta acción no se puede deshacer.`
          : "Esta acción no se puede deshacer."
      }
      textoConfirmar="Sí, eliminar"
      textoCancelar="Cancelar"
      tipo="peligro"
      cargando={eliminando}
      onConfirmar={confirmarEliminarItem}
      onCancelar={() => {
        if (!eliminando) setItemPorEliminar(null);
      }}
    />
    </>
  );
}