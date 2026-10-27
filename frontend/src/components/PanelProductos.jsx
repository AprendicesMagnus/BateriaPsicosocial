import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { descargarExportacionPanel } from "../api/panel";
import { subirImagenProducto } from "../api/productos";
import { categoriasDe, CATEGORIAS_PRODUCTO, formatearCOP, imagenDe, useProductos } from "../data/products";
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
  const [subiendo, setSubiendo] = useState(false);
  const [categoriaNueva, setCategoriaNueva] = useState(false);
  const [exportando, setExportando] = useState(false);

  async function exportar() {
    setExportando(true);
    try {
      await descargarExportacionPanel(token, "productos");
      setMensaje({ tipo: "ok", texto: "Inventario de productos exportado con éxito." });
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No fue posible exportar el inventario." });
    } finally {
      setExportando(false);
    }
  }

  const cambiar = (campo) => (e) =>
    setForm((actual) => ({ ...actual, [campo]: e.target.value }));

  async function elegirImagen(e) {
    const archivo = e.target.files?.[0];
    e.target.value = "";
    if (!archivo) return;
    if (!/^image\/(jpeg|png|webp)$/.test(archivo.type)) {
      setMensaje({ tipo: "error", texto: "Usa una imagen JPG, PNG o WEBP." });
      return;
    }
    if (archivo.size > 3 * 1024 * 1024) {
      setMensaje({ tipo: "error", texto: "La imagen no puede superar los 3 MB." });
      return;
    }
    setSubiendo(true);
    setMensaje(null);
    try {
      const { imagen_url } = await subirImagenProducto(token, archivo);
      setForm((actual) => ({ ...actual, imagen_url }));
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message || "No se pudo subir la imagen." });
    } finally {
      setSubiendo(false);
    }
  }

  const categorias = categoriasDe([...productos, ...(form?.categoria ? [{ categoria: form.categoria }] : [])]);
  const opciones = categorias.length ? categorias : CATEGORIAS_PRODUCTO;

  const abrirNuevo = () => {
    setMensaje(null);
    setCategoriaNueva(false);
    setForm({ ...VACIO });
  };

  const abrirEdicion = (producto) => {
    setMensaje(null);
    setCategoriaNueva(false);
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

    const categoria = form.categoria.trim().replace(/\s+/g, " ");
    if (categoria.length < 2 || categoria.length > 40) {
      setMensaje({ tipo: "error", texto: "La categoría debe tener entre 2 y 40 caracteres." });
      return;
    }

    if (!Number.isInteger(precio) || precio <= 0) {
      setMensaje({ tipo: "error", texto: "El precio debe ser un número entero en pesos." });
      return;
    }

    const datos = {
      nombre: form.nombre.trim(),
      categoria,
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
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <button type="button" className="adm-btn adm-btn--borde" disabled={exportando} onClick={exportar}>
            {exportando ? "Exportando..." : "Exportar a Excel"}
          </button>
          <button type="button" className="adm-btn adm-btn--oscuro" onClick={abrirNuevo}>
            + Agregar producto
          </button>
        </div>
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
            {categoriaNueva ? (
              <>
                <input
                  type="text"
                  maxLength={40}
                  placeholder="Nombre de la nueva categoría"
                  value={form.categoria}
                  onChange={cambiar("categoria")}
                  autoFocus
                />
                <button
                  type="button"
                  className="adm-accion"
                  onClick={() => {
                    setCategoriaNueva(false);
                    setForm((a) => ({ ...a, categoria: opciones[0] }));
                  }}
                >
                  ← Usar una existente
                </button>
              </>
            ) : (
              <select
                value={form.categoria}
                onChange={(e) => {
                  if (e.target.value === "__nueva__") {
                    setCategoriaNueva(true);
                    setForm((a) => ({ ...a, categoria: "" }));
                  } else {
                    cambiar("categoria")(e);
                  }
                }}
              >
                {opciones.map((categoria) => (
                  <option key={categoria} value={categoria}>
                    {categoria}
                  </option>
                ))}
                <option value="__nueva__">➕ Nueva categoría…</option>
              </select>
            )}
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

          <div className="producto-imagen">
            <img className="producto-imagen__vista" src={imagenDe({ imagen_url: form.imagen_url })} alt="Vista previa" />
            <div className="producto-imagen__campos">
              <span>Imagen del producto</span>
              <div className="producto-imagen__botones">
                <label className="adm-btn adm-btn--borde producto-imagen__subir">
                  {subiendo ? "Subiendo…" : form.imagen_url ? "Cambiar imagen" : "Cargar imagen"}
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={elegirImagen}
                    disabled={subiendo}
                    hidden
                  />
                </label>
                {form.imagen_url && (
                  <button
                    type="button"
                    className="adm-accion adm-accion--peligro"
                    onClick={() => setForm((a) => ({ ...a, imagen_url: "" }))}
                  >
                    ✕ Quitar
                  </button>
                )}
              </div>
              <small>JPG, PNG o WEBP, máximo 3 MB.</small>
            </div>
          </div>

          <div className="plan-form__acciones">
            <button type="submit" className="adm-btn adm-btn--dorado" disabled={subiendo}>
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
