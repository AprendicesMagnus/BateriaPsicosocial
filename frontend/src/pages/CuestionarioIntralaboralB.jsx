import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/cuestionario-estres.css";

/* =========================================================
   PREGUNTAS PRINCIPALES (1-88) — Forma B
========================================================= */

const preguntasPrincipales = [
  { id: 1, tipo: "likert", texto: "El ruido en el lugar donde trabajo es molesto." },
  { id: 2, tipo: "likert", texto: "En el lugar donde trabajo hace mucho frío." },
  { id: 3, tipo: "likert", texto: "En el lugar donde trabajo hace mucho calor." },
  { id: 4, tipo: "likert", texto: "El aire en el lugar donde trabajo es fresco y agradable." },
  { id: 5, tipo: "likert", texto: "La luz del sitio donde trabajo es agradable." },
  { id: 6, tipo: "likert", texto: "El espacio donde trabajo es cómodo." },
  { id: 7, tipo: "likert", texto: "En mi trabajo me preocupa estar expuesto a sustancias químicas que afecten mi salud." },
  { id: 8, tipo: "likert", texto: "Mi trabajo me exige hacer mucho esfuerzo físico." },
  { id: 9, tipo: "likert", texto: "Los equipos o herramientas con los que trabajo son cómodos." },
  { id: 10, tipo: "likert", texto: "En mi trabajo me preocupa estar expuesto a microbios, animales o plantas que afecten mi salud." },
  { id: 11, tipo: "likert", texto: "Me preocupa accidentarme en mi trabajo." },
  { id: 12, tipo: "likert", texto: "El lugar donde trabajo es limpio y ordenado." },
  { id: 13, tipo: "likert", texto: "Por la cantidad de trabajo que tengo debo quedarme tiempo adicional." },
  { id: 14, tipo: "likert", texto: "Me alcanza el tiempo de trabajo para tener al día mis deberes." },
  { id: 15, tipo: "likert", texto: "Por la cantidad de trabajo que tengo debo trabajar sin parar." },
  { id: 16, tipo: "likert", texto: "Mi trabajo me exige hacer mucho esfuerzo mental." },
  { id: 17, tipo: "likert", texto: "Mi trabajo me exige estar muy concentrado." },
  { id: 18, tipo: "likert", texto: "Mi trabajo me exige memorizar mucha información." },
  { id: 19, tipo: "likert", texto: "En mi trabajo tengo que hacer cálculos matemáticos." },
  { id: 20, tipo: "likert", texto: "Mi trabajo requiere que me fije en pequeños detalles." },
  { id: 21, tipo: "likert", texto: "Trabajo en horario de noche." },
  { id: 22, tipo: "likert", texto: "En mi trabajo es posible tomar pausas para descansar." },
  { id: 23, tipo: "likert", texto: "Mi trabajo me exige laborar en días de descanso, festivos o fines de semana." },
  { id: 24, tipo: "likert", texto: "En mi trabajo puedo tomar fines de semana o días de descanso al mes." },
  { id: 25, tipo: "likert", texto: "Cuando estoy en casa sigo pensando en el trabajo." },
  { id: 26, tipo: "likert", texto: "Discuto con mi familia o amigos por causa de mi trabajo." },
  { id: 27, tipo: "likert", texto: "Debo atender asuntos de trabajo cuando estoy en casa." },
  { id: 28, tipo: "likert", texto: "Por mi trabajo el tiempo que paso con mi familia y amigos es muy poco." },
  { id: 29, tipo: "likert", texto: "En mi trabajo puedo hacer cosas nuevas." },
  { id: 30, tipo: "likert", texto: "Mi trabajo me permite desarrollar mis habilidades." },
  { id: 31, tipo: "likert", texto: "Mi trabajo me permite aplicar mis conocimientos." },
  { id: 32, tipo: "likert", texto: "Mi trabajo me permite aprender nuevas cosas." },
  { id: 33, tipo: "likert", texto: "Puedo tomar pausas cuando las necesito." },
  { id: 34, tipo: "likert", texto: "Puedo decidir cuánto trabajo hago en el día." },
  { id: 35, tipo: "likert", texto: "Puedo decidir la velocidad a la que trabajo." },
  { id: 36, tipo: "likert", texto: "Puedo cambiar el orden de las actividades en mi trabajo." },
  { id: 37, tipo: "likert", texto: "Puedo parar un momento mi trabajo para atender algún asunto personal." },
  { id: 38, tipo: "likert", texto: "Me explican claramente los cambios que ocurren en mi trabajo." },
  { id: 39, tipo: "likert", texto: "Puedo dar sugerencias sobre los cambios que ocurren en mi trabajo." },
  { id: 40, tipo: "likert", texto: "Cuando se presentan cambios en mi trabajo se tienen en cuenta mis ideas y sugerencias." },
  { id: 41, tipo: "likert", texto: "Me informan con claridad cuáles son mis funciones." },
  { id: 42, tipo: "likert", texto: "Me informan cuáles son las decisiones que puedo tomar en mi trabajo." },
  { id: 43, tipo: "likert", texto: "Me explican claramente los resultados que debo lograr en mi trabajo." },
  { id: 44, tipo: "likert", texto: "Me explican claramente los objetivos de mi trabajo." },
  { id: 45, tipo: "likert", texto: "Me informan claramente con quien puedo resolver los asuntos de trabajo." },
  { id: 46, tipo: "likert", texto: "La empresa me permite asistir a capacitaciones relacionadas con mi trabajo." },
  { id: 47, tipo: "likert", texto: "Recibo capacitación útil para hacer mi trabajo." },
  { id: 48, tipo: "likert", texto: "Recibo capacitación que me ayuda a hacer mejor mi trabajo." },
  { id: 49, tipo: "likert", texto: "Mi jefe ayuda a organizar mejor el trabajo." },
  { id: 50, tipo: "likert", texto: "Mi jefe tiene en cuenta mis puntos de vista y opiniones." },
  { id: 51, tipo: "likert", texto: "Mi jefe me anima para hacer mejor mi trabajo." },
  { id: 52, tipo: "likert", texto: "Mi jefe distribuye las tareas de forma que me facilita el trabajo." },
  { id: 53, tipo: "likert", texto: "Mi jefe me comunica a tiempo la información relacionada con el trabajo." },
  { id: 54, tipo: "likert", texto: "La orientación que me da mi jefe me ayuda a hacer mejor el trabajo." },
  { id: 55, tipo: "likert", texto: "Mi jefe me ayuda a progresar en el trabajo." },
  { id: 56, tipo: "likert", texto: "Mi jefe me ayuda a sentirme bien en el trabajo." },
  { id: 57, tipo: "likert", texto: "Mi jefe ayuda a solucionar los problemas que se presentan en el trabajo." },
  { id: 58, tipo: "likert", texto: "Mi jefe me trata con respeto." },
  { id: 59, tipo: "likert", texto: "Siento que puedo confiar en mi jefe." },
  { id: 60, tipo: "likert", texto: "Mi jefe me escucha cuando tengo problemas de trabajo." },
  { id: 61, tipo: "likert", texto: "Mi jefe me brinda su apoyo cuando lo necesito." },
  { id: 62, tipo: "likert", texto: "Me agrada el ambiente de mi grupo de trabajo." },
  { id: 63, tipo: "likert", texto: "En mi grupo de trabajo me tratan de forma respetuosa." },
  { id: 64, tipo: "likert", texto: "Siento que puedo confiar en mis compañeros de trabajo." },
  { id: 65, tipo: "likert", texto: "Me siento a gusto con mis compañeros de trabajo." },
  { id: 66, tipo: "likert", texto: "En mi grupo de trabajo algunas personas me maltratan." },
  { id: 67, tipo: "likert", texto: "Entre compañeros solucionamos los problemas de forma respetuosa." },
  { id: 68, tipo: "likert", texto: "Mi grupo de trabajo es muy unido." },
  { id: 69, tipo: "likert", texto: "Cuando tenemos que realizar trabajo de grupo los compañeros colaboran." },
  { id: 70, tipo: "likert", texto: "Es fácil poner de acuerdo al grupo para hacer el trabajo." },
  { id: 71, tipo: "likert", texto: "Mis compañeros de trabajo me ayudan cuando tengo dificultades." },
  { id: 72, tipo: "likert", texto: "En mi trabajo las personas nos apoyamos unos a otros." },
  { id: 73, tipo: "likert", texto: "Algunos compañeros de trabajo me escuchan cuando tengo problemas." },
  { id: 74, tipo: "likert", texto: "Me informan sobre lo que hago bien en mi trabajo." },
  { id: 75, tipo: "likert", texto: "Me informan sobre lo que debo mejorar en mi trabajo." },
  { id: 76, tipo: "likert", texto: "La información que recibo sobre mi rendimiento en el trabajo es clara." },
  { id: 77, tipo: "likert", texto: "La forma como evalúan mi trabajo en la empresa me ayuda a mejorar." },
  { id: 78, tipo: "likert", texto: "Me informan a tiempo sobre lo que debo mejorar en el trabajo." },
  { id: 79, tipo: "likert", texto: "En la empresa me pagan a tiempo mi salario." },
  { id: 80, tipo: "likert", texto: "El pago que recibo es el que me ofreció la empresa." },
  { id: 81, tipo: "likert", texto: "El pago que recibo es el que merezco por el trabajo que realizo." },
  { id: 82, tipo: "likert", texto: "En mi trabajo tengo posibilidades de progresar." },
  { id: 83, tipo: "likert", texto: "Las personas que hacen bien el trabajo pueden progresar en la empresa." },
  { id: 84, tipo: "likert", texto: "La empresa se preocupa por el bienestar de los trabajadores." },
  { id: 85, tipo: "likert", texto: "Mi trabajo en la empresa es estable." },
  { id: 86, tipo: "likert", texto: "El trabajo que hago me hace sentir bien." },
  { id: 87, tipo: "likert", texto: "Siento orgullo de trabajar en esta empresa." },
  { id: 88, tipo: "likert", texto: "Hablo bien de la empresa con otras personas." },
];

/* =========================================================
   BLOQUE CONDICIONAL: ATENCIÓN A CLIENTES (89-97)
   Solo se muestra si la pregunta filtro "clientes" = "Sí".
   (La Forma B no tiene bloque de jefatura, a diferencia de
   la Forma A.)
========================================================= */

const preguntaClientes = {
  id: "clientes",
  tipo: "si_no",
  texto: "En mi trabajo debo brindar servicio a clientes o usuarios:",
};

const preguntasClientes = [
  { id: 89, tipo: "likert", texto: "Atiendo clientes o usuarios muy enojados." },
  { id: 90, tipo: "likert", texto: "Atiendo clientes o usuarios muy preocupados." },
  { id: 91, tipo: "likert", texto: "Atiendo clientes o usuarios muy tristes." },
  { id: 92, tipo: "likert", texto: "Mi trabajo me exige atender personas muy enfermas." },
  { id: 93, tipo: "likert", texto: "Mi trabajo me exige atender personas muy necesitadas de ayuda." },
  { id: 94, tipo: "likert", texto: "Atiendo clientes o usuarios que me maltratan." },
  { id: 95, tipo: "likert", texto: "Mi trabajo me exige atender situaciones de violencia." },
  { id: 96, tipo: "likert", texto: "Mi trabajo me exige atender situaciones muy tristes o dolorosas." },
  { id: 97, tipo: "likert", texto: "Puedo expresar tristeza o enojo frente a las personas que atiendo." },
];

const PREGUNTAS_POR_PAGINA = 8;

const opciones = [
  "Siempre",
  "Casi siempre",
  "Algunas veces",
  "Casi nunca",
  "Nunca",
];

/**
 * Devuelve la lista de preguntas visibles según la respuesta a
 * la pregunta filtro "clientes". Si es "No", las 9 preguntas de
 * atención a clientes ni se muestran ni cuentan para el total.
 */
function obtenerPreguntasVisibles(respuestas) {
  const visibles = [...preguntasPrincipales, preguntaClientes];

  if (respuestas[preguntaClientes.id] === "Sí") {
    visibles.push(...preguntasClientes);
  }

  return visibles;
}

export default function CuestionarioIntralaboralB() {

  const navigate = useNavigate();

  const [respuestas, setRespuestas] = useState({});
  const [pagina, setPagina] = useState(0);
  const [intentoFinalizar, setIntentoFinalizar] = useState(false);

  const seleccionarRespuesta = (preguntaId, respuesta) => {
    setRespuestas({
      ...respuestas,
      [preguntaId]: respuesta,
    });
  };

  const preguntasVisibles = obtenerPreguntasVisibles(respuestas);
  const totalPaginas = Math.max(
    1,
    Math.ceil(preguntasVisibles.length / PREGUNTAS_POR_PAGINA)
  );
  const paginaSegura = Math.min(pagina, totalPaginas - 1);

  const inicio = paginaSegura * PREGUNTAS_POR_PAGINA;
  const fin = Math.min(inicio + PREGUNTAS_POR_PAGINA, preguntasVisibles.length);
  const preguntasPagina = preguntasVisibles.slice(inicio, fin);

  const irAnterior = () => {
    if (paginaSegura === 0) {
      navigate("/dashboard");
      return;
    }
    setPagina(paginaSegura - 1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const irSiguiente = () => {
    if (paginaSegura < totalPaginas - 1) {
      setPagina(paginaSegura + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    const preguntaSinResponder = preguntasVisibles.find(
      (p) => respuestas[p.id] === undefined
    );

    if (preguntaSinResponder) {
      const faltantes = preguntasVisibles.filter(
        (p) => respuestas[p.id] === undefined
      ).length;

      const indiceFaltante = preguntasVisibles.indexOf(preguntaSinResponder);
      const paginaFaltante = Math.floor(indiceFaltante / PREGUNTAS_POR_PAGINA);

      setIntentoFinalizar(true);

      alert(
        `Te faltan ${faltantes} pregunta(s) por responder. Te llevamos a la primera pregunta sin responder.`
      );

      setPagina(paginaFaltante);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    alert("Las respuestas han sido guardadas correctamente.");
  };

  const respondidas = preguntasVisibles.filter(
    (p) => respuestas[p.id] !== undefined
  ).length;
  const progreso = Math.round((respondidas / preguntasVisibles.length) * 100);

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
            className="questionnaire-menu-item"
            type="button"
            onClick={() => navigate("/cuestionario-estresB")}
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
            onClick={() => navigate("/cuestionario-extralaboralB")}
          >
            <span>▣</span>

            <div>
              <strong>Factores extralaborales</strong>
              <small>31 preguntas</small>
            </div>

          </button>


          <button
            className="questionnaire-menu-item active"
            type="button"
            onClick={() => navigate("/cuestionario-intralaboralB")}
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
              Cuestionario de Factores de Riesgo Psicosocial Intralaboral · Forma B
            </h2>

            <p>
              Las siguientes preguntas están relacionadas con las condiciones de
              su trabajo. Señale la frecuencia con que se presenta cada situación.
            </p>

          </div>

        </section>



        {/* =================================================
            PESTAÑAS
        ================================================= */}

        <div className="questionnaire-tabs">

          <button
            type="button"

            onClick={() => navigate("/cuestionario-estres")}

            onClick={() => navigate("/cuestionario-estresB")}
          >
            <strong>Estrés</strong>
            <span>31</span>
          </button>

          <button
            type="button"

            onClick={() => navigate("/cuestionario-extralaboral")}
            onClick={() => navigate("/cuestionario-extralaboralB")}
          >
            <strong>Extralaboral</strong>
            <span>31</span>
          </button>

          <button
            type="button"
            className="active"
            onClick={() => navigate("/cuestionario-intralaboral-b")}
            onClick={() => navigate("/cuestionario-intralaboralB")}
          >
            <strong>Intralaboral - Forma B</strong>
            <span>88</span>
          </button>

          <div className="general-progress">
            <span>Progreso general</span>
            <div className="general-progress-bar">
              <div style={{ width: `${progreso}%` }}></div>
            </div>
            <small>{progreso}%</small>
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
                Pregunta {inicio + 1}–{fin} de {preguntasVisibles.length}
              </strong>

              <div className="questions-progress">
                <div style={{ width: `${progreso}%` }}></div>
              </div>

            </div>

            <span>
              Sección: Intralaboral
            </span>

          </div>



          {/* ENCABEZADO DE OPCIONES */}

          <div className="answers-header">

            <span>
              Frecuencia:
            </span>

            {opciones.map((opcion) => (
              <span key={opcion}>{opcion}</span>
            ))}

          </div>



          {/* PREGUNTAS */}

          <div className="questions-list">

            {preguntasPagina.map((pregunta) => {

              const sinResponder =
                intentoFinalizar && respuestas[pregunta.id] === undefined;

              if (pregunta.tipo === "si_no") {
                return (
                  <div
                    className={`question-row question-row-gate ${
                      sinResponder ? "question-row-error" : ""
                    }`}
                    key={pregunta.id}
                  >

                    <div className="question-number">?</div>

                    <div className="question-text">
                      {pregunta.texto}
                    </div>

                    {["Sí", "No"].map((opcion) => (
                      <label className="answer-option" key={opcion}>
                        <input
                          type="radio"
                          name={`pregunta-${pregunta.id}`}
                          value={opcion}
                          checked={respuestas[pregunta.id] === opcion}
                          onChange={() =>
                            seleccionarRespuesta(pregunta.id, opcion)
                          }
                        />
                        <span className="custom-radio"></span>
                        <small>{opcion}</small>
                      </label>
                    ))}

                  </div>
                );
              }

              return (
                <div
                  className={`question-row ${
                    sinResponder ? "question-row-error" : ""
                  }`}
                  key={pregunta.id}
                >

                  <div className="question-number">
                    {pregunta.id}
                  </div>

                  <div className="question-text">
                    {pregunta.id}. {pregunta.texto}
                  </div>

                  {opciones.map((opcion) => (
                    <label className="answer-option" key={opcion}>
                      <input
                        type="radio"
                        name={`pregunta-${pregunta.id}`}
                        value={opcion}
                        checked={respuestas[pregunta.id] === opcion}
                        onChange={() =>
                          seleccionarRespuesta(pregunta.id, opcion)
                        }
                      />
                      <span className="custom-radio"></span>
                      <small>{opcion}</small>
                    </label>
                  ))}

                </div>
              );

            })}

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
              Página {paginaSegura + 1} de {totalPaginas}
            </span>

            <button
              className="next-button"
              type="button"
              onClick={irSiguiente}
            >
              {paginaSegura < totalPaginas - 1 ? "Siguiente →" : "Finalizar"}
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}