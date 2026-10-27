import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { CATEGORIAS_PRODUCTO, formatearCOP, imagenDe, useProductos } from "../data/products";
import "../styles/Planes.css";
import "../styles/PanelAcciones.css";
import "../styles/Catalogo.css";

const VACIO = {
  nombre: "",
  categoria: CATEGORIAS_PRODUCTO[0],
  precio: "",
  imagen_url: "",
};

export default function PanelProductos() {
  const { token } = useAuth();
  const { productos, cargando, error, crear, actualizar, eliminar } = useProductos({
    token,
    admin: true,
  });

  const [form, setForm] = useState(null);
  const [mensaje, setMensaje] = useState(null);

  const cambiar = (campo) => (e) =>
    setForm((actual) => ({ ...actual, [campo]: e.target.value }));

  const abrirNuevo = () => {
    setMensaje(null);
    setForm({ ...VACIO });
  };

  const abrirEdicion = (producto) => {
    setMensaje(null);
    setForm({
      id: producto.id,
      nombre: producto.nombre,
      categoria: producto.categoria,
      precio: String(producto.precio),
      imagen_url: producto.imagen_url || "",
    });
  };

  async function guardar(e) {
    e.preventDefault();

    const precio = Number(form.precio);

    if (form.nombre.trim().length < 2) {
      setMensaje({ tipo: "error", texto: "Escribe el nombre del producto." });
      return;
    }

    if (!Number.isInteger(precio) || precio <= 0) {
      setMensaje({ tipo: "error", texto: "El precio debe ser un número entero en pesos." });
      return;
    }

    const datos = {
      nombre: form.nombre.trim(),
      categoria: form.categoria,
      precio,
      imagen_url: form.imagen_url.trim(),
    };

    try {
      if (form.id) {
        await actualizar(form.id, datos);
      } else {
        await crear(datos);
      }

      setForm(null);
      setMensaje({ tipo: "ok", texto: "Producto guardado correctamente." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo guardar el producto." });
    }
  }

  async function borrar(producto) {
    if (!window.confirm(`¿Eliminar "${producto.nombre}"? Esta acción no se puede deshacer.`)) {
      return;
    }

    try {
      await eliminar(producto.id);
      setMensaje({ tipo: "ok", texto: "Producto eliminado." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo eliminar el producto." });
    }
  }

  return (
    <section id="productos" className="adm-card">
      <div className="adm-card__head">
        <div>
          <h2>Gestión de Productos</h2>
          <span>Los productos se guardan en la base de datos y aparecen en el catálogo.</span>
        </div>
        <button type="button" className="adm-btn adm-btn--oscuro" onClick={abrirNuevo}>
          + Agregar producto
        </button>
      </div>

      {mensaje && (
        <div className={`plan-mensaje plan-mensaje--${mensaje.tipo}`}>
          {mensaje.texto}
        </div>
      )}

      {error && <div className="plan-mensaje plan-mensaje--error">{error}</div>}

      {form && (
        <form className="plan-form" onSubmit={guardar} noValidate>
          <label>
            Nombre
            <input
              type="text"
              maxLength={120}
              value={form.nombre}
              onChange={cambiar("nombre")}
            />
          </label>

          <label>
            Categoría
            <select value={form.categoria} onChange={cambiar("categoria")}>
              {CATEGORIAS_PRODUCTO.map((categoria) => (
                <option key={categoria} value={categoria}>
                  {categoria}
                </option>
              ))}
            </select>
          </label>

          <label>
            Precio (COP)
            <input
              type="number"
              min={1}
              value={form.precio}
              onChange={cambiar("precio")}
            />
          </label>

          <label>
            URL de la imagen (opcional)
            <input
              type="url"
              placeholder="https://..."
              maxLength={500}
              value={form.imagen_url}
              onChange={cambiar("imagen_url")}
            />
          </label>

          <div className="plan-form__acciones">
            <button type="submit" className="adm-btn adm-btn--dorado">
              Guardar
            </button>
            <button
              type="button"
              className="adm-btn adm-btn--borde"
              onClick={() => setForm(null)}
            >
              Cancelar
            </button>
          </div>
        </form>
      )}

      {cargando ? (
        <p className="adm-vacio">Cargando productos…</p>
      ) : (
        <div className="adm-tabla-wrap">
          <table className="adm-tabla">
            <thead>
              <tr>
                <th>Imagen</th>
                <th>Producto</th>
                <th>Categoría</th>
                <th>Precio</th>
                <th>Acciones</th>
              </tr>
            </thead>

            <tbody>
              {productos.map((producto) => (
                <tr key={producto.id}>
                  <td>
                    <img className="producto-mini" src={imagenDe(producto)} alt="" />
                  </td>
                  <td className="adm-fuerte">{producto.nombre}</td>
                  <td>
                    <span
                      className={`adm-chip ${
                        producto.categoria === "SST"
                          ? "adm-chip--info"
                          : "adm-chip--neutro"
                      }`}
                    >
                      {producto.categoria}
                    </span>
                  </td>
                  <td>{formatearCOP(producto.precio)}</td>
                  <td>
                    <div className="adm-acciones">
                      <button
                        type="button"
                        className="adm-accion"
                        onClick={() => abrirEdicion(producto)}
                      >
                        ✎ Editar
                      </button>
                      <button
                        type="button"
                        className="adm-accion adm-accion--peligro"
                        onClick={() => borrar(producto)}
                      >
                        ✕ Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}

              {!productos.length && (
                <tr>
                  <td colSpan={5} className="adm-vacio">
                    No hay productos registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
