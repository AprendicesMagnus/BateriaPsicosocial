import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../styles/cuestionario-estres.css";
import "../styles/Fichadatosgenerales.css";

// =======================================================
// OPCIONES DE CADA PREGUNTA
// =======================================================

const OPCIONES_SEXO = ["Masculino", "Femenino"];

const OPCIONES_ESTADO_CIVIL = [
  "Soltero (a)",
  "Casado (a)",
  "Unión libre",
  "Separado (a)",
  "Divorciado (a)",
  "Viudo (a)",
  "Sacerdote / Monja",
];

const OPCIONES_ESTUDIOS = [
  "Ninguno",
  "Primaria incompleta",
  "Primaria completa",
  "Bachillerato incompleto",
  "Bachillerato completo",
  "Técnico / tecnológico incompleto",
  "Técnico / tecnológico completo",
  "Profesional incompleto",
  "Profesional completo",
  "Carrera militar / policía",
  "Post-grado incompleto",
  "Post-grado completo",
];

const OPCIONES_ESTRATO = ["1", "2", "3", "4", "5", "6", "Finca", "No sé"];

const OPCIONES_VIVIENDA = ["Propia", "En arriendo", "Familiar"];

const OPCIONES_TIPO_CARGO = [
  "Jefatura - tiene personal a cargo",
  "Profesional, analista, técnico, tecnólogo",
  "Auxiliar, asistente administrativo, asistente técnico",
  "Operario, operador, ayudante, servicios generales",
];

const OPCIONES_CONTRATO = [
  "Temporal de menos de 1 año",
  "Temporal de 1 año o más",
  "Término indefinido",
  "Cooperado (cooperativa)",
  "Prestación de servicios",
  "No sé",
];

const OPCIONES_SALARIO = [
  "Fijo (diario, semanal, quincenal o mensual)",
  "Una parte fija y otra variable",
  "Todo variable (a destajo, por producción, por comisión)",
];

// Preguntas obligatorias mínimas para validar antes de guardar
const CAMPOS_REQUERIDOS = [
  "nombreCompleto",
  "sexo",
  "anioNacimiento",
  "estadoCivil",
  "nivelEstudios",
  "ocupacion",
  "residenciaCiudad",
  "residenciaDepartamento",
  "estrato",
  "tipoVivienda",
  "personasACargo",
  "trabajoCiudad",
  "trabajoDepartamento",
  "antiguedadEmpresa",
  "nombreCargo",
  "tipoCargo",
  "antiguedadCargo",
  "areaODepartamento",
  "tipoContrato",
  "horasDiarias",
  "tipoSalario",
];

const RUTAS = {
  estres: "/cuestionario-estresB",
  extralaboral: "/cuestionario-extralaboralB",
  intralaboral: "/cuestionario-intralaboralB",
  fichaGeneral: "/ficha-datos-generales",
};

export default function FichaDatosGenerales() {
  const navigate = useNavigate();
  const location = useLocation();

  const [datos, setDatos] = useState({
    nombreCompleto: "",
    sexo: "",
    anioNacimiento: "",
    estadoCivil: "",
    nivelEstudios: "",
    ocupacion: "",
    residenciaCiudad: "",
    residenciaDepartamento: "",
    estrato: "",
    tipoVivienda: "",
    personasACargo: "",
    trabajoCiudad: "",
    trabajoDepartamento: "",
    antiguedadEmpresaMenosUnAnio: false,
    antiguedadEmpresa: "",
    nombreCargo: "",
    tipoCargo: "",
    antiguedadCargoMenosUnAnio: false,
    antiguedadCargo: "",
    areaODepartamento: "",
    tipoContrato: "",
    horasDiarias: "",
    tipoSalario: "",
  });

  const [intentoGuardar, setIntentoGuardar] = useState(false);

  const actualizarCampo = (campo, valor) => {
    setDatos((prev) => ({ ...prev, [campo]: valor }));
  };

  const esCampoInvalido = (campo) =>
    intentoGuardar &&
    CAMPOS_REQUERIDOS.includes(campo) &&
    (datos[campo] === "" || datos[campo] === undefined);

  const guardar = () => {
    const faltantes = CAMPOS_REQUERIDOS.filter(
      (campo) => datos[campo] === "" || datos[campo] === undefined
    );

    if (faltantes.length > 0) {
      setIntentoGuardar(true);
      alert(
        `Te faltan ${faltantes.length} campo(s) por completar. Revisa los campos resaltados en rojo.`
      );
      return;
    }

    setIntentoGuardar(false);
    alert("Los datos generales han sido guardados correctamente.");
    // Aquí puedes reemplazar el alert por tu llamada a la API / navegación
    // navigate("/cuestionario-estresB");
  };

  const irAnterior = () => {
    navigate("/dashboard");
  };

  const camposRespondidos = CAMPOS_REQUERIDOS.filter(
    (campo) => datos[campo] !== "" && datos[campo] !== undefined
  ).length;

  const progreso = Math.round(
    (camposRespondidos / CAMPOS_REQUERIDOS.length) * 100
  );

  return (
    <div className="questionnaire-page">
      {/* =====================================================
          MENÚ LATERAL
      ===================================================== */}

      <aside className="questionnaire-sidebar">
        <div className="questionnaire-logo">
          <div>
            <img
              src="/logob1.png"
              alt="Magnus"
              style={{ height: 70, marginRight: "auto" }}
            />
          </div>
        </div>

        <nav className="questionnaire-menu">
          <button
            className={`questionnaire-menu-item ${
              location.pathname === RUTAS.fichaGeneral ? "active" : ""
            }`}
            type="button"
            onClick={() => navigate(RUTAS.fichaGeneral)}
          >
            <span>▣</span>
            <div>
              <strong>Datos generales</strong>
              <small>19 preguntas</small>
            </div>
          </button>

          
        </nav>

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
        <section className="questionnaire-intro">
          <div className="questionnaire-heart">♥</div>

          <div>
            <h2>Ficha de Datos Generales</h2>
            <p>
              Por favor responda todas las preguntas con información veraz.
              Estos datos son confidenciales y se usan únicamente para fines
              estadísticos.
            </p>
          </div>
        </section>

        <div className="questionnaire-tabs">
          <button
            type="button"
            className={location.pathname === RUTAS.fichaGeneral ? "active" : ""}
            onClick={() => navigate(RUTAS.fichaGeneral)}
          >
            <strong>Datos generales</strong>
            <span>19</span>
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
            FORMULARIO
        ================================================= */}

        <section className="ficha-card">
          <div className="ficha-header">
            <strong>Datos generales</strong>
            <span>{camposRespondidos} / {CAMPOS_REQUERIDOS.length} completados</span>
          </div>

          <div className="ficha-form">
            {/* 1. Nombre completo */}
            <div className={`ficha-field ${esCampoInvalido("nombreCompleto") ? "ficha-field-error" : ""}`}>
              <label>1. Nombre completo</label>
              <input
                type="text"
                value={datos.nombreCompleto}
                onChange={(e) => actualizarCampo("nombreCompleto", e.target.value)}
                placeholder="Escriba su nombre completo"
              />
            </div>

            {/* 2. Sexo */}
            <div className={`ficha-field ${esCampoInvalido("sexo") ? "ficha-field-error" : ""}`}>
              <label>2. Sexo</label>
              <div className="ficha-opciones">
                {OPCIONES_SEXO.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="sexo"
                      checked={datos.sexo === op}
                      onChange={() => actualizarCampo("sexo", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 3. Año de nacimiento */}
            <div className={`ficha-field ${esCampoInvalido("anioNacimiento") ? "ficha-field-error" : ""}`}>
              <label>3. Año de nacimiento</label>
              <input
                type="number"
                value={datos.anioNacimiento}
                onChange={(e) => actualizarCampo("anioNacimiento", e.target.value)}
                placeholder="Ej: 1990"
                min="1930"
                max={new Date().getFullYear()}
              />
            </div>

            {/* 4. Estado civil */}
            <div className={`ficha-field ${esCampoInvalido("estadoCivil") ? "ficha-field-error" : ""}`}>
              <label>4. Estado civil</label>
              <div className="ficha-opciones ficha-opciones-wrap">
                {OPCIONES_ESTADO_CIVIL.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="estadoCivil"
                      checked={datos.estadoCivil === op}
                      onChange={() => actualizarCampo("estadoCivil", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 5. Nivel de estudios */}
            <div className={`ficha-field ${esCampoInvalido("nivelEstudios") ? "ficha-field-error" : ""}`}>
              <label>5. Último nivel de estudios que alcanzó</label>
              <div className="ficha-opciones ficha-opciones-wrap">
                {OPCIONES_ESTUDIOS.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="nivelEstudios"
                      checked={datos.nivelEstudios === op}
                      onChange={() => actualizarCampo("nivelEstudios", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 6. Ocupación */}
            <div className={`ficha-field ${esCampoInvalido("ocupacion") ? "ficha-field-error" : ""}`}>
              <label>6. ¿Cuál es su ocupación o profesión?</label>
              <input
                type="text"
                value={datos.ocupacion}
                onChange={(e) => actualizarCampo("ocupacion", e.target.value)}
                placeholder="Escriba su ocupación o profesión"
              />
            </div>

            {/* 7. Lugar de residencia */}
            <div className="ficha-field-group">
              <label className="ficha-field-group-label">7. Lugar de residencia actual</label>
              <div className="ficha-field-row">
                <div className={`ficha-field ${esCampoInvalido("residenciaCiudad") ? "ficha-field-error" : ""}`}>
                  <label>Ciudad / municipio</label>
                  <input
                    type="text"
                    value={datos.residenciaCiudad}
                    onChange={(e) => actualizarCampo("residenciaCiudad", e.target.value)}
                  />
                </div>
                <div className={`ficha-field ${esCampoInvalido("residenciaDepartamento") ? "ficha-field-error" : ""}`}>
                  <label>Departamento</label>
                  <input
                    type="text"
                    value={datos.residenciaDepartamento}
                    onChange={(e) => actualizarCampo("residenciaDepartamento", e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* 8. Estrato */}
            <div className={`ficha-field ${esCampoInvalido("estrato") ? "ficha-field-error" : ""}`}>
              <label>8. Estrato de los servicios públicos de su vivienda</label>
              <div className="ficha-opciones">
                {OPCIONES_ESTRATO.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="estrato"
                      checked={datos.estrato === op}
                      onChange={() => actualizarCampo("estrato", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 9. Tipo de vivienda */}
            <div className={`ficha-field ${esCampoInvalido("tipoVivienda") ? "ficha-field-error" : ""}`}>
              <label>9. Tipo de vivienda</label>
              <div className="ficha-opciones">
                {OPCIONES_VIVIENDA.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="tipoVivienda"
                      checked={datos.tipoVivienda === op}
                      onChange={() => actualizarCampo("tipoVivienda", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 10. Personas a cargo */}
            <div className={`ficha-field ${esCampoInvalido("personasACargo") ? "ficha-field-error" : ""}`}>
              <label>10. Número de personas que dependen económicamente de usted</label>
              <input
                type="number"
                min="0"
                value={datos.personasACargo}
                onChange={(e) => actualizarCampo("personasACargo", e.target.value)}
              />
            </div>

            {/* 11. Lugar donde trabaja */}
            <div className="ficha-field-group">
              <label className="ficha-field-group-label">11. Lugar donde trabaja actualmente</label>
              <div className="ficha-field-row">
                <div className={`ficha-field ${esCampoInvalido("trabajoCiudad") ? "ficha-field-error" : ""}`}>
                  <label>Ciudad / municipio</label>
                  <input
                    type="text"
                    value={datos.trabajoCiudad}
                    onChange={(e) => actualizarCampo("trabajoCiudad", e.target.value)}
                  />
                </div>
                <div className={`ficha-field ${esCampoInvalido("trabajoDepartamento") ? "ficha-field-error" : ""}`}>
                  <label>Departamento</label>
                  <input
                    type="text"
                    value={datos.trabajoDepartamento}
                    onChange={(e) => actualizarCampo("trabajoDepartamento", e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* 12. Antigüedad en la empresa */}
            <div className={`ficha-field ${esCampoInvalido("antiguedadEmpresa") ? "ficha-field-error" : ""}`}>
              <label>12. ¿Hace cuántos años que trabaja en esta empresa?</label>
              <div className="ficha-antiguedad">
                <label className="ficha-opcion">
                  <input
                    type="checkbox"
                    checked={datos.antiguedadEmpresaMenosUnAnio}
                    onChange={(e) => {
                      actualizarCampo("antiguedadEmpresaMenosUnAnio", e.target.checked);
                      if (e.target.checked) actualizarCampo("antiguedadEmpresa", "menos de 1 año");
                      else actualizarCampo("antiguedadEmpresa", "");
                    }}
                  />
                  <span>Menos de un año</span>
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="Años (si lleva más de 1)"
                  disabled={datos.antiguedadEmpresaMenosUnAnio}
                  value={datos.antiguedadEmpresaMenosUnAnio ? "" : datos.antiguedadEmpresa}
                  onChange={(e) => actualizarCampo("antiguedadEmpresa", e.target.value)}
                />
              </div>
            </div>

            {/* 13. Nombre del cargo */}
            <div className={`ficha-field ${esCampoInvalido("nombreCargo") ? "ficha-field-error" : ""}`}>
              <label>13. ¿Cuál es el nombre del cargo que ocupa en la empresa?</label>
              <input
                type="text"
                value={datos.nombreCargo}
                onChange={(e) => actualizarCampo("nombreCargo", e.target.value)}
              />
            </div>

            {/* 14. Tipo de cargo */}
            <div className={`ficha-field ${esCampoInvalido("tipoCargo") ? "ficha-field-error" : ""}`}>
              <label>14. Seleccione el tipo de cargo que más se parece al que usted desempeña</label>
              <div className="ficha-opciones ficha-opciones-wrap">
                {OPCIONES_TIPO_CARGO.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="tipoCargo"
                      checked={datos.tipoCargo === op}
                      onChange={() => actualizarCampo("tipoCargo", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 15. Antigüedad en el cargo */}
            <div className={`ficha-field ${esCampoInvalido("antiguedadCargo") ? "ficha-field-error" : ""}`}>
              <label>15. ¿Hace cuántos años que desempeña el cargo u oficio actual en esta empresa?</label>
              <div className="ficha-antiguedad">
                <label className="ficha-opcion">
                  <input
                    type="checkbox"
                    checked={datos.antiguedadCargoMenosUnAnio}
                    onChange={(e) => {
                      actualizarCampo("antiguedadCargoMenosUnAnio", e.target.checked);
                      if (e.target.checked) actualizarCampo("antiguedadCargo", "menos de 1 año");
                      else actualizarCampo("antiguedadCargo", "");
                    }}
                  />
                  <span>Menos de un año</span>
                </label>
                <input
                  type="number"
                  min="1"
                  placeholder="Años (si lleva más de 1)"
                  disabled={datos.antiguedadCargoMenosUnAnio}
                  value={datos.antiguedadCargoMenosUnAnio ? "" : datos.antiguedadCargo}
                  onChange={(e) => actualizarCampo("antiguedadCargo", e.target.value)}
                />
              </div>
            </div>

            {/* 16. Área / departamento de la empresa */}
            <div className={`ficha-field ${esCampoInvalido("areaODepartamento") ? "ficha-field-error" : ""}`}>
              <label>16. Nombre del departamento, área o sección de la empresa en el que trabaja</label>
              <input
                type="text"
                value={datos.areaODepartamento}
                onChange={(e) => actualizarCampo("areaODepartamento", e.target.value)}
              />
            </div>

            {/* 17. Tipo de contrato */}
            <div className={`ficha-field ${esCampoInvalido("tipoContrato") ? "ficha-field-error" : ""}`}>
              <label>17. Seleccione el tipo de contrato que tiene actualmente</label>
              <div className="ficha-opciones ficha-opciones-wrap">
                {OPCIONES_CONTRATO.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="tipoContrato"
                      checked={datos.tipoContrato === op}
                      onChange={() => actualizarCampo("tipoContrato", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* 18. Horas diarias */}
            <div className={`ficha-field ${esCampoInvalido("horasDiarias") ? "ficha-field-error" : ""}`}>
              <label>18. Horas diarias de trabajo establecidas habitualmente por la empresa</label>
              <input
                type="number"
                min="0"
                max="24"
                value={datos.horasDiarias}
                onChange={(e) => actualizarCampo("horasDiarias", e.target.value)}
                placeholder="Horas de trabajo al día"
              />
            </div>

            {/* 19. Tipo de salario */}
            <div className={`ficha-field ${esCampoInvalido("tipoSalario") ? "ficha-field-error" : ""}`}>
              <label>19. Seleccione el tipo de salario que recibe</label>
              <div className="ficha-opciones ficha-opciones-wrap">
                {OPCIONES_SALARIO.map((op) => (
                  <label className="ficha-opcion" key={op}>
                    <input
                      type="radio"
                      name="tipoSalario"
                      checked={datos.tipoSalario === op}
                      onChange={() => actualizarCampo("tipoSalario", op)}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* BOTONES */}
          <div className="questionnaire-navigation">
            <button className="previous-button" type="button" onClick={irAnterior}>
              ← Anterior
            </button>

            <button className="next-button" type="button" onClick={guardar}>
              Guardar y continuar →
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}