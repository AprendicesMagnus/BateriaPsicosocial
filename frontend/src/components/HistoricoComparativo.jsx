import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchHistoricoIndicadores } from "../api/indicadores";
import "../styles/HistoricoComparativo.css";

const TAMANO_VENTANA = 6;
const TAMANO_PAGINA = 5;

const NIVELES = [
  { clave: "SIN_RIESGO", etiqueta: "Sin riesgo", color: "#10b981" },
  { clave: "BAJO", etiqueta: "Bajo", color: "#3b82f6" },
  { clave: "MEDIO", etiqueta: "Medio", color: "#facc15" },
  { clave: "ALTO", etiqueta: "Alto", color: "#f97316" },
  { clave: "MUY_ALTO", etiqueta: "Muy alto", color: "#dc2626" },
];

function redondear(valor) {
  return Math.round(valor * 100) / 100;
}

function normalizar(texto) {
  return (texto || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function fechaCorta(iso) {
  return new Date(iso).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "2-digit" });
}

function fechaCompleta(iso) {
  return new Date(iso).toLocaleDateString("es-CO");
}

function DistribucionNiveles({ distribucion }) {
  const total = NIVELES.reduce((suma, nivel) => suma + (distribucion?.[nivel.clave] || 0), 0);
  if (total === 0) return <span className="historico__sin-datos">Sin datos</span>;
  const descripcion = NIVELES.filter((nivel) => distribucion[nivel.clave] > 0)
    .map((nivel) => `${nivel.etiqueta}: ${distribucion[nivel.clave]}`)
    .join(", ");
  return (
    <div className="historico__distribucion" role="img" aria-label={descripcion} title={descripcion}>
      {NIVELES.map((nivel) => {
        const cantidad = distribucion[nivel.clave] || 0;
        if (!cantidad) return null;
        return <span key={nivel.clave} style={{ width: `${(cantidad * 100) / total}%`, background: nivel.color }} />;
      })}
    </div>
  );
}

export default function HistoricoComparativo({ token, organizacionId }) {
  const [historico, setHistorico] = useState([]);
  const [minimo, setMinimo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [finVentana, setFinVentana] = useState(0);
  const [busqueda, setBusqueda] = useState("");
  const [pagina, setPagina] = useState(1);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const datos = await fetchHistoricoIndicadores(token, organizacionId);
      const lista = datos?.historico || [];
      setHistorico(lista);
      setMinimo(datos?.minimoAnonimato ?? null);
      setFinVentana(lista.filter((item) => !item.oculto).length);
      setPagina(1);
    } catch (err) {
      setError(err.message || "No se pudo cargar el histórico comparativo.");
    } finally {
      setCargando(false);
    }
  }, [token, organizacionId]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const total = historico.length;
  const visibles = useMemo(() => historico.filter((item) => !item.oculto), [historico]);
  const inicioVentana = Math.max(0, finVentana - TAMANO_VENTANA);
  const ventana = historico.slice(inicioVentana, finVentana);

  const resumen = useMemo(() => {
    if (visibles.length === 0) return null;
    const ultimo = visibles[visibles.length - 1];
    const anterior = visibles.length > 1 ? visibles[visibles.length - 2] : null;
    const menor = visibles.reduce((a, b) =>
      b.promedioPuntajeTransformado < a.promedioPuntajeTransformado ? b : a
    );
    const mayor = visibles.reduce((a, b) =>
      b.promedioPuntajeTransformado > a.promedioPuntajeTransformado ? b : a
    );
    const diferencia = anterior
      ? redondear(ultimo.promedioPuntajeTransformado - anterior.promedioPuntajeTransformado)
      : null;
    return { ultimo, menor, mayor, diferencia };
  }, [visibles]);

  const filas = useMemo(() => {
    const termino = normalizar(busqueda.trim());
    return [...historico]
      .reverse()
      .filter((item) => !termino || normalizar(item.nombreEvaluacion).includes(termino));
  }, [historico, busqueda]);

  const totalPaginas = Math.max(1, Math.ceil(filas.length / TAMANO_PAGINA));
  const paginaActual = Math.min(pagina, totalPaginas);
  const filasPagina = filas.slice((paginaActual - 1) * TAMANO_PAGINA, paginaActual * TAMANO_PAGINA);

  if (cargando) {
    return <p className="historico__estado">Cargando histórico comparativo...</p>;
  }

  if (error) {
    return (
      <div className="historico">
        <p className="historico__error" role="alert">
          {error}
        </p>
      </div>
    );
  }

  if (!resumen) {
    return (
      <div className="historico">
        <h2 className="historico__titulo">Histórico comparativo BRP</h2>
        <p className="historico__vacio">
          {historico.length > 0
            ? `Las evaluaciones registradas tienen menos de ${minimo} participantes; sus resultados se ocultan para proteger el anonimato.`
            : "Aún no existen evaluaciones finalizadas y tabuladas en esta organización para comparar la tendencia histórica de riesgo."}
        </p>
      </div>
    );
  }

  const { ultimo, menor, mayor, diferencia } = resumen;
  let textoCambio = "Sin evaluación anterior";
  let claseCambio = "";
  let detalleCambio = "";
  if (diferencia !== null) {
    if (diferencia < 0) {
      textoCambio = `Bajó ${Math.abs(diferencia)} pts`;
      claseCambio = " historico__tarjeta-valor--mejora";
      detalleCambio = "Menor riesgo que la evaluación anterior";
    } else if (diferencia > 0) {
      textoCambio = `Subió ${diferencia} pts`;
      claseCambio = " historico__tarjeta-valor--empeora";
      detalleCambio = "Mayor riesgo que la evaluación anterior";
    } else {
      textoCambio = "Sin cambio";
      detalleCambio = "Igual que la evaluación anterior";
    }
  }

  return (
    <div className="historico">
      <div className="historico__encabezado">
        <div>
          <h2 className="historico__titulo">Histórico comparativo BRP</h2>
          <p className="historico__subtitulo">
            Evolución del puntaje promedio de riesgo psicosocial entre evaluaciones. Un puntaje menor indica menor
            riesgo.
          </p>
        </div>
        <button type="button" className="historico__boton" onClick={cargar}>
          Actualizar
        </button>
      </div>

      <ul className="historico__resumen">
        <li className="historico__tarjeta">
          <span className="historico__tarjeta-etiqueta">Último puntaje</span>
          <span className="historico__tarjeta-valor">{ultimo.promedioPuntajeTransformado} pts</span>
          <span className="historico__tarjeta-detalle">{ultimo.nombreEvaluacion}</span>
        </li>
        <li className="historico__tarjeta">
          <span className="historico__tarjeta-etiqueta">Cambio frente a la anterior</span>
          <span className={`historico__tarjeta-valor${claseCambio}`}>{textoCambio}</span>
          {detalleCambio && <span className="historico__tarjeta-detalle">{detalleCambio}</span>}
        </li>
        <li className="historico__tarjeta">
          <span className="historico__tarjeta-etiqueta">Menor puntaje registrado</span>
          <span className="historico__tarjeta-valor">{menor.promedioPuntajeTransformado} pts</span>
          <span className="historico__tarjeta-detalle">{menor.nombreEvaluacion}</span>
        </li>
        <li className="historico__tarjeta">
          <span className="historico__tarjeta-etiqueta">Mayor puntaje registrado</span>
          <span className="historico__tarjeta-valor">{mayor.promedioPuntajeTransformado} pts</span>
          <span className="historico__tarjeta-detalle">{mayor.nombreEvaluacion}</span>
        </li>
      </ul>

      <div className="historico__grafico" role="group" aria-label="Puntaje promedio por evaluación">
        <h3 className="historico__grafico-titulo">Puntaje promedio por evaluación</h3>
        <ul className="historico__barras">
          {ventana.map((item) => {
            const esUltima = item.evaluacionId === ultimo.evaluacionId;
            const altura = Math.min(100, Math.max(4, item.promedioPuntajeTransformado));
            return (
              <li
                key={item.evaluacionId}
                className="historico__barra-item"
                title={`${item.nombreEvaluacion}: ${item.promedioPuntajeTransformado} pts`}
              >
                <span className="historico__barra-valor">{item.promedioPuntajeTransformado}</span>
                <span className="historico__barra-area">
                  <span
                    className={`historico__barra${esUltima ? " historico__barra--ultima" : ""}`}
                    style={{ height: `${altura}%` }}
                  />
                </span>
                <span className="historico__barra-fecha">{fechaCorta(item.fecha)}</span>
                <span className="historico__oculto">{item.nombreEvaluacion}</span>
              </li>
            );
          })}
        </ul>
        {total > TAMANO_VENTANA && (
          <div className="historico__navegacion">
            <button
              type="button"
              className="historico__boton"
              onClick={() =>
                setFinVentana(Math.max(Math.min(TAMANO_VENTANA, total), finVentana - TAMANO_VENTANA))
              }
              disabled={inicioVentana === 0}
            >
              Anteriores
            </button>
            <span aria-live="polite">
              Mostrando {inicioVentana + 1} a {finVentana} de {total} evaluaciones
            </span>
            <button
              type="button"
              className="historico__boton"
              onClick={() => setFinVentana(Math.min(total, finVentana + TAMANO_VENTANA))}
              disabled={finVentana >= total}
            >
              Más recientes
            </button>
          </div>
        )}
      </div>

      <div className="historico__herramientas">
        <label className="historico__busqueda" htmlFor="historico-busqueda">
          Buscar evaluación
          <input
            id="historico-busqueda"
            type="search"
            value={busqueda}
            placeholder="Nombre de la evaluación"
            onChange={(evento) => {
              setBusqueda(evento.target.value);
              setPagina(1);
            }}
          />
        </label>
        <span className="historico__contador" aria-live="polite">
          {filas.length} evaluación(es)
        </span>
      </div>

      <div className="historico__tabla-contenedor">
        <table className="historico__tabla">
          <caption className="historico__oculto">Evaluaciones registradas, de la más reciente a la más antigua</caption>
          <thead>
            <tr>
              <th scope="col">Evaluación</th>
              <th scope="col">Fecha</th>
              <th scope="col">Participantes</th>
              <th scope="col">Promedio</th>
              <th scope="col">Distribución de niveles</th>
            </tr>
          </thead>
          <tbody>
            {filasPagina.map((item) => (
              <tr key={item.evaluacionId}>
                <td className="historico__nombre">{item.nombreEvaluacion}</td>
                <td>{fechaCompleta(item.fecha)}</td>
                <td>{item.totalParticipantes}</td>
                <td className="historico__promedio">
                  {item.oculto ? "Oculto" : `${item.promedioPuntajeTransformado} pts`}
                </td>
                <td>
                  {item.oculto
                    ? <span className="historico__sin-datos">Oculto por anonimato</span>
                    : <DistribucionNiveles distribucion={item.distribucionNiveles} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {historico.some((item) => item.oculto) && (
        <p className="historico__vacio">
          Las evaluaciones con menos de {minimo} participantes no muestran resultados para proteger el anonimato.
        </p>
      )}

      {filas.length === 0 && <p className="historico__vacio">No hay evaluaciones que coincidan con la búsqueda.</p>}

      {filas.length > TAMANO_PAGINA && (
        <div className="historico__navegacion">
          <button
            type="button"
            className="historico__boton"
            onClick={() => setPagina(paginaActual - 1)}
            disabled={paginaActual === 1}
          >
            Anterior
          </button>
          <span aria-live="polite">
            Página {paginaActual} de {totalPaginas}
          </span>
          <button
            type="button"
            className="historico__boton"
            onClick={() => setPagina(paginaActual + 1)}
            disabled={paginaActual === totalPaginas}
          >
            Siguiente
          </button>
        </div>
      )}

      <ul className="historico__leyenda" aria-label="Leyenda de niveles de riesgo">
        {NIVELES.map((nivel) => (
          <li key={nivel.clave}>
            <span className="historico__muestra" style={{ background: nivel.color }} />
            {nivel.etiqueta}
          </li>
        ))}
      </ul>
    </div>
  );
}
