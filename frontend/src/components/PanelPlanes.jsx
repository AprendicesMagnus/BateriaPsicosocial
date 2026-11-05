import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { crearPlan, editarPlan, eliminarPlan, fetchPlanesAdmin } from "../api/planes";
import { etiquetaRango, formatearPrecio } from "../utils/planes";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";
import ModalConfirmacion from "./ModalConfirmacion";

const VACIO = { nombre: "", cantidadMin: "", cantidadMax: "", precioUnitario: "", activo: true };

// Administración de los planes (solo Super Administrador, dentro del Panel).
export default function PanelPlanes() {
  const { token } = useAuth();
  const [planes, setPlanes] = useState([]);
  const [form, setForm] = useState(null); // null = cerrado; {id?, ...campos}
  const [guardando, setGuardando] = useState(false);
  const [planPorEliminar, setPlanPorEliminar] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const [mensaje, setMensaje] = useState(null); // {tipo, texto}

  const cargar = () =>
    fetchPlanesAdmin(token)
      .then(setPlanes)
      .catch((err) => setMensaje({ tipo: "error", texto: err.message || "No se pudieron cargar los planes." }));

  useEffect(() => {
    if (token) cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const abrirNuevo = () => {
    setMensaje(null);
    setForm({ ...VACIO });
  };

  const abrirEdicion = (plan) => {
    setMensaje(null);
    setForm({
      id: plan.id,
      nombre: plan.nombre,
      cantidadMin: String(plan.cantidadMin),
      cantidadMax: plan.cantidadMax == null ? "" : String(plan.cantidadMax),
      precioUnitario: String(plan.precioUnitario),
      activo: plan.activo,
    });
  };

  async function guardar(e) {
    e.preventDefault();
    const min = Number(form.cantidadMin);
    const max = form.cantidadMax === "" ? null : Number(form.cantidadMax);
    const precio = Number(form.precioUnitario);

    if (form.nombre.trim().length < 2) return setMensaje({ tipo: "error", texto: "Escribe el nombre del plan." });
    if (!Number.isInteger(min) || min < 1) return setMensaje({ tipo: "error", texto: "La cantidad mínima debe ser un entero desde 1." });
    if (max !== null && (!Number.isInteger(max) || max < min))
      return setMensaje({ tipo: "error", texto: "La cantidad máxima debe ser un entero igual o mayor que la mínima (o déjala vacía para 'en adelante')." });
    if (!Number.isInteger(precio) || precio < 0) return setMensaje({ tipo: "error", texto: "El precio debe ser un número entero (pesos)." });

    const cuerpo = { nombre: form.nombre.trim(), cantidadMin: min, cantidadMax: max, precioUnitario: precio, activo: form.activo };
    setGuardando(true);
    setMensaje(null);
    try {
      if (form.id) await editarPlan(token, form.id, cuerpo);
      else await crearPlan(token, cuerpo);
      setForm(null);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Plan guardado correctamente." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo guardar el plan." });
    } finally {
      setGuardando(false);
    }
  }

  function eliminar(plan) {
    setPlanPorEliminar(plan);
  }

  async function confirmarEliminarPlan() {
    if (!planPorEliminar) return;
    setEliminando(true);
    try {
      await eliminarPlan(token, planPorEliminar.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Plan eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar el plan." });
    } finally {
      setEliminando(false);
      setPlanPorEliminar(null);
    }
  }

  /*
  async function eliminarPlanAntiguo(plan) {
    // confirmacion reemplazada por ModalConfirmacion
    try {
      await eliminarPlan(token, plan.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Plan eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar el plan." });
    }
  }

  */
  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  return (
    <section id="planes" className="adm-card">
      <div className="adm-card__head">
        <div>
          <h2>Planes de baterías</h2>
          <span>Lo que ven los visitantes en "Planes" de la página principal. Precio en pesos por batería.</span>
        </div>
        <button type="button" className="adm-btn adm-btn--oscuro" onClick={abrirNuevo}>
          + Agregar plan
        </button>
      </div>

      {mensaje && <div className={`plan-mensaje plan-mensaje--${mensaje.tipo}`}>{mensaje.texto}</div>}

      {form && (
        <form className="adm-formulario" onSubmit={guardar} noValidate>
          <div className="plan-form__cabecera">
            <h3>{form.id ? "Editar plan" : "Nuevo plan"}</h3>
            <p>Define el rango de baterías y el precio que verán los visitantes.</p>
          </div>
          <div className="plan-form__campos">
            <label className="plan-campo plan-campo--ancho">
              Nombre del plan
              <input type="text" maxLength={80} placeholder="Ej.: Plan 1 a 10" value={form.nombre} onChange={cambiar("nombre")} />
            </label>
            <label className="plan-campo">
              Cantidad mínima
              <input type="number" min={1} value={form.cantidadMin} onChange={cambiar("cantidadMin")} />
              <small>Desde cuántas baterías aplica.</small>
            </label>
            <label className="plan-campo">
              Cantidad máxima
              <input type="number" min={1} placeholder="En adelante" value={form.cantidadMax} onChange={cambiar("cantidadMax")} />
              <small>Déjala vacía para "en adelante".</small>
            </label>
            <label className="plan-campo">
              Precio por batería (COP)
              <span className="plan-campo__dinero">
                <span>$</span>
                <input type="number" min={0} value={form.precioUnitario} onChange={cambiar("precioUnitario")} />
              </span>
              <small>En pesos, sin puntos ni comas.</small>
            </label>
          </div>
          <div className="plan-form__pie">
            <label className="plan-switch">
              <input type="checkbox" checked={form.activo} onChange={(e) => setForm((f) => ({ ...f, activo: e.target.checked }))} />
              <span className="plan-switch__pista" />
              Visible en la página
            </label>
            <div className="plan-form__botones">
              <button type="button" className="adm-btn adm-btn--borde" onClick={() => setForm(null)} disabled={guardando}>
                Cancelar
              </button>
              <button type="submit" className="adm-btn adm-btn--dorado" disabled={guardando}>
                {guardando ? "Guardando..." : form.id ? "Guardar cambios" : "Crear plan"}
              </button>
            </div>
          </div>
        </form>
      )}

      <div className="adm-tabla-wrap">
        <table className="adm-tabla">
          <thead>
            <tr>
              <th>Plan</th>
              <th>Rango</th>
              <th>Precio por batería</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {planes.map((plan) => (
              <tr key={plan.id}>
                <td className="adm-fuerte">{plan.nombre}</td>
                <td>{etiquetaRango(plan.cantidadMin, plan.cantidadMax)}</td>
                <td>{formatearPrecio(plan.precioUnitario)}</td>
                <td>
                  <span className={`adm-chip ${plan.activo ? "adm-chip--info" : "adm-chip--neutro"}`}>
                    {plan.activo ? "Visible" : "Oculto"}
                  </span>
                </td>
                <td>
                  <div className="adm-acciones">
                    <button type="button" className="adm-accion" onClick={() => abrirEdicion(plan)}>
                      ✎ Editar
                    </button>
                    <button type="button" className="adm-accion adm-accion--peligro" onClick={() => eliminar(plan)}>
                      ✕ Eliminar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {planes.length === 0 && (
              <tr>
                <td colSpan={5} className="adm-vacio">
                  Aún no hay planes. Usa "Agregar plan".
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <ModalConfirmacion
        abierto={Boolean(planPorEliminar)}
        titulo="¿Eliminar plan?"
        mensaje={`Se eliminará "${planPorEliminar?.nombre}". Esta acción no se puede deshacer.`}
        textoConfirmar="Sí, eliminar"
        textoCancelar="Cancelar"
        tipo="peligro"
        cargando={eliminando}
        onConfirmar={confirmarEliminarPlan}
        onCancelar={() => {
          if (!eliminando) setPlanPorEliminar(null);
        }}
      />
    </section>
  );
}