import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCuestionarioBackend } from "../hooks/useCuestionarioBackend";
// Muestra "Cargando…" o el error cuando las respuestas no se pueden guardar
import AvisoCuestionario from "../components/AvisoCuestionario";
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

const MAPA_ESTRES = {
  "Siempre": 4,
  "Casi siempre": 3,
  "A veces": 2,
  "Nunca": 1,
};

const opciones = Object.keys(MAPA_ESTRES);

export default function CuestionarioEstres() {
  const navigate = useNavigate();

  const [pagina, setPagina] = useState(0);
  const [intentoFinalizar, setIntentoFinalizar] = useState(false);

  const {
    respuestas,
    seleccionarRespuesta,
    finalizarYNavegar,
    cargando, // true mientras se carga el cuestionario desde el backend
    error, // mensaje cuando no hay evaluación o falla el guardado
  } = useCuestionarioBackend("ESTRES", MAPA_ESTRES);

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
            className="questionnaire-menu-item active"
            type="button"
            onClick={() => navigate("/cuestionario-estres")}
          >
            <span>▣</span>
            <div>
              <strong>Estrés</strong>
              <small>31 preguntas</small>
            </div>
          </button>

          <button
            className="questionnaire-menu-item"
            type="button"
            onClick={() => navigate("/cuestionario-extralaboral")}
          >
            <span>▣</span>
            <div>
              <strong>Factores extralaborales</strong>
              <small>31 preguntas</small>
            </div>
          </button>

          <button
            className="questionnaire-menu-item"
            type="button"
            onClick={() => navigate("/cuestionario-intralaboral")}
          >
            <span>▣</span>
            <div>
              <strong>Factores intralaborales</strong>
              <small>Forma A · 123 preguntas</small>
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
        {/* Aviso de carga / error del guardado en la BD */}
        <AvisoCuestionario cargando={cargando} error={error} />

        {/* TARJETA DE PRESENTACIÓN */}
        <section className="questionnaire-intro">
          <div className="questionnaire-heart">♥</div>
          <div>
            <h2>Cuestionario para la Evaluación del Estrés</h2>
            <p>
              Tercera versión · Señale la frecuencia con que
              se han presentado estos malestares durante los
              últimos tres meses.
            </p>
          </div>
        </section>

        {/* PESTAÑAS */}
        <div className="questionnaire-tabs">
          <button
            type="button"
            className="active"
            onClick={() => navigate("/cuestionario-estres")}
          >
            <strong>Estrés</strong>
            <span>31</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/cuestionario-extralaboral")}
          >
            <strong>Extralaboral</strong>
            <span>31</span>
          </button>

          <button
            type="button"
            onClick={() => navigate("/cuestionario-intralaboral")}
          >
            <strong>Intralaboral - Forma A</strong>
            <span>123</span>
          </button>
        </div>

        {/* PREGUNTAS Y NAVEGACIÓN */}
        <section className="questionnaire-content">
          <div className="questions-list">
            {preguntasPagina.map((pregunta) => (
              <div key={pregunta.id} className="question-item">
                <p className="question-text">
                  {pregunta.id}. {pregunta.texto}
                </p>
                <div className="options-group">
                  {opciones.map((opcion) => (
                    <label key={opcion} className="option-label">
                      <input
                        type="radio"
                        name={`pregunta-${pregunta.id}`}
                        // Se compara y se envía el TEXTO de la opción ("Siempre", "A veces"...):
                        // useCuestionarioBackend lo convierte a número con MAPA_ESTRES al guardar.
                        // Antes se enviaba el número y el hook buscaba MAPA_ESTRES[4] -> undefined,
                        // por eso el backend respondía "El campo 'valor' es obligatorio".
                        checked={respuestas[pregunta.id] === opcion}
                        onChange={() => seleccionarRespuesta(pregunta.id, opcion)}
                      />
                      <span>{opcion}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="questionnaire-navigation">
            <button type="button" className="btn-nav" onClick={irAnterior}>
              {pagina === 0 ? "Volver al Dashboard" : "Anterior"}
            </button>
            <div className="page-indicator">
              Página {pagina + 1} de {TOTAL_PAGINAS}
            </div>
            <button type="button" className="btn-nav btn-primary" onClick={irSiguiente}>
              {pagina === TOTAL_PAGINAS - 1 ? "Finalizar" : "Siguiente"}
            </button>
          </div>
        </section>

      </main>
    </div>
  );
}
