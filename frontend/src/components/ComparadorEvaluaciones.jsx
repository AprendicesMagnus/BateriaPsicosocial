import { useEffect, useState } from "react";
import { fetchHistoricoIndicadores, fetchCompararEvaluaciones } from "../api/indicadores";
import "../styles/ComparadorEvaluaciones.css";

function fechaCorta(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" });
}

export default function ComparadorEvaluaciones({ token, organizacionId }) {
  const [evaluacionesVisibles, setEvaluacionesVisibles] = useState([]);
  const [evaluacionA, setEvaluacionA] = useState("");
  const [evaluacionB, setEvaluacionB] = useState("");
  const [codigo, setCodigo] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [cargandoLista, setCargandoLista] = useState(true);
  const [cargandoComparacion, setCargandoComparacion] = useState(false);
  const [errorLista, setErrorLista] = useState(null);
  const [errorComparacion, setErrorComparacion] = useState(null);

  useEffect(() => {
    let activo = true;
    setCargandoLista(true);
    setErrorLista(null);
    fetchHistoricoIndicadores(token, organizacionId)
      .then((datos) => {
        if (!activo) return;
        const lista = (datos?.historico || [])
          .filter((item) => !item.oculto)
          .sort((a, b) => new Date(a.fecha) - new Date(b.fecha));
        setEvaluacionesVisibles(lista);
        if (lista.length >= 2) {
          setEvaluacionA(lista[lista.length - 2].evaluacionId);
          setEvaluacionB(lista[lista.length - 1].evaluacionId);
        }
      })
      .catch((err) => {
        if (activo) setErrorLista(err.message || "No se pudo cargar la lista de evaluaciones.");
      })
      .finally(() => {
        if (activo) setCargandoLista(false);
      });
    return () => {
      activo = false;
    };
  }, [token, organizacionId]);

  const mismaEvaluacion = Boolean(evaluacionA && evaluacionB && evaluacionA === evaluacionB);

  useEffect(() => {
    if (!evaluacionA || !evaluacionB || mismaEvaluacion) {
      setResultado(null);
      return;
    }
    let activo = true;
    setCargandoComparacion(true);
    setErrorComparacion(null);
    fetchCompararEvaluaciones(token, {
      evaluacionA,
      evaluacionB,
      organizacionId,
      codigo,
    })
      .then((res) => {
        if (!activo) return;
        setResultado(res);
        if (res.codigo && res.codigo !== codigo) {
          setCodigo(res.codigo);
        }
      })
      .catch((err) => {
        if (activo) setErrorComparacion(err.message || "No se pudo realizar la comparación.");
      })
      .finally(() => {
        if (activo) setCargandoComparacion(false);
      });
    return () => {
      activo = false;
    };
  }, [token, organizacionId, evaluacionA, evaluacionB, codigo, mismaEvaluacion]);

  if (cargandoLista) {
    return (
      <div className="comparador">
        <p className="comparador__vacio" role="alert">Cargando evaluaciones disponibles...</p>
      </div>
    );
  }

  if (errorLista) {
    return (
      <div className="comparador">
        <p className="comparador__error" role="alert">{errorLista}</p>
      </div>
    );
  }

  if (evaluacionesVisibles.length < 2) {
    return (
      <div className="comparador">
        <div className="comparador__encabezado">
          <div>
            <h2 className="comparador__titulo">Comparación entre dos evaluaciones</h2>
            <p className="comparador__subtitulo">
              Compara el puntaje promedio y niveles de riesgo de cada dimensión entre dos momentos en el tiempo.
            </p>
          </div>
        </div>
        <p className="comparador__vacio">
          Se necesitan al menos dos evaluaciones con 5 o más participantes completados para compararlas.
        </p>
      </div>
    );
  }

  const categorias = resultado?.categorias || [];
  const evalInfoA = resultado?.evaluaciones?.[0];
  const evalInfoB = resultado?.evaluaciones?.[1];
  const dimensiones = resultado?.dimensiones || [];

  return (
    <div className="comparador">
      <div className="comparador__encabezado">
        <div>
          <h2 className="comparador__titulo">Comparación entre dos evaluaciones</h2>
          <p className="comparador__subtitulo">
            Compara el puntaje promedio y niveles de riesgo de cada dimensión entre dos momentos en el tiempo.
          </p>
        </div>
      </div>

      <div className="comparador__selectores">
        <label className="comparador__campo">
          <span className="comparador__campo-etiqueta">Evaluación anterior (A):</span>
          <select
            className="comparador__select"
            value={evaluacionA}
            onChange={(e) => setEvaluacionA(e.target.value)}
          >
            {evaluacionesVisibles.map((ev) => (
              <option key={ev.evaluacionId} value={ev.evaluacionId}>
                {ev.nombreEvaluacion} ({fechaCorta(ev.fecha)})
              </option>
            ))}
          </select>
        </label>

        <label className="comparador__campo">
          <span className="comparador__campo-etiqueta">Evaluación a comparar (B):</span>
          <select
            className="comparador__select"
            value={evaluacionB}
            onChange={(e) => setEvaluacionB(e.target.value)}
          >
            {evaluacionesVisibles.map((ev) => (
              <option key={ev.evaluacionId} value={ev.evaluacionId}>
                {ev.nombreEvaluacion} ({fechaCorta(ev.fecha)})
              </option>
            ))}
          </select>
        </label>

        {categorias.length > 1 && (
          <label className="comparador__campo">
            <span className="comparador__campo-etiqueta">Cuestionario:</span>
            <select
              className="comparador__select"
              value={codigo ?? resultado?.codigo ?? ""}
              onChange={(e) => setCodigo(e.target.value)}
            >
              {categorias.map((c) => (
                <option key={c.codigo} value={c.codigo}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {mismaEvaluacion && (
        <p className="comparador__aviso" role="alert">
          Selecciona dos evaluaciones distintas para compararlas.
        </p>
      )}

      {errorComparacion && (
        <p className="comparador__error" role="alert">
          {errorComparacion}
        </p>
      )}

      {cargandoComparacion && (
        <p className="comparador__vacio" role="alert">
          Cargando datos de comparación...
        </p>
      )}

      {!cargandoComparacion && !errorComparacion && !mismaEvaluacion && resultado && (
        <>
          <div className="comparador__tarjetas">
            {evalInfoA && (
              <div className="comparador__tarjeta">
                <span className="comparador__tarjeta-letra">Evaluación A</span>
                <strong className="comparador__tarjeta-nombre">{evalInfoA.nombre}</strong>
                <span className="comparador__tarjeta-fecha">{fechaCorta(evalInfoA.fecha)}</span>
                <div className="comparador__tarjeta-datos">
                  <div>
                    <span className="comparador__tarjeta-etiqueta">Participantes:</span>
                    <span className="comparador__tarjeta-valor">{evalInfoA.participantes}</span>
                  </div>
                  <div>
                    <span className="comparador__tarjeta-etiqueta">Riesgo Alto / Muy Alto:</span>
                    <span className="comparador__tarjeta-valor">
                      {evalInfoA.oculto
                        ? "Oculto por anonimato"
                        : evalInfoA.porcentajeAltoMuyAlto !== null
                        ? `${evalInfoA.porcentajeAltoMuyAlto}%`
                        : "Sin datos"}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {evalInfoB && (
              <div className="comparador__tarjeta">
                <span className="comparador__tarjeta-letra">Evaluación B</span>
                <strong className="comparador__tarjeta-nombre">{evalInfoB.nombre}</strong>
                <span className="comparador__tarjeta-fecha">{fechaCorta(evalInfoB.fecha)}</span>
                <div className="comparador__tarjeta-datos">
                  <div>
                    <span className="comparador__tarjeta-etiqueta">Participantes:</span>
                    <span className="comparador__tarjeta-valor">{evalInfoB.participantes}</span>
                  </div>
                  <div>
                    <span className="comparador__tarjeta-etiqueta">Riesgo Alto / Muy Alto:</span>
                    <span className="comparador__tarjeta-valor">
                      {evalInfoB.oculto
                        ? "Oculto por anonimato"
                        : evalInfoB.porcentajeAltoMuyAlto !== null
                        ? `${evalInfoB.porcentajeAltoMuyAlto}%`
                        : "Sin datos"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {dimensiones.length === 0 ? (
            <p className="comparador__vacio">
              No hay cuestionarios ni dimensiones comunes entre ambas evaluaciones para comparar.
            </p>
          ) : (
            <div className="comparador__tabla-contenedor">
              <table className="comparador__tabla">
                <thead>
                  <tr>
                    <th>Dimensión</th>
                    <th>Dominio</th>
                    <th>A</th>
                    <th>B</th>
                    <th>Diferencia</th>
                  </tr>
                </thead>
                <tbody>
                  {dimensiones.map((dim) => {
                    const dif = dim.diferencia;
                    let claseDif = "comparador__diferencia--neutro";
                    let textoDif = "0 pts";

                    if (dif === null) {
                      textoDif = "Oculto";
                      claseDif = "comparador__diferencia--oculto";
                    } else if (dif < 0) {
                      textoDif = `Bajó ${Math.abs(dif)} pts`;
                      claseDif = "comparador__diferencia--mejora";
                    } else if (dif > 0) {
                      textoDif = `Subió ${dif} pts`;
                      claseDif = "comparador__diferencia--empeora";
                    }

                    return (
                      <tr key={dim.codigo}>
                        <td className="comparador__nombre">{dim.nombre}</td>
                        <td className="comparador__dominio">{dim.dominio || "—"}</td>
                        <td className="comparador__promedio">
                          {dim.promedioA !== null ? dim.promedioA : "Oculto"}
                        </td>
                        <td className="comparador__promedio">
                          {dim.promedioB !== null ? dim.promedioB : "Oculto"}
                        </td>
                        <td className={`comparador__diferencia ${claseDif}`}>
                          {textoDif}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          <p className="comparador__ayuda">
            Un puntaje menor indica menor riesgo. Solo se comparan los cuestionarios presentes en ambas evaluaciones.
          </p>
        </>
      )}
    </div>
  );
}
