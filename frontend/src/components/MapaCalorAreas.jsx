import { useEffect, useState } from "react";
import { fetchMapaCalor } from "../api/indicadores";
import "../styles/MapaCalorAreas.css";

const NIVELES = {
  SIN_RIESGO: { etiqueta: "Sin riesgo", fondo: "#DEF7EC", texto: "#03543F" },
  BAJO: { etiqueta: "Bajo", fondo: "#E1EFFE", texto: "#1E40AF" },
  MEDIO: { etiqueta: "Medio", fondo: "#FEF08A", texto: "#713F12" },
  ALTO: { etiqueta: "Alto", fondo: "#FDBA74", texto: "#9A3412" },
  MUY_ALTO: { etiqueta: "Muy alto", fondo: "#FCA5A5", texto: "#991B1B" },
};

function CeldaMapa({ celda }) {
  if (!celda) {
    return <td className="mapa-calor__celda mapa-calor__celda--vacia">-</td>;
  }
  if (celda.anonimizado) {
    return (
      <td
        className="mapa-calor__celda mapa-calor__celda--oculta"
        title="Hay menos participantes que el mínimo requerido para proteger el anonimato"
      >
        Oculto
      </td>
    );
  }
  const nivel = NIVELES[celda.nivel];
  return (
    <td
      className="mapa-calor__celda"
      style={{ background: nivel.fondo, color: nivel.texto }}
      title={`${nivel.etiqueta}: ${celda.total} participantes, ${celda.porcentajeAltoMuyAlto}% en riesgo alto o muy alto`}
    >
      <span className="mapa-calor__nivel">{nivel.etiqueta}</span>
      <span className="mapa-calor__n">n={celda.total}</span>
    </td>
  );
}

export default function MapaCalorAreas({ token, organizacionId }) {
  const [datos, setDatos] = useState(null);
  const [codigo, setCodigo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let activo = true;
    setCargando(true);
    setError(null);
    fetchMapaCalor(token, organizacionId, codigo)
      .then((respuesta) => {
        if (activo) setDatos(respuesta);
      })
      .catch((err) => {
        if (activo) setError(err.message || "No se pudo cargar el mapa de calor.");
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [token, organizacionId, codigo]);

  const categorias = datos?.categorias || [];
  const dimensiones = datos?.dimensiones || [];
  const areas = datos?.areas || [];

  return (
    <div className="mapa-calor">
      <div className="mapa-calor__encabezado">
        <div>
          <h2 className="mapa-calor__titulo">Mapa de calor por área</h2>
          <p className="mapa-calor__subtitulo">Nivel de riesgo predominante por área y dimensión.</p>
        </div>
        {categorias.length > 1 && (
          <select
            className="mapa-calor__selector"
            aria-label="Cuestionario del mapa de calor"
            value={codigo ?? datos.codigo}
            onChange={(evento) => setCodigo(evento.target.value)}
          >
            {categorias.map((categoria) => (
              <option key={categoria.codigo} value={categoria.codigo}>
                {categoria.nombre}
              </option>
            ))}
          </select>
        )}
      </div>

      {error && (
        <p className="mapa-calor__error" role="alert">
          {error}
        </p>
      )}

      {!error && cargando && !datos && <p className="mapa-calor__estado">Cargando mapa de calor...</p>}

      {!error && datos && areas.length === 0 && (
        <p className="mapa-calor__estado">Aún no hay resultados completados para generar el mapa de calor.</p>
      )}

      {!error && areas.length > 0 && (
        <>
          <div className="mapa-calor__contenedor">
            <table className="mapa-calor__tabla">
              <thead>
                <tr>
                  <th scope="col" className="mapa-calor__esquina">
                    Área
                  </th>
                  {dimensiones.map((dimension) => (
                    <th scope="col" key={dimension.codigo} title={dimension.dominio}>
                      {dimension.nombre}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {areas.map((area) => (
                  <tr key={area.id ?? "sin-area"}>
                    <th scope="row" className="mapa-calor__area">
                      {area.nombre}
                    </th>
                    {dimensiones.map((dimension) => (
                      <CeldaMapa key={dimension.codigo} celda={area.celdas[dimension.codigo]} />
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="mapa-calor__leyenda">
            {Object.values(NIVELES).map((nivel) => (
              <li key={nivel.etiqueta}>
                <span className="mapa-calor__muestra" style={{ background: nivel.fondo }} />
                {nivel.etiqueta}
              </li>
            ))}
          </ul>
          <p className="mapa-calor__nota">
            Las celdas con menos de {datos.minimoAnonimato} participantes completados no se muestran para proteger
            el anonimato.
          </p>
        </>
      )}
    </div>
  );
}
