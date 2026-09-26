import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useCuestionarioBackend } from "../hooks/useCuestionarioBackend";
import "../styles/cuestionario-estres.css";

// ⚠️ NO MODIFICAR el texto, el orden ni los ids: son parte del instrumento
// oficial (Batería de Riesgo Psicosocial — Cuestionario de Factores
// Psicosociales Extralaborales). Los ids se usan como clave de calificación.
const preguntas = [
  { id: 1,  texto: "Es fácil trasportarme entre mi casa y el trabajo." },
  { id: 2,  texto: "Tengo que tomar varios medios de transporte para llegar a mi lugar de trabajo." },
  { id: 3,  texto: "Paso mucho tiempo viajando de ida y regreso al trabajo." },
  { id: 4,  texto: "Me trasporto cómodamente entre mi casa y el trabajo." },
  { id: 5,  texto: "La zona donde vivo es segura." },
  { id: 6,  texto: "En la zona donde vivo se presentan hurtos y mucha delincuencia." },
  { id: 7,  texto: "Desde donde vivo me es fácil llegar al centro médico donde me atienden." },
  { id: 8,  texto: "Cerca a mi vivienda las vías están en buenas condiciones." },
  { id: 9,  texto: "Cerca a mi vivienda encuentro fácilmente transporte." },
  { id: 10, texto: "Las condiciones de mi vivienda son buenas." },
  { id: 11, texto: "En mi vivienda hay servicios de agua y luz." },
  { id: 12, texto: "Las condiciones de mi vivienda me permiten descansar cuando lo requiero." },
  { id: 13, texto: "Las condiciones de mi vivienda me permiten sentirme cómodo." },
  { id: 14, texto: "Me queda tiempo para actividades de recreación." },
  { id: 15, texto: "Fuera del trabajo tengo tiempo suficiente para descansar." },
  { id: 16, texto: "Tengo tiempo para atender mis asuntos personales y del hogar." },
  { id: 17, texto: "Tengo tiempo para compartir con mi familia o amigos." },
  { id: 18, texto: "Tengo buena comunicación con las personas cercanas." },
  { id: 19, texto: "Las relaciones con mis amigos son buenas." },
  { id: 20, texto: "Converso con personas cercanas sobre diferentes temas." },
  { id: 21, texto: "Mis amigos están dispuestos a escucharme cuando tengo problemas." },
  { id: 22, texto: "Cuento con el apoyo de mi familia cuando tengo problemas." },
  { id: 23, texto: "Puedo hablar con personas cercanas sobre las cosas que me pasan." },
  { id: 24, texto: "Mis problemas personales o familiares afectan mi trabajo." },
  { id: 25, texto: "La relación con mi familia cercana es cordial." },
  { id: 26, texto: "Mis problemas personales o familiares me quitan la energía que necesito para trabajar." },
  { id: 27, texto: "Los problemas con mis familiares los resolvemos de manera amistosa." },
  { id: 28, texto: "Mis problemas personales o familiares afectan mis relaciones en el trabajo." },
  { id: 29, texto: "El dinero que ganamos en el hogar alcanza para cubrir los gastos básicos." },
  { id: 30, texto: "Tengo otros compromisos económicos que afectan mucho el presupuesto familiar." },
  { id: 31, texto: "En mi hogar tenemos deudas difíciles de pagar." },
];

const PREGUNTAS_POR_PAGINA = 8;
const TOTAL_PAGINAS = Math.ceil(preguntas.length / PREGUNTAS_POR_PAGINA);

const MAPA_EXTRALABORAL = {
  "Siempre": 5,
  "Casi siempre": 4,
  "A veces": 3,
  "Algunas veces": 3,
  "Casi nunca": 2,
  "Nunca": 1,
};

const opciones = [
  "Siempre",
  "Casi siempre",
  "Algunas veces",
  "Casi nunca",
  "Nunca",
];

const RUTAS = {
  estres: "/cuestionario-estresB",
  extralaboral: "/cuestionario-extralaboralB",
  intralaboral: "/cuestionario-intralaboralB",
};

export default function CuestionarioExtralaboralB() {
  const navigate = useNavigate();
  const location = useLocation();

  const [pagina, setPagina] = useState(0);
  const [intentoFinalizar, setIntentoFinalizar] = useState(false);

  const {
    respuestas,
    seleccionarRespuesta,
    finalizarYNavegar,
  } = useCuestionarioBackend("EXTRALABORAL", MAPA_EXTRALABORAL);

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

    finalizarYNavegar();
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
              Cuestionario de Factores Psicosociales Extralaborales
            </h2>

            <p>
              Señale la frecuencia con que se presentan las siguientes
              situaciones relacionadas con su vida fuera del trabajo.
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
              Sección: Extralaboral
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