import { useEffect, useState } from "react";
import { fetchAnalisisGrupos } from "../api/indicadores";
import "../styles/AnalisisGruposFicha.css";

export default function AnalisisGruposFicha({ token, organizacionId }) {
  const [datos, setDatos] = useState(null);
  const [codigo, setCodigo] = useState(null);
  const [variable, setVariable] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let activo = true;
    setCargando(true);
    setError(null);
    fetchAnalisisGrupos(token, organizacionId, { codigo, variable })
      .then((respuesta) => {
        if (activo) setDatos(respuesta);
      })
      .catch((err) => {
        if (activo) setError(err.message || "No se pudo cargar el análisis por grupos.");
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [token, organizacionId, codigo, variable]);

  const categorias = datos?.categorias || [];
  const variables = datos?.variables || [];
  const grupos = datos?.grupos || [];

  return (
    <div className="grupos">
      <div className="grupos__encabezado">
        <div>
          <h2 className="grupos__titulo">Análisis por grupos de la ficha de datos</h2>
          <p className="grupos__subtitulo">
            Porcentaje de resultados por dimensión en riesgo alto o muy alto, según la característica elegida.
          </p>
        </div>
        {datos && categorias.length > 0 && (
          <div className="grupos__controles">
            <select
              className="grupos__selector"
              aria-label="Característica para agrupar"
              value={variable ?? datos.variable}
              onChange={(evento) => setVariable(evento.target.value)}
            >
              {variables.map((opcion) => (
                <option key={opcion.clave} value={opcion.clave}>
                  {opcion.etiqueta}
                </option>
              ))}
            </select>
            {categorias.length > 1 && (
              <select
                className="grupos__selector"
                aria-label="Cuestionario del análisis"
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
        )}
      </div>

      {error && (
        <p className="grupos__error" role="alert">
          {error}
        </p>
      )}

      {!error && cargando && !datos && <p className="grupos__estado">Cargando análisis por grupos...</p>}

      {!error && datos && categorias.length === 0 && (
        <p className="grupos__estado">Aún no hay resultados completados para analizar por grupos.</p>
      )}

      {!error && datos && categorias.length > 0 && grupos.length === 0 && (
        <p className="grupos__estado">
          Ningún grupo de esta característica alcanza el mínimo de {datos.minimoAnonimato} participantes
          completados.
        </p>
      )}

      {grupos.length > 0 && (
        <ul className="grupos__lista">
          {grupos.map((grupo) => (
            <li key={grupo.nombre} className="grupos__item">
              <div className="grupos__fila">
                <span className="grupos__nombre">{grupo.nombre}</span>
                <span className="grupos__valor">{grupo.porcentajeAltoMuyAlto}% en riesgo alto o muy alto</span>
              </div>
              <div className="grupos__barra" aria-hidden="true">
                <span className="grupos__relleno" style={{ width: `${grupo.porcentajeAltoMuyAlto}%` }} />
              </div>
              <span className="grupos__meta">
                {grupo.participantes} participantes · puntaje promedio {grupo.promedioPuntaje}
              </span>
            </li>
          ))}
        </ul>
      )}

      {datos && grupos.length > 0 && (
        <p className="grupos__nota">
          {datos.gruposOcultos > 0 &&
            `${datos.gruposOcultos} grupo(s) no se muestran por tener menos de ${datos.minimoAnonimato} participantes. `}
          {datos.sinDato > 0 && `${datos.sinDato} participante(s) no respondieron esta pregunta de la ficha. `}
          Las diferencias entre grupos son descriptivas y no demuestran una relación de causa.
        </p>
      )}
    </div>
  );
}
