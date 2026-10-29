import { useEffect } from "react";
import { categoriasDe, formatearCOP, imagenDe, useProductos } from "../data/products";
import "../styles/Planes.css";
import "../styles/Catalogo.css";

export default function ModalCatalogo({ onCerrar }) {
  const { productos, cargando, error } = useProductos();

  useEffect(() => {
    const alTeclear = (e) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alTeclear);
    return () => window.removeEventListener("keydown", alTeclear);
  }, [onCerrar]);

  return (
    <div
      className="planes-fondo"
      role="dialog"
      aria-modal="true"
      aria-labelledby="catalogo-titulo"
      onClick={onCerrar}
    >
      <div
        className="planes-modal catalogo-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="planes-modal__cabecera">
          <div>
            <h2 id="catalogo-titulo">Catálogo de Productos</h2>
            <p>Equipos de seguridad y tecnología. Inicia sesión para comprarlos.</p>
          </div>

          <button
            type="button"
            className="planes-modal__cerrar"
            onClick={onCerrar}
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>

        {cargando && <p className="planes-vacio">Cargando productos…</p>}
        {error && <p className="planes-vacio">{error}</p>}
        {!cargando && !error && productos.length === 0 && (
          <p className="planes-vacio">Pronto publicaremos nuestros productos.</p>
        )}

        {!cargando &&
          !error &&
          categoriasDe(productos).map((categoria) => {
            const lista = productos.filter((p) => p.categoria === categoria);
            if (!lista.length) return null;

            return (
              <section key={categoria} className="catalogo-seccion">
                <h3 className="catalogo-seccion__titulo">{categoria}</h3>

                <div className="catalogo-grid catalogo-grid--compacto">
                  {lista.map((producto) => (
                    <article key={producto.id} className="producto-card">
                      <img
                        src={imagenDe(producto)}
                        alt={producto.nombre}
                        loading="lazy"
                      />
                      <div className="producto-card__cuerpo">
                        <h4>{producto.nombre}</h4>
                        <strong>{formatearCOP(producto.precio)}</strong>
                        <span className={`producto-stock ${producto.stock <= 0 ? "producto-stock--agotado" : producto.stock <= 5 ? "producto-stock--bajo" : ""}`}>
                          {producto.stock <= 0 ? "Agotado" : producto.stock <= 5 ? `Últimas ${producto.stock} unidades` : "Disponible"}
                        </span>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
      </div>
    </div>
  );
}
