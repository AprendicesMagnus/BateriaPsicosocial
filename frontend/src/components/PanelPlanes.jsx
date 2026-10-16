import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { crearPlan, editarPlan, eliminarPlan, fetchPlanesAdmin } from "../api/planes";
import { etiquetaRango, formatearPrecio } from "../utils/planes";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";

const VACIO = { nombre: "", cantidadMin: "", cantidadMax: "", precioUnitario: "", activo: true };

// Administración de los planes (solo Super Administrador, dentro del Panel).
export default function PanelPlanes() {
  const { token } = useAuth();
  const [planes, setPlanes] = useState([]);
  const [form, setForm] = useState(null); // null = cerrado; {id?, ...campos}
  const [guardando, setGuardando] = useState(false);
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

  async function eliminar(plan) {
    if (!window.confirm(`¿Eliminar "${plan.nombre}"? Esta acción no se puede deshacer.`)) return;
    try {
      await eliminarPlan(token, plan.id);
      await cargar();
      setMensaje({ tipo: "ok", texto: "Plan eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar el plan." });
    }
  }

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
        <form className="plan-form" onSubmit={guardar} noValidate>
          <label>
            Nombre
            <input type="text" maxLength={80} value={form.nombre} onChange={cambiar("nombre")} />
          </label>
          <label>
            Cantidad mínima
            <input type="number" min={1} value={form.cantidadMin} onChange={cambiar("cantidadMin")} />
          </label>
          <label>
            Cantidad máxima (vacío = en adelante)
            <input type="number" min={1} value={form.cantidadMax} onChange={cambiar("cantidadMax")} />
          </label>
          <label>
            Precio por batería (COP)
            <input type="number" min={0} value={form.precioUnitario} onChange={cambiar("precioUnitario")} />
          </label>
          <div className="plan-form__acciones">
            <label className="plan-form__check">
              <input type="checkbox" checked={form.activo} onChange={(e) => setForm((f) => ({ ...f, activo: e.target.checked }))} />
              Visible en la página
            </label>
            <button type="submit" className="adm-btn adm-btn--dorado" disabled={guardando}>
              {guardando ? "Guardando..." : "Guardar"}
            </button>
            <button type="button" className="adm-btn adm-btn--borde" onClick={() => setForm(null)} disabled={guardando}>
              Cancelar
            </button>
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
    </section>
  );
}