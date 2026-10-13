import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import { useAuth } from "../context/AuthContext";
import { fetchEncuestasRealizadas, fetchRespuestasEncuesta } from "../api/reportes";
import {
  ESTADOS_ENCUESTA,
  NIVELES,
  NOMBRES_INSTRUMENTO,
  formatearFecha,
  iniciales,
  normalizar,
  textoRespuesta,
} from "../utils/encuestas";
import "../styles/app-shell.css";
import "../styles/Respuestas.css";

// Pestañas en el orden en que se responde la batería
const ORDEN_INSTRUMENTOS = ["FICHA_DATOS", "ESTRES", "EXTRALABORAL", "INTRALABORAL_A", "INTRALABORAL_B"];

const NOMBRES_PESTANA = {
  ...NOMBRES_INSTRUMENTO,
  FICHA_DATOS: "Sociodemográfico",
};

// Secciones de la Ficha de datos generales (códigos F1..F21 del seed)
const SECCIONES_FICHA = [
  { titulo: "Datos personales", desde: 1, hasta: 11 },
  { titulo: "Datos ocupacionales", desde: 12, hasta: 21 },
];

// Antigüedad se guarda en años ("0" = menos de un año) y las horas como número
function valorFicha(codigo, valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  if (codigo === "F14" || codigo === "F17") {
    if (String(valor) === "0") return "Menos de 1 año";
    return `${valor} ${String(valor) === "1" ? "año" : "años"}`;
  }
  if (codigo === "F20") return `${valor} horas`;
  return String(valor);
}

function numeroFicha(codigo) {
  return Number(String(codigo || "").replace(/\D/g, "")) || 0;
}

function NivelBadge({ nivel }) {
  if (!nivel) return null;
  const n = NIVELES[nivel];
  return (
    <span className="resp-nivel" style={n ? { background: n.bg, color: n.text } : undefined}>
      {n ? n.label : nivel}
    </span>
  );
}

function EstadoBadge({ estado }) {
  const e = ESTADOS_ENCUESTA[estado] || ESTADOS_ENCUESTA.PENDIENTE;
  return <span className={`resp-estado resp-estado--${(estado || "PENDIENTE").toLowerCase()}`}>{e.label}</span>;
}

/* ---------- Pestaña Sociodemográfico (Ficha de datos generales) ---------- */
function FichaSociodemografica({ respuestas }) {
  if (respuestas.length === 0) {
    return <p className="resp-vacio">El usuario aún no ha llenado la Ficha de datos generales.</p>;
  }
  return SECCIONES_FICHA.map((seccion) => {
    const campos = respuestas.filter((r) => {
      const n = numeroFicha(r.codigo);
      return n >= seccion.desde && n <= seccion.hasta;
    });
    if (campos.length === 0) return null;
    return (
      <section key={seccion.titulo} className="resp-bloque">
        <h3 className="resp-bloque-titulo">{seccion.titulo}</h3>
        <dl className="resp-ficha">
          {campos.map((r) => (
            <div key={r.codigo} className="resp-ficha-campo">
              <dt>{r.enunciado}</dt>
              <dd>{valorFicha(r.codigo, r.valor)}</dd>
            </div>
          ))}
        </dl>
      </section>
    );
  });
}

/* ---------- Pestaña de un cuestionario calificado (Estrés, Extralaboral, Intralaboral) ---------- */
function CuestionarioDetalle({ instrumento, resultados }) {
  const { codigo, respuestas } = instrumento;

  // Resultados de este instrumento indexados por tipo y nombre
  const delInstrumento = resultados.filter((r) => r.instrumento === codigo);
  // Estrés y Extralaboral no tienen fila TOTAL: su única dimensión es el resultado del cuestionario
  const dimensionesCalificadas = delInstrumento.filter((r) => r.tipo === "DIMENSION");
  const total =
    delInstrumento.find((r) => r.tipo === "TOTAL") ||
    (dimensionesCalificadas.length === 1 ? dimensionesCalificadas[0] : null);
  const porNombre = (tipo, nombre) =>
    delInstrumento.find((r) => r.tipo === tipo && r.dimension === nombre && r !== total);

  // Respuestas agrupadas dominio -> dimensión, conservando el orden de aparición
  const dominios = [];
  for (const r of respuestas) {
    let dom = dominios.find((d) => d.nombre === r.dominio);
    if (!dom) {
      dom = { nombre: r.dominio, dimensiones: [] };
      dominios.push(dom);
    }
    let dim = dom.dimensiones.find((d) => d.nombre === r.dimension);
    if (!dim) {
      dim = { nombre: r.dimension, respuestas: [] };
      dom.dimensiones.push(dim);
    }
    dim.respuestas.push(r);
  }
  // Con un solo dominio (Estrés, Extralaboral) el encabezado de dominio sobra
  const mostrarDominios = dominios.length > 1;

  return (
    <>
      <div className="resp-resumen">
        <div>
          <span className="resp-resumen-label">Resultado total</span>
          {total ? (
            <span className="resp-resumen-valor">
              {total.puntajeTransformado.toFixed(1)}
              <small> / 100</small>
            </span>
          ) : (
            <span className="resp-resumen-pendiente">
              Se calcula cuando el usuario termina toda la batería
            </span>
          )}
        </div>
        {total && <NivelBadge nivel={total.nivel} />}
        <span className="resp-resumen-conteo">{respuestas.length} respuestas</span>
      </div>

      {respuestas.length === 0 ? (
        <p className="resp-vacio">El usuario aún no ha respondido este cuestionario.</p>
      ) : (
        dominios.map((dom) => {
          const resDominio = porNombre("DOMINIO", dom.nombre);
          return (
            <section key={dom.nombre} className="resp-bloque">
              {mostrarDominios && (
                <div className="resp-dominio">
                  <h3 className="resp-bloque-titulo">{dom.nombre}</h3>
                  {resDominio && (
                    <span className="resp-puntaje">
                      {resDominio.puntajeTransformado.toFixed(1)} <NivelBadge nivel={resDominio.nivel} />
                    </span>
                  )}
                </div>
              )}
              {dom.dimensiones.map((dim) => {
                const resDim = porNombre("DIMENSION", dim.nombre);
                return (
                  <div key={dim.nombre} className="resp-dimension">
                    <div className="resp-dimension-cab">
                      <h4>{dim.nombre}</h4>
                      {resDim && (
                        <span className="resp-puntaje">
                          {resDim.puntajeTransformado.toFixed(1)} <NivelBadge nivel={resDim.nivel} />
                        </span>
                      )}
                    </div>
                    <ol className="resp-preguntas">
                      {dim.respuestas.map((r) => (
                        <li key={r.codigo || r.orden} className="resp-pregunta">
                          <span className="resp-num">{r.orden}</span>
                          <span className="resp-enunciado">{r.enunciado}</span>
                          <span className="resp-valor">{textoRespuesta(codigo, r.valor)}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                );
              })}
            </section>
          );
        })
      )}
    </>
  );
}

export default function Respuestas() {
  const { token } = useAuth();
  // ?id=<participanteId> deja abierto un usuario (se puede compartir o recargar)
  const [params, setParams] = useSearchParams();
  const seleccionado = params.get("id");

  const [encuestas, setEncuestas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [busqueda, setBusqueda] = useState("");

  // participanteId -> { datos } | { error } | { cargando }
  const [cache, setCache] = useState({});
  const [pestana, setPestana] = useState(null);

  useEffect(() => {
    if (!token) return;
    setCargando(true);
    fetchEncuestasRealizadas(token)
      .then((data) => setEncuestas(data || []))
      .catch((err) => setError(err.message || "Error al cargar los usuarios."))
      .finally(() => setCargando(false));
  }, [token]);

  // Pide las respuestas del usuario abierto una sola vez
  useEffect(() => {
    if (!token || !seleccionado || cache[seleccionado]) return;
    setCache((c) => ({ ...c, [seleccionado]: { cargando: true } }));
    fetchRespuestasEncuesta(token, seleccionado)
      .then((datos) => setCache((c) => ({ ...c, [seleccionado]: { datos } })))
      .catch((err) =>
        setCache((c) => ({ ...c, [seleccionado]: { error: err.message || "No se pudieron cargar las respuestas." } }))
      );
  }, [token, seleccionado, cache]);

  const filtradas = useMemo(() => {
    const q = normalizar(busqueda.trim());
    if (!q) return encuestas;
    return encuestas.filter((e) =>
      [e.trabajadorNombre, e.trabajadorEmail, e.participanteId, e.trabajadorId].some((campo) =>
        normalizar(campo).includes(q)
      )
    );
  }, [busqueda, encuestas]);

  const encuesta = encuestas.find((e) => e.participanteId === seleccionado);
  const entrada = seleccionado ? cache[seleccionado] : null;

  // Instrumentos del usuario en orden de la batería (asignados o con respuestas)
  const instrumentos = useMemo(() => {
    const lista = entrada?.datos?.instrumentos || [];
    return [...lista].sort((a, b) => ORDEN_INSTRUMENTOS.indexOf(a.codigo) - ORDEN_INSTRUMENTOS.indexOf(b.codigo));
  }, [entrada]);
  const activo = instrumentos.find((i) => i.codigo === pestana) || instrumentos[0];

  function seleccionar(participanteId) {
    setParams({ id: participanteId });
    setPestana(null);
    // En pantallas angostas el detalle queda debajo de la lista
    if (window.matchMedia("(max-width: 860px)").matches) {
      setTimeout(() => document.getElementById("resp-detalle")?.scrollIntoView({ behavior: "smooth" }), 0);
    }
  }

  return (
    <div className="app-shell-page resp-pagina">
      <AppTopbar />

      <main className="app-hero">
        <div className="app-content">
          {/* Fondo claro: texto oscuro en el botón */}
          <BotonRegresar tono="oscuro" />

          <h1 className="app-title">Respuestas</h1>
          <p className="app-subtitle">
            Ficha sociodemográfica y respuestas de cada usuario a los cuestionarios de estrés, extralaboral e intralaboral.
          </p>
          <p className="resp-nota-legal">
            Resultados individuales: información confidencial, visible solo para administradores y evaluadores SST.
          </p>

          {error && <div className="resp-error">⚠️ {error}</div>}

          <div className="resp-layout">
            {/* ---------- Lista de usuarios con buscador ---------- */}
            <aside className="resp-panel resp-lista">
              <div className="resp-buscador">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
                  <path d="m20 20-3.5-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                <input
                  type="search"
                  placeholder="Buscar por nombre o ID"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  aria-label="Buscar usuario por nombre o ID"
                />
                <span className="resp-contador">
                  {filtradas.length}/{encuestas.length}
                </span>
              </div>

              {cargando ? (
                <p className="resp-vacio">Cargando usuarios...</p>
              ) : filtradas.length === 0 ? (
                <p className="resp-vacio">
                  {encuestas.length === 0 ? "Todavía no hay usuarios con encuestas." : `Sin resultados para "${busqueda}".`}
                </p>
              ) : (
                <ul className="resp-usuarios">
                  {filtradas.map((e) => (
                    <li key={e.participanteId}>
                      <button
                        type="button"
                        className={`resp-usuario ${e.participanteId === seleccionado ? "resp-usuario--activo" : ""}`}
                        onClick={() => seleccionar(e.participanteId)}
                        aria-current={e.participanteId === seleccionado}
                      >
                        <span className="resp-avatar">{iniciales(e.trabajadorNombre)}</span>
                        <span className="resp-usuario-info">
                          <span className="resp-usuario-nombre">{e.trabajadorNombre}</span>
                          <span className="resp-usuario-meta">
                            ID {e.participanteId.slice(0, 8)} · {e.instrumentosCompletados}/{e.instrumentos.length}
                          </span>
                        </span>
                        <EstadoBadge estado={e.estado} />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </aside>

            {/* ---------- Detalle del usuario seleccionado ---------- */}
            <section id="resp-detalle" className="resp-panel resp-detalle">
              {!seleccionado ? (
                <p className="resp-vacio resp-vacio--grande">Selecciona un usuario para ver toda su información.</p>
              ) : (
                <>
                  {encuesta && (
                    <header className="resp-cabecera">
                      <span className="resp-avatar resp-avatar--grande">{iniciales(encuesta.trabajadorNombre)}</span>
                      <div className="resp-cabecera-info">
                        <h2>{encuesta.trabajadorNombre}</h2>
                        <p>{encuesta.viaEnlace ? "Paciente (enlace)" : encuesta.trabajadorEmail}</p>
                      </div>
                      <EstadoBadge estado={encuesta.estado} />

                      <dl className="resp-datos">
                        <div>
                          <dt>ID</dt>
                          <dd className="resp-id">{encuesta.participanteId}</dd>
                        </div>
                        <div>
                          <dt>Evaluación</dt>
                          <dd>{encuesta.evaluacionNombre}</dd>
                        </div>
                        {encuesta.organizacionNombre && (
                          <div>
                            <dt>Organización</dt>
                            <dd>{encuesta.organizacionNombre}</dd>
                          </div>
                        )}
                        <div>
                          <dt>Inicio</dt>
                          <dd>{formatearFecha(encuesta.fechaInicio)}</dd>
                        </div>
                        <div>
                          <dt>Finalización</dt>
                          <dd>{formatearFecha(encuesta.fechaFin)}</dd>
                        </div>
                        <div>
                          <dt>Avance</dt>
                          <dd>
                            {encuesta.instrumentosCompletados} de {encuesta.instrumentos.length} instrumentos
                          </dd>
                        </div>
                      </dl>
                    </header>
                  )}

                  {!entrada || entrada.cargando ? (
                    <p className="resp-vacio">Cargando respuestas...</p>
                  ) : entrada.error ? (
                    <p className="resp-vacio resp-vacio--error">{entrada.error}</p>
                  ) : instrumentos.length === 0 ? (
                    <p className="resp-vacio">Este usuario no tiene cuestionarios asignados.</p>
                  ) : (
                    <>
                      <div className="resp-tabs" role="tablist">
                        {instrumentos.map((inst) => (
                          <button
                            key={inst.codigo}
                            type="button"
                            role="tab"
                            aria-selected={inst.codigo === activo.codigo}
                            className={`resp-tab ${inst.codigo === activo.codigo ? "resp-tab--activa" : ""}`}
                            onClick={() => setPestana(inst.codigo)}
                          >
                            {inst.estado === "COMPLETADA" && <span aria-label="completado">✓</span>}
                            {NOMBRES_PESTANA[inst.codigo] || inst.nombre}
                          </button>
                        ))}
                      </div>

                      <div role="tabpanel">
                        {activo.codigo === "FICHA_DATOS" ? (
                          <FichaSociodemografica respuestas={activo.respuestas} />
                        ) : (
                          <CuestionarioDetalle instrumento={activo} resultados={encuesta?.resultados || []} />
                        )}
                      </div>
                    </>
                  )}
                </>
              )}
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
