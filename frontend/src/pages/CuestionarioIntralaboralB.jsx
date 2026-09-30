import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCuestionarioBackend } from "../hooks/useCuestionarioBackend";
// Muestra "Cargando…" o el error cuando las respuestas no se pueden guardar
import AvisoCuestionario from "../components/AvisoCuestionario";
import "../styles/cuestionario-estres.css";

/* =========================================================
   PREGUNTAS PRINCIPALES (1-88) — Forma B

   ⚠️ NO MODIFICAR el texto, el orden ni los ids: son parte
   del instrumento oficial (Batería de Riesgo Psicosocial,
   Forma B). Los ids se usan como clave de calificación por
   dominio/dimensión; cambiarlos rompe los resultados.
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

   ⚠️ NO MODIFICAR el texto, el orden ni los ids 89-97: son
   parte del instrumento oficial (Batería de Riesgo
   Psicosocial, Forma B). Los ids se usan como clave de
   calificación; cambiarlos rompe los resultados.
========================================================= */

const ID_FILTRO_CLIENTES = "clientes";

const preguntaClientes = {
  id: ID_FILTRO_CLIENTES,
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

// ⚠️ NO MODIFICAR: escala oficial Forma B. El orden importa
// (Siempre → Nunca) porque de él depende la puntuación.
const opciones = [
  "Siempre",
  "Casi siempre",
  "Algunas veces",
  "Casi nunca",
  "Nunca",
];

const OPCIONES_SI_NO = ["Sí", "No"];

// Las respuestas se guardan en sessionStorage para no perderlas
// al recargar o al navegar a otro cuestionario. Se borran al
// cerrar la pestaña (son datos sensibles del trabajador).
const CLAVE_RESPUESTAS = "magnussing:intralaboralB:respuestas";

// Navegación entre cuestionarios de la Forma B (menú lateral y pestañas).
// Un solo lugar para las rutas: deben coincidir con App.jsx.
const NAVEGACION = [
  { clave: "estres", ruta: "/cuestionario-estresB", titulo: "Estrés", tituloPestana: "Estrés", detalle: "31 preguntas", cantidad: "31" },
  { clave: "extralaboral", ruta: "/cuestionario-extralaboralB", titulo: "Factores extralaborales", tituloPestana: "Extralaboral", detalle: "31 preguntas", cantidad: "31" },
  { clave: "intralaboral", ruta: "/cuestionario-intralaboralB", titulo: "Factores intralaborales", tituloPestana: "Intralaboral - Forma B", detalle: "Forma B · 88 a 97 preguntas", cantidad: "88-97" },
];

const CLAVE_ACTIVA = "intralaboral";

/**
 * ⚠️ NO MODIFICAR sin revisar la calificación.
 * Devuelve la lista de preguntas visibles según la respuesta a
 * la pregunta filtro "clientes". Si es "No" (o aún sin responder),
 * las 9 preguntas de atención a clientes ni se muestran ni cuentan
 * para el total.
 */
function obtenerPreguntasVisibles(respuestas) {
  const visibles = [...preguntasPrincipales, preguntaClientes];

  if (respuestas[ID_FILTRO_CLIENTES] === "Sí") {
    visibles.push(...preguntasClientes);
  }

  return visibles;
}

/**
 * ⚠️ NO MODIFICAR: evita datos corruptos en el resultado.
 * Descarta las respuestas de preguntas que ya no son visibles.
 * Caso típico: el usuario contesta "Sí", responde 89-97 y luego
 * cambia el filtro a "No". Sin esta limpieza esas 9 respuestas
 * quedarían guardadas y se enviarían/calificarían aunque el
 * trabajador dijo que no atiende clientes.
 */
function limpiarRespuestasHuerfanas(respuestas) {
  const idsVisibles = new Set(
    obtenerPreguntasVisibles(respuestas).map((p) => String(p.id))
  );

  return Object.fromEntries(
    Object.entries(respuestas).filter(([id]) => idsVisibles.has(id))
  );
}

function leerRespuestasGuardadas() {
  try {
    const guardado = JSON.parse(sessionStorage.getItem(CLAVE_RESPUESTAS));
    return guardado && typeof guardado === "object" ? guardado : {};
  } catch {
    // sessionStorage bloqueado o contenido corrupto: empezamos vacío.
    return {};
  }
}

/* =========================================================
   FILA DE PREGUNTA
   Una sola implementación para la pregunta filtro (Sí/No) y
   las preguntas Likert, para que ambas se comporten igual.
========================================================= */

function FilaPregunta({ pregunta, respuesta, sinResponder, onSeleccionar }) {
  const esFiltro = pregunta.tipo === "si_no";
  const listaOpciones = esFiltro ? OPCIONES_SI_NO : opciones;

  const clases = ["question-row"];
  if (esFiltro) clases.push("question-row-gate");
  if (sinResponder) clases.push("question-row-error");

  return (
    // El id de la fila lo usa irSiguiente() para hacer scroll a la
    // primera pregunta sin responder. No lo quites.
    <div className={clases.join(" ")} id={`fila-pregunta-${pregunta.id}`}>

      <div className="question-number">
        {esFiltro ? "?" : pregunta.id}
      </div>

      <div className="question-text">
        {esFiltro ? pregunta.texto : `${pregunta.id}. ${pregunta.texto}`}
      </div>

      {listaOpciones.map((opcion) => (
        <label className="answer-option" key={opcion}>
          <input
            type="radio"
            name={`pregunta-${pregunta.id}`}
            value={opcion}
            checked={respuesta === opcion}
            onChange={() => onSeleccionar(pregunta.id, opcion)}
          />
          <span className="custom-radio"></span>
          <small>{opcion}</small>
        </label>
      ))}

    </div>
  );
}

// Texto de la opción -> valor que se guarda en la BD.
// Escala oficial del intralaboral 0-4 (las preguntas están sembradas con valor_minimo=0 y valor_maximo=4).
// "Sí"/"No" no van aquí: la pregunta filtro de clientes la maneja useCuestionarioBackend aparte.
const MAPA_INTRALABORAL = {
  "Siempre": 4,
  "Casi siempre": 3,
  "Algunas veces": 2,
  "Casi nunca": 1,
  "Nunca": 0,
};

export default function CuestionarioIntralaboralB() {
  const navigate = useNavigate();

  const [pagina, setPagina] = useState(0);
  const [intentoFinalizar, setIntentoFinalizar] = useState(false);
  const [preguntaAEnfocar, setPreguntaAEnfocar] = useState(null);

  const {
    respuestas,
    seleccionarRespuesta: seleccionarRespuestaBackend,
    finalizarYNavegar,
    cargando, // true mientras se carga el cuestionario desde el backend
    error, // mensaje cuando no hay evaluación o falla el guardado
  } = useCuestionarioBackend("INTRALABORAL_B", MAPA_INTRALABORAL);

  const seleccionarRespuesta = (preguntaId, respuesta) => {
    seleccionarRespuestaBackend(preguntaId, respuesta);
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

  useEffect(() => {
    if (preguntaAEnfocar === null) return;

    const fila = document.getElementById(`fila-pregunta-${preguntaAEnfocar}`);
    if (fila) {
      fila.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    setPreguntaAEnfocar(null);
  }, [preguntaAEnfocar, paginaSegura]);

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

    const sinResponder = preguntasVisibles.filter(
      (p) => respuestas[p.id] === undefined
    );

    if (sinResponder.length > 0) {
      const primera = sinResponder[0];
      const indicePrimera = preguntasVisibles.indexOf(primera);

      setIntentoFinalizar(true);

      alert(
        `Te faltan ${sinResponder.length} pregunta(s) por responder. Te llevamos a la primera pregunta sin responder.`
      );

      setPagina(Math.floor(indicePrimera / PREGUNTAS_POR_PAGINA));
      setPreguntaAEnfocar(primera.id);
      return;
    }

    setIntentoFinalizar(false);
    finalizarYNavegar();
  };

  const respondidas = preguntasVisibles.filter(
    (p) => respuestas[p.id] !== undefined
  ).length;
  const progreso = Math.round((respondidas / preguntasVisibles.length) * 100);

  // Encabezado: solo cuentan las preguntas numeradas (88, o 97 con
  // clientes). La pregunta filtro no tiene número y no se cuenta.
  const numeradasPagina = preguntasPagina.filter((p) => p.tipo === "likert");
  const totalNumeradas = preguntasVisibles.filter((p) => p.tipo === "likert").length;
  const textoRango =
    numeradasPagina.length === 0
      ? "Pregunta filtro: atención a clientes"
      : `Pregunta ${numeradasPagina[0].id}–${numeradasPagina[numeradasPagina.length - 1].id} de ${totalNumeradas}`;

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

          {NAVEGACION.map((item) => (
            <button
              key={item.clave}
              className={`questionnaire-menu-item ${
                item.clave === CLAVE_ACTIVA ? "active" : ""
              }`}
              type="button"
              onClick={() => navigate(item.ruta)}
            >
              <span>▣</span>

              <div>
                <strong>{item.titulo}</strong>
                <small>{item.detalle}</small>
              </div>

            </button>
          ))}

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

          {NAVEGACION.map((item) => (
            <button
              key={item.clave}
              type="button"
              className={item.clave === CLAVE_ACTIVA ? "active" : undefined}
              onClick={() => navigate(item.ruta)}
            >
              <strong>{item.tituloPestana}</strong>
              <span>{item.cantidad}</span>
            </button>
          ))}

          {/* Este porcentaje es solo de ESTE cuestionario. */}
          <div className="general-progress">
            <span>Progreso</span>
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

              <strong>{textoRango}</strong>

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

            {preguntasPagina.map((pregunta) => (
              <FilaPregunta
                key={pregunta.id}
                pregunta={pregunta}
                respuesta={respuestas[pregunta.id]}
                sinResponder={
                  intentoFinalizar && respuestas[pregunta.id] === undefined
                }
                onSeleccionar={seleccionarRespuesta}
              />
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
