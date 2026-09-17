import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../styles/cuestionario-estres.css";

const preguntas = [
  { id: 1, texto: "Dolores en el cuello y espalda o tensión muscular." },
  { id: 2, texto: "Problemas gastrointestinales, úlcera péptica, acidez, problemas digestivos o del colon." },
  { id: 3, texto: "Problemas respiratorios." },
  { id: 4, texto: "Dolor de cabeza." },
  { id: 5, texto: "Trastornos del sueño como somnolencia durante el día o desvelo en la noche." },
  { id: 6, texto: "Palpitaciones en el pecho o problemas cardíacos." },
  { id: 7, texto: "Cambios fuertes del apetito." },
  { id: 8, texto: "Problemas relacionados con la función de los órganos genitales (impotencia, frigidez)." },
  { id: 9, texto: "Dificultad en las relaciones familiares." },
  { id: 10, texto: "Dificultad para permanecer quieto o dificultad para iniciar actividades." },
  { id: 11, texto: "Dificultad en las relaciones con otras personas." },
  { id: 12, texto: "Sensación de aislamiento y desinterés." },
  { id: 13, texto: "Sentimiento de sobrecarga de trabajo." },
  { id: 14, texto: "Dificultad para concentrarse, olvidos frecuentes." },
  { id: 15, texto: "Aumento en el número de accidentes de trabajo." },
  { id: 16, texto: "Sentimiento de frustración, de no haber hecho lo que se quería en la vida." },
  { id: 17, texto: "Cansancio, tedio o desgano." },
  { id: 18, texto: "Disminución del rendimiento en el trabajo o poca creatividad." },
  { id: 19, texto: "Deseo de no asistir al trabajo." },
  { id: 20, texto: "Bajo compromiso o poco interés con lo que se hace." },
  { id: 21, texto: "Dificultad para tomar decisiones." },
  { id: 22, texto: "Deseo de cambiar de empleo." },
  { id: 23, texto: "Sentimiento de soledad y miedo." },
  { id: 24, texto: "Sentimiento de irritabilidad, actitudes y pensamientos negativos." },
  { id: 25, texto: "Sentimiento de angustia, preocupación o tristeza." },
  { id: 26, texto: "Consumo de drogas para aliviar la tensión o los nervios." },
  { id: 27, texto: "Sentimientos de que \"no vale nada\", o \"no sirve para nada\"." },
  { id: 28, texto: "Consumo de bebidas alcohólicas o café o cigarrillo." },
  { id: 29, texto: "Sentimiento de que está perdiendo la razón." },
  { id: 30, texto: "Comportamientos rígidos, obstinación o terquedad." },
  { id: 31, texto: "Sensación de no poder manejar los problemas de la vida." },
];

const PREGUNTAS_POR_PAGINA = 8;
const TOTAL_PAGINAS = Math.ceil(preguntas.length / PREGUNTAS_POR_PAGINA);

const opciones = [
  "Siempre",
  "Casi siempre",
  "A veces",
  "Casi nunca",
  "Nunca",
];

// Rutas usadas para saber qué botón resaltar en el menú/pestañas
const RUTAS = {
  estres: "/cuestionario-estresB",
  extralaboral: "/cuestionario-extralaboralB",
  intralaboral: "/cuestionario-intralaboralB",
};

export default function CuestionarioEstres() {

  const navigate = useNavigate();
  const location = useLocation();

  const [respuestas, setRespuestas] = useState({});
  const [pagina, setPagina] = useState(0); // 0 = primera página (preguntas 1-8)
  const [intentoFinalizar, setIntentoFinalizar] = useState(false);

  const seleccionarRespuesta = (preguntaId, respuesta) => {
    setRespuestas({
      ...respuestas,
      [preguntaId]: respuesta,
    });
  };

  const inicio = pagina * PREGUNTAS_POR_PAGINA;
  const fin = Math.min(inicio + PREGUNTAS_POR_PAGINA, preguntas.length);
  const preguntasPagina = preguntas.slice(inicio, fin);

  const irAnterior = () => {
    if (pagina === 0) {
      navigate("/dashboard");
      return;
    }
    setPagina((p) => p - 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const irSiguiente = () => {
    if (pagina < TOTAL_PAGINAS - 1) {
      setPagina((p) => p + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    // Última página: no dejar finalizar si faltan preguntas por responder
    const preguntaSinResponder = preguntas.find(
      (p) => respuestas[p.id] === undefined
    );

    if (preguntaSinResponder) {
      const faltantes = preguntas.length - Object.keys(respuestas).length;
      const paginaFaltante = Math.floor(
        (preguntaSinResponder.id - 1) / PREGUNTAS_POR_PAGINA
      );

      setIntentoFinalizar(true);

      alert(
        `Te faltan ${faltantes} pregunta(s) por responder. Te llevamos a la primera pregunta sin responder (pregunta ${preguntaSinResponder.id}).`
      );

      setPagina(paginaFaltante);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    alert("Las respuestas han sido guardadas correctamente.");
  };

  return (
    <div className="questionnaire-page">

      {/* =====================================================
          MENÚ LATERAL
      ===================================================== */}

      <aside className="questionnaire-sidebar">

        {/* LOGO */}

        <div className="questionnaire-logo">


          <div>
            
            <img
            src="/logob1.png"
            alt="Magnus"
            style={{ height: 70, marginRight: "auto" }}
          />
          
          </div>

        </div>


        {/* MENÚ */}

        <nav className="questionnaire-menu">

          <button
            className={`questionnaire-menu-item ${
              location.pathname === RUTAS.estres ? "active" : ""
            }`}
            type="button"
            onClick={() => navigate(RUTAS.estres)}
          >
            <span>▣</span>

            <div>
              <strong>Estrés</strong>
              <small>31 preguntas</small>
            </div>

          </button>


          <button
            className={`questionnaire-menu-item ${
              location.pathname === RUTAS.extralaboral ? "active" : ""
            }`}
            type="button"
            onClick={() => navigate(RUTAS.extralaboral)}
          >
            <span>▣</span>

            <div>
              <strong>Factores extralaborales</strong>
              <small>31 preguntas</small>
            </div>

          </button>


          <button
            className={`questionnaire-menu-item ${
              location.pathname === RUTAS.intralaboral ? "active" : ""
            }`}
            type="button"
            onClick={() => navigate(RUTAS.intralaboral)}
          >
            <span>▣</span>

            <div>
              <strong>Factores intralaborales</strong>
              <small>Forma B · 88 preguntas</small>
            </div>

          </button>

        </nav>


        {/* PIE DEL MENÚ */}

        <div className="questionnaire-sidebar-footer">

          Tu bienestar también
          <br />
          es parte del trabajo

        </div>

      </aside>



      {/* =====================================================
          CONTENIDO
          
      ===================================================== */}

      <main className="questionnaire-main">

        {/* =================================================
            TARJETA DE PRESENTACIÓN
        ================================================= */}

        <section className="questionnaire-intro">

          <div className="questionnaire-heart">
            ♥
          </div>


          <div>

            <h2>
              Cuestionario para la Evaluación del Estrés
            </h2>

            <p>
              Tercera versión · Señale la frecuencia con que
              se han presentado estos malestares durante los
              últimos tres meses.
            </p>

          </div>

        </section>



        {/* =================================================
            PESTAÑAS
        ================================================= */}

        <div className="questionnaire-tabs">

          <button
            type="button"
            className={location.pathname === RUTAS.estres ? "active" : ""}
            onClick={() => navigate(RUTAS.estres)}
          >
            <strong>Estrés B</strong>
            <span>31</span>
          </button>

          <button
            type="button"
            className={location.pathname === RUTAS.extralaboral ? "active" : ""}
            onClick={() => navigate(RUTAS.extralaboral)}
          >
            <strong>Extralaboral B</strong>
            <span>31</span>
          </button>

          <button
            type="button"
            className={location.pathname === RUTAS.intralaboral ? "active" : ""}
            onClick={() => navigate(RUTAS.intralaboral)}
          >
            <strong>Intralaboral - Forma B</strong>
            <span>123</span>
          </button>

          <div className="general-progress">
            <span>Progreso general</span>
            <div className="general-progress-bar">
              <div
                style={{
                  width: `${Math.round((Object.keys(respuestas).length / preguntas.length) * 100)}%`,
                }}
              ></div>
            </div>
            <small>
              {Math.round((Object.keys(respuestas).length / preguntas.length) * 100)}%
            </small>
          </div>

        </div>

        {/* =================================================
            CONTENEDOR DE PREGUNTAS
        ================================================= */}

        <section className="questions-card">


          {/* ENCABEZADO DE PREGUNTAS */}

          <div className="questions-header">

            <div>

              <strong>
                Pregunta {inicio + 1}–{fin} de {preguntas.length}
              </strong>

              <div className="questions-progress">

                <div
                  style={{
                    width: `${(Object.keys(respuestas).length / preguntas.length) * 100}%`,
                  }}
                ></div>

              </div>

            </div>


            <span>
              Sección: Estrés
            </span>

          </div>



          {/* ENCABEZADO DE OPCIONES */}

          <div className="answers-header">

            <span>
              Frecuencia:
            </span>

            {opciones.map((opcion) => (

              <span key={opcion}>
                {opcion}
              </span>

            ))}

          </div>



          {/* PREGUNTAS */}

          <div className="questions-list">

            {preguntasPagina.map((pregunta) => (

              <div
                className={`question-row ${
                  intentoFinalizar && respuestas[pregunta.id] === undefined
                    ? "question-row-error"
                    : ""
                }`}
                key={pregunta.id}
              >


                {/* NÚMERO */}

                <div className="question-number">
                  {pregunta.id}
                </div>


                {/* TEXTO */}

                <div className="question-text">
                  {pregunta.id}. {pregunta.texto}
                </div>


                {/* RESPUESTAS */}

                {opciones.map((opcion) => (

                  <label
                    className="answer-option"
                    key={opcion}
                  >

                    <input
                      type="radio"
                      name={`pregunta-${pregunta.id}`}
                      value={opcion}
                      checked={
                        respuestas[pregunta.id] === opcion
                      }
                      onChange={() =>
                        seleccionarRespuesta(
                          pregunta.id,
                          opcion
                        )
                      }
                    />

                    <span className="custom-radio"></span>

                    <small>
                      {opcion}
                    </small>

                  </label>

                ))}

              </div>

            ))}

          </div>



          {/* BOTONES */}

          <div className="questionnaire-navigation">

            <button
              className="previous-button"
              type="button"
              onClick={irAnterior}
            >
              ← Anterior
            </button>

            <span className="page-indicator">
              Página {pagina + 1} de {TOTAL_PAGINAS}
            </span>

            <button
              className="next-button"
              type="button"
              onClick={irSiguiente}
            >
              {pagina < TOTAL_PAGINAS - 1 ? "Siguiente →" : "Finalizar"}
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}