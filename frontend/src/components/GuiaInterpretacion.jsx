import { NIVELES } from "../utils/encuestas";
import "../styles/GuiaInterpretacion.css";

const NIVELES_RIESGO = [
  {
    clave: "SIN_RIESGO",
    texto: "No hay riesgo o es tan bajo que no hace falta ninguna acción específica de intervención.",
  },
  {
    clave: "BAJO",
    texto: "No se esperan efectos negativos. Basta con mantener y reforzar las acciones de promoción y prevención.",
  },
  {
    clave: "MEDIO",
    texto: "Se espera una respuesta de estrés moderada. Conviene observar y aplicar acciones sistemáticas para prevenir daños en la salud.",
  },
  {
    clave: "ALTO",
    texto: "Hay una probabilidad significativa de respuestas de estrés altas. Requiere intervención dentro de un sistema de vigilancia epidemiológica.",
  },
  {
    clave: "MUY_ALTO",
    texto: "Es el nivel con mayor probabilidad de respuestas de estrés muy altas. Requiere intervención inmediata dentro de un sistema de vigilancia epidemiológica.",
  },
];

const DOMINIOS_INTRALABORAL = [
  {
    nombre: "Liderazgo y relaciones sociales en el trabajo",
    texto: "Cómo es la relación con jefes, compañeros y colaboradores, y cuánta retroalimentación se recibe sobre el desempeño.",
  },
  {
    nombre: "Control sobre el trabajo",
    texto: "Margen de decisión y autonomía, claridad del rol, capacitación, participación en los cambios y oportunidades de usar y desarrollar habilidades.",
  },
  {
    nombre: "Demandas del trabajo",
    texto: "Exigencias que impone el trabajo: carga física, mental, emocional y cuantitativa, responsabilidad del cargo, jornada y su influencia en la vida fuera del trabajo.",
  },
  {
    nombre: "Recompensas",
    texto: "Reconocimiento, compensación y satisfacción por pertenecer a la organización y por el trabajo que se realiza.",
  },
];

const CUESTIONARIOS = [
  {
    nombre: "Intralaboral",
    texto: "Condiciones del trabajo y de la organización. Se organiza en dominios y dimensiones.",
  },
  {
    nombre: "Extralaboral",
    texto: "Aspectos del entorno familiar, social y económico de la persona fuera del trabajo.",
  },
  {
    nombre: "Estrés",
    texto: "Síntomas físicos, de comportamiento, intelectuales y emocionales asociados al estrés.",
  },
  {
    nombre: "Ficha de datos generales",
    texto: "Información sociodemográfica y ocupacional que permite agrupar y comparar los resultados.",
  },
];

export default function GuiaInterpretacion() {
  return (
    <div className="guia-interpretacion">
      <h3 className="guia-interpretacion__titulo">Cómo interpretar los resultados</h3>
      <p className="guia-interpretacion__intro">
        Resumen breve de los términos que aparecen en este tablero. Los resultados se muestran
        agrupados y solo cuando hay al menos 5 personas.
      </p>

      <details className="guia-interpretacion__bloque">
        <summary>Niveles de riesgo</summary>
        <div className="guia-interpretacion__contenido">
          {NIVELES_RIESGO.map(({ clave, texto }) => (
            <div className="guia-interpretacion__fila" key={clave}>
              <span
                className="guia-interpretacion__nivel"
                style={{ background: NIVELES[clave].bg, color: NIVELES[clave].text }}
              >
                {NIVELES[clave].label}
              </span>
              <p className="guia-interpretacion__texto">{texto}</p>
            </div>
          ))}
        </div>
      </details>

      <details className="guia-interpretacion__bloque">
        <summary>Dominios y dimensiones</summary>
        <div className="guia-interpretacion__contenido">
          <p className="guia-interpretacion__texto">
            Un dominio agrupa varias dimensiones, y cada dimensión reúne las preguntas que evalúan un
            aspecto específico del trabajo. En el cuestionario intralaboral, el puntaje de cada
            dimensión se lleva a una escala de 0 a 100 y se compara con los baremos del Manual para
            asignar su nivel de riesgo. La Forma A tiene 19 dimensiones y la Forma B, 16.
          </p>
          {DOMINIOS_INTRALABORAL.map(({ nombre, texto }) => (
            <p className="guia-interpretacion__texto" key={nombre}>
              <strong>{nombre}.</strong> {texto}
            </p>
          ))}
        </div>
      </details>

      <details className="guia-interpretacion__bloque">
        <summary>Qué mide cada cuestionario</summary>
        <div className="guia-interpretacion__contenido">
          {CUESTIONARIOS.map(({ nombre, texto }) => (
            <p className="guia-interpretacion__texto" key={nombre}>
              <strong>{nombre}.</strong> {texto}
            </p>
          ))}
        </div>
      </details>
    </div>
  );
}
