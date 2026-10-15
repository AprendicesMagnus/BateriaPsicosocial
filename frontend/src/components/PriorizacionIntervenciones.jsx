import { useCallback, useEffect, useState } from "react";
import { fetchPriorizacion } from "../api/indicadores";
import { guardarSeguimientoRecomendacion } from "../api/seguimiento";
import "../styles/PriorizacionIntervenciones.css";

const ETIQUETAS_ESTADO = {
  PENDIENTE: "Pendiente",
  EN_PROGRESO: "En progreso",
  IMPLEMENTADA: "Implementada",
};

const ETIQUETAS_NIVEL = {
  ALTO: "Riesgo alto",
  MUY_ALTO: "Riesgo muy alto",
};

export default function PriorizacionIntervenciones({ token, organizacionId, onPlanActualizado }) {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [errorAccion, setErrorAccion] = useState(null);
  const [agregandoId, setAgregandoId] = useState(null);

  const cargar = useCallback(async () => {
    try {
      setDatos(await fetchPriorizacion(token, organizacionId));
      setError(null);
    } catch (err) {
      setError(err.message || "No se pudo cargar la priorización de intervenciones.");
    } finally {
      setCargando(false);
    }
  }, [token, organizacionId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function agregarAlPlan(recomendacionId) {
    setAgregandoId(recomendacionId);
    setErrorAccion(null);
    try {
      await guardarSeguimientoRecomendacion(token, {
        organizacionId,
        recomendacionId,
        estado: "PENDIENTE",
      });
      await cargar();
      if (onPlanActualizado) onPlanActualizado();
    } catch (err) {
      setErrorAccion(err.message || "No se pudo agregar la recomendación al plan de acción.");
    } finally {
      setAgregandoId(null);
    }
  }

  const dimensiones = datos?.dimensiones || [];

  return (
    <div className="priorizacion">
      <h2 className="priorizacion__titulo">Priorización de intervenciones</h2>
      <p className="priorizacion__subtitulo">
        Dimensiones con mayor riesgo, ordenadas por índice de prioridad: (2 x personas en riesgo muy alto + personas
        en riesgo alto) / participantes, de 0 a 2.
      </p>

      {error && (
        <p className="priorizacion__error" role="alert">
          {error}
        </p>
      )}
      {errorAccion && (
        <p className="priorizacion__error" role="alert">
          {errorAccion}
        </p>
      )}
      {!error && cargando && <p className="priorizacion__estado">Cargando priorización...</p>}

      {!error && !cargando && dimensiones.length === 0 && (
        <p className="priorizacion__estado">
          No hay dimensiones en riesgo alto o muy alto con suficientes participantes para priorizar.
        </p>
      )}

      {dimensiones.length > 0 && (
        <ol className="priorizacion__lista">
          {dimensiones.map((dimension, posicion) => {
            const porcentajeMuyAlto = (dimension.distribucion.MUY_ALTO * 100) / dimension.total;
            const porcentajeAlto = (dimension.distribucion.ALTO * 100) / dimension.total;
            return (
              <li key={dimension.id} className="priorizacion__item">
                <div className="priorizacion__cabecera">
                  <span className="priorizacion__posicion">{posicion + 1}</span>
                  <div className="priorizacion__info">
                    <strong>{dimension.nombre}</strong>
                    <span className="priorizacion__meta">
                      {dimension.cuestionario} · {dimension.total} participantes
                    </span>
                  </div>
                  <div className="priorizacion__metricas">
                    <span>{dimension.porcentajeAltoMuyAlto}% en riesgo alto o muy alto</span>
                    <span>Índice {dimension.indice}</span>
                  </div>
                </div>

                <div className="priorizacion__barra" aria-hidden="true">
                  <span className="priorizacion__tramo priorizacion__tramo--muy-alto" style={{ width: `${porcentajeMuyAlto}%` }} />
                  <span className="priorizacion__tramo priorizacion__tramo--alto" style={{ width: `${porcentajeAlto}%` }} />
                </div>

                {dimension.recomendaciones.length === 0 ? (
                  <p className="priorizacion__estado">No hay recomendaciones registradas para esta dimensión.</p>
                ) : (
                  <ul className="priorizacion__recomendaciones">
                    {dimension.recomendaciones.map((recomendacion) => (
                      <li key={recomendacion.id} className="priorizacion__recomendacion">
                        <div className="priorizacion__texto">
                          <strong>{recomendacion.titulo}</strong>
                          <span className="priorizacion__nivel">{ETIQUETAS_NIVEL[recomendacion.nivel]}</span>
                          <p>{recomendacion.descripcion}</p>
                        </div>
                        {recomendacion.estadoSeguimiento ? (
                          <span className="priorizacion__en-plan">
                            En el plan: {ETIQUETAS_ESTADO[recomendacion.estadoSeguimiento]}
                          </span>
                        ) : (
                          <button
                            type="button"
                            className="priorizacion__agregar"
                            disabled={agregandoId === recomendacion.id}
                            onClick={() => agregarAlPlan(recomendacion.id)}
                          >
                            {agregandoId === recomendacion.id ? "Agregando..." : "Agregar al plan de acción"}
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ol>
      )}

      {datos?.dimensionesOcultas > 0 && (
        <p className="priorizacion__nota">
          {datos.dimensionesOcultas} dimensión(es) no se muestran porque no alcanzan el mínimo de{" "}
          {datos.minimoAnonimato} participantes completados.
        </p>
      )}
    </div>
  );
}
