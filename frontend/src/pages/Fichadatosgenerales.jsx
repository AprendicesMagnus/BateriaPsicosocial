import { useState, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../styles/cuestionario-estres.css";
import "../styles/Fichadatosgenerales.css";
import {
  nombrePersonaValido,
  lugarValido,
  textoLibreValido,
  enteroEnRango,
  filtrarNombrePersona,
  filtrarLugar,
  filtrarTextoLibre,
  soloDigitos,
} from "../utils/validaciones";

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


const RUTAS_A = {
  estres: "/cuestionario-estres",
  extralaboral: "/cuestionario-extralaboral",
  intralaboral: "/cuestionario-intralaboral",
  fichaGeneral: "/ficha-datos-generales",
};

const RUTAS_B = {
  estres: "/cuestionario-estresB",
  extralaboral: "/cuestionario-extralaboralB",
  intralaboral: "/cuestionario-intralaboralB",
  fichaGeneral: "/ficha-datos-generalesB",

};

export default function FichaDatosGenerales() {
  const navigate = useNavigate();
  const location = useLocation();


  const RUTAS = location.pathname === RUTAS_B.fichaGeneral ? RUTAS_B : RUTAS_A;


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
  const [tocados, setTocados] = useState({});

  const actualizarCampo = (campo, valor) => {
    setDatos((prev) => ({ ...prev, [campo]: valor }));
  };

  const marcarTocado = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = useMemo(() => {
    const errs = {};
    const currentYear = new Date().getFullYear();
    const minAnio = currentYear - 100;
    const maxAnio = currentYear - 15;

    // 1. Nombre completo
    if (!datos.nombreCompleto.trim()) {
      errs.nombreCompleto = "Ingresa tu nombre completo.";
    } else if (!nombrePersonaValido(datos.nombreCompleto)) {
      errs.nombreCompleto = "Ingresa un nombre completo válido (solo letras, mín. 2 letras).";
    }

    // 2. Sexo
    if (!datos.sexo) {
      errs.sexo = "Selecciona una opción.";
    }

    // 3. Año de nacimiento
    if (!datos.anioNacimiento.trim()) {
      errs.anioNacimiento = "Ingresa el año de nacimiento.";
    } else if (!enteroEnRango(datos.anioNacimiento, minAnio, maxAnio)) {
      errs.anioNacimiento = `El año de nacimiento debe estar entre ${minAnio} y ${maxAnio}.`;
    }

    // 4. Estado civil
    if (!datos.estadoCivil) {
      errs.estadoCivil = "Selecciona una opción.";
    }

    // 5. Nivel de estudios
    if (!datos.nivelEstudios) {
      errs.nivelEstudios = "Selecciona una opción.";
    }

    // 6. Ocupación
    if (!datos.ocupacion.trim()) {
      errs.ocupacion = "Ingresa tu ocupación.";
    } else if (!textoLibreValido(datos.ocupacion, 100)) {
      errs.ocupacion = "Ingresa una ocupación válida.";
    }

    // 7. Residencia ciudad / departamento
    if (!datos.residenciaCiudad.trim()) {
      errs.residenciaCiudad = "Ingresa la ciudad de residencia.";
    } else if (!lugarValido(datos.residenciaCiudad)) {
      errs.residenciaCiudad = "Ingresa una ciudad válida.";
    }

    if (!datos.residenciaDepartamento.trim()) {
      errs.residenciaDepartamento = "Ingresa el departamento de residencia.";
    } else if (!lugarValido(datos.residenciaDepartamento)) {
      errs.residenciaDepartamento = "Ingresa un departamento válido.";
    }

    // 8. Estrato
    if (!datos.estrato) {
      errs.estrato = "Selecciona una opción.";
    }

    // 9. Tipo de vivienda
    if (!datos.tipoVivienda) {
      errs.tipoVivienda = "Selecciona una opción.";
    }

    // 10. Personas a cargo
    if (datos.personasACargo === "" || datos.personasACargo === undefined) {
      errs.personasACargo = "Ingresa el número de personas a cargo.";
    } else if (!enteroEnRango(datos.personasACargo, 0, 30)) {
      errs.personasACargo = "El número de personas a cargo debe estar entre 0 y 30.";
    }

    // 11. Trabajo ciudad / departamento
    if (!datos.trabajoCiudad.trim()) {
      errs.trabajoCiudad = "Ingresa la ciudad de trabajo.";
    } else if (!lugarValido(datos.trabajoCiudad)) {
      errs.trabajoCiudad = "Ingresa una ciudad válida.";
    }

    if (!datos.trabajoDepartamento.trim()) {
      errs.trabajoDepartamento = "Ingresa el departamento de trabajo.";
    } else if (!lugarValido(datos.trabajoDepartamento)) {
      errs.trabajoDepartamento = "Ingresa un departamento válido.";
    }

    // 12. Antigüedad en la empresa
    if (!datos.antiguedadEmpresaMenosUnAnio) {
      if (!datos.antiguedadEmpresa.trim()) {
        errs.antiguedadEmpresa = "Ingresa los años o marca 'Menos de un año'.";
      } else if (!enteroEnRango(datos.antiguedadEmpresa, 1, 60)) {
        errs.antiguedadEmpresa = "La antigüedad en la empresa debe estar entre 1 y 60 años.";
      }
    }

    // 13. Nombre del cargo
    if (!datos.nombreCargo.trim()) {
      errs.nombreCargo = "Ingresa el nombre del cargo.";
    } else if (!textoLibreValido(datos.nombreCargo, 100)) {
      errs.nombreCargo = "Ingresa un nombre de cargo válido.";
    }

    // 14. Tipo de cargo
    if (!datos.tipoCargo) {
      errs.tipoCargo = "Selecciona una opción.";
    }

    // 15. Antigüedad en el cargo
    if (!datos.antiguedadCargoMenosUnAnio) {
      if (!datos.antiguedadCargo.trim()) {
        errs.antiguedadCargo = "Ingresa los años o marca 'Menos de un año'.";
      } else if (!enteroEnRango(datos.antiguedadCargo, 1, 60)) {
        errs.antiguedadCargo = "La antigüedad en el cargo debe estar entre 1 y 60 años.";
      }
    }

    // 16. Área o departamento
    if (!datos.areaODepartamento.trim()) {
      errs.areaODepartamento = "Ingresa el área o departamento.";
    } else if (!textoLibreValido(datos.areaODepartamento, 100)) {
      errs.areaODepartamento = "Ingresa un área o departamento válido.";
    }

    // 17. Tipo de contrato
    if (!datos.tipoContrato) {
      errs.tipoContrato = "Selecciona una opción.";
    }

    // 18. Horas diarias
    if (!datos.horasDiarias.trim()) {
      errs.horasDiarias = "Ingresa las horas diarias de trabajo.";
    } else if (!enteroEnRango(datos.horasDiarias, 1, 24)) {
      errs.horasDiarias = "Las horas diarias de trabajo deben estar entre 1 y 24.";
    }

    // 19. Tipo de salario
    if (!datos.tipoSalario) {
      errs.tipoSalario = "Selecciona una opción.";
    }

    return errs;
  }, [datos]);

  const esCampoInvalido = (campo) => {
    return !!(errores[campo] && (intentoGuardar || tocados[campo]));
  };

  const guardar = (e) => {
    if (e) e.preventDefault();
    setIntentoGuardar(true);

    if (Object.keys(errores).length > 0) {
      setTimeout(() => {
        const primInvalido = document.querySelector(
          ".field__input--invalid, .ficha-field-error input, .ficha-field-error"
        );
        if (primInvalido && typeof primInvalido.focus === "function") {
          primInvalido.focus();
        }
      }, 0);

      return;
    }

    setIntentoGuardar(false);
    alert("Los datos generales han sido guardados correctamente.");
    // Aquí puedes reemplazar el alert por tu llamada a la API / navegación
    // navigate("/cuestionario-estresB");
    navigate(RUTAS.estres);
  };

  const irAnterior = () => {
    navigate("/dashboard");
  };

const camposRespondidos = CAMPOS_REQUERIDOS.filter(
  (campo) =>
    datos[campo] !== "" &&
    datos[campo] !== undefined &&
    !errores[campo]
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

        <form className="ficha-card" onSubmit={guardar} noValidate>
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
                className={`field__input ${esCampoInvalido("nombreCompleto") ? "field__input--invalid" : ""}`}
                maxLength={100}
                value={datos.nombreCompleto}
                onChange={(e) => actualizarCampo("nombreCompleto", filtrarNombrePersona(e.target.value, 100))}
                onBlur={() => marcarTocado("nombreCompleto")}
                placeholder="Escriba su nombre completo"
              />
              {esCampoInvalido("nombreCompleto") && (
                <span className="field__error" id="nombreCompleto-error">
                  {errores.nombreCompleto}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("sexo", op);
                        marcarTocado("sexo");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("sexo") && (
                <span className="field__error" id="sexo-error">
                  {errores.sexo}
                </span>
              )}
            </div>

            {/* 3. Año de nacimiento */}
            <div className={`ficha-field ${esCampoInvalido("anioNacimiento") ? "ficha-field-error" : ""}`}>
              <label>3. Año de nacimiento</label>
              <input
                type="text"
                inputMode="numeric"
                className={`field__input ${esCampoInvalido("anioNacimiento") ? "field__input--invalid" : ""}`}
                maxLength={4}
                value={datos.anioNacimiento}
                onChange={(e) => actualizarCampo("anioNacimiento", soloDigitos(e.target.value, 4))}
                onBlur={() => marcarTocado("anioNacimiento")}
                placeholder="Ej: 1990"
              />
              {esCampoInvalido("anioNacimiento") && (
                <span className="field__error" id="anioNacimiento-error">
                  {errores.anioNacimiento}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("estadoCivil", op);
                        marcarTocado("estadoCivil");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("estadoCivil") && (
                <span className="field__error" id="estadoCivil-error">
                  {errores.estadoCivil}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("nivelEstudios", op);
                        marcarTocado("nivelEstudios");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("nivelEstudios") && (
                <span className="field__error" id="nivelEstudios-error">
                  {errores.nivelEstudios}
                </span>
              )}
            </div>

            {/* 6. Ocupación */}
            <div className={`ficha-field ${esCampoInvalido("ocupacion") ? "ficha-field-error" : ""}`}>
              <label>6. ¿Cuál es su ocupación o profesión?</label>
              <input
                type="text"
                className={`field__input ${esCampoInvalido("ocupacion") ? "field__input--invalid" : ""}`}
                maxLength={100}
                value={datos.ocupacion}
                onChange={(e) => actualizarCampo("ocupacion", filtrarTextoLibre(e.target.value, 100))}
                onBlur={() => marcarTocado("ocupacion")}
                placeholder="Escriba su ocupación o profesión"
              />
              {esCampoInvalido("ocupacion") && (
                <span className="field__error" id="ocupacion-error">
                  {errores.ocupacion}
                </span>
              )}
            </div>

            {/* 7. Lugar de residencia */}
            <div className="ficha-field-group">
              <label className="ficha-field-group-label">7. Lugar de residencia actual</label>
              <div className="ficha-field-row">
                <div className={`ficha-field ${esCampoInvalido("residenciaCiudad") ? "ficha-field-error" : ""}`}>
                  <label>Ciudad / municipio</label>
                  <input
                    type="text"
                    className={`field__input ${esCampoInvalido("residenciaCiudad") ? "field__input--invalid" : ""}`}
                    maxLength={80}
                    value={datos.residenciaCiudad}
                    onChange={(e) => actualizarCampo("residenciaCiudad", filtrarLugar(e.target.value, 80))}
                    onBlur={() => marcarTocado("residenciaCiudad")}
                  />
                  {esCampoInvalido("residenciaCiudad") && (
                    <span className="field__error" id="residenciaCiudad-error">
                      {errores.residenciaCiudad}
                    </span>
                  )}
                </div>
                <div className={`ficha-field ${esCampoInvalido("residenciaDepartamento") ? "ficha-field-error" : ""}`}>
                  <label>Departamento</label>
                  <input
                    type="text"
                    className={`field__input ${esCampoInvalido("residenciaDepartamento") ? "field__input--invalid" : ""}`}
                    maxLength={80}
                    value={datos.residenciaDepartamento}
                    onChange={(e) => actualizarCampo("residenciaDepartamento", filtrarLugar(e.target.value, 80))}
                    onBlur={() => marcarTocado("residenciaDepartamento")}
                  />
                  {esCampoInvalido("residenciaDepartamento") && (
                    <span className="field__error" id="residenciaDepartamento-error">
                      {errores.residenciaDepartamento}
                    </span>
                  )}
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
                      onChange={() => {
                        actualizarCampo("estrato", op);
                        marcarTocado("estrato");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("estrato") && (
                <span className="field__error" id="estrato-error">
                  {errores.estrato}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("tipoVivienda", op);
                        marcarTocado("tipoVivienda");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("tipoVivienda") && (
                <span className="field__error" id="tipoVivienda-error">
                  {errores.tipoVivienda}
                </span>
              )}
            </div>

            {/* 10. Personas a cargo */}
            <div className={`ficha-field ${esCampoInvalido("personasACargo") ? "ficha-field-error" : ""}`}>
              <label>10. Número de personas que dependen económicamente de usted</label>
              <input
                type="text"
                inputMode="numeric"
                className={`field__input ${esCampoInvalido("personasACargo") ? "field__input--invalid" : ""}`}
                maxLength={2}
                value={datos.personasACargo}
                onChange={(e) => actualizarCampo("personasACargo", soloDigitos(e.target.value, 2))}
                onBlur={() => marcarTocado("personasACargo")}
              />
              {esCampoInvalido("personasACargo") && (
                <span className="field__error" id="personasACargo-error">
                  {errores.personasACargo}
                </span>
              )}
            </div>

            {/* 11. Lugar donde trabaja */}
            <div className="ficha-field-group">
              <label className="ficha-field-group-label">11. Lugar donde trabaja actualmente</label>
              <div className="ficha-field-row">
                <div className={`ficha-field ${esCampoInvalido("trabajoCiudad") ? "ficha-field-error" : ""}`}>
                  <label>Ciudad / municipio</label>
                  <input
                    type="text"
                    className={`field__input ${esCampoInvalido("trabajoCiudad") ? "field__input--invalid" : ""}`}
                    maxLength={80}
                    value={datos.trabajoCiudad}
                    onChange={(e) => actualizarCampo("trabajoCiudad", filtrarLugar(e.target.value, 80))}
                    onBlur={() => marcarTocado("trabajoCiudad")}
                  />
                  {esCampoInvalido("trabajoCiudad") && (
                    <span className="field__error" id="trabajoCiudad-error">
                      {errores.trabajoCiudad}
                    </span>
                  )}
                </div>
                <div className={`ficha-field ${esCampoInvalido("trabajoDepartamento") ? "ficha-field-error" : ""}`}>
                  <label>Departamento</label>
                  <input
                    type="text"
                    className={`field__input ${esCampoInvalido("trabajoDepartamento") ? "field__input--invalid" : ""}`}
                    maxLength={80}
                    value={datos.trabajoDepartamento}
                    onChange={(e) => actualizarCampo("trabajoDepartamento", filtrarLugar(e.target.value, 80))}
                    onBlur={() => marcarTocado("trabajoDepartamento")}
                  />
                  {esCampoInvalido("trabajoDepartamento") && (
                    <span className="field__error" id="trabajoDepartamento-error">
                      {errores.trabajoDepartamento}
                    </span>
                  )}
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
                      marcarTocado("antiguedadEmpresa");
                    }}
                  />
                  <span>Menos de un año</span>
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="Años (si lleva más de 1)"
                  disabled={datos.antiguedadEmpresaMenosUnAnio}
                  className={`field__input ${esCampoInvalido("antiguedadEmpresa") ? "field__input--invalid" : ""}`}
                  maxLength={2}
                  value={datos.antiguedadEmpresaMenosUnAnio ? "" : datos.antiguedadEmpresa}
                  onChange={(e) => actualizarCampo("antiguedadEmpresa", soloDigitos(e.target.value, 2))}
                  onBlur={() => marcarTocado("antiguedadEmpresa")}
                />
              </div>
              {esCampoInvalido("antiguedadEmpresa") && (
                <span className="field__error" id="antiguedadEmpresa-error">
                  {errores.antiguedadEmpresa}
                </span>
              )}
            </div>

            {/* 13. Nombre del cargo */}
            <div className={`ficha-field ${esCampoInvalido("nombreCargo") ? "ficha-field-error" : ""}`}>
              <label>13. ¿Cuál es el nombre del cargo que ocupa en la empresa?</label>
              <input
                type="text"
                className={`field__input ${esCampoInvalido("nombreCargo") ? "field__input--invalid" : ""}`}
                maxLength={100}
                value={datos.nombreCargo}
                onChange={(e) => actualizarCampo("nombreCargo", filtrarTextoLibre(e.target.value, 100))}
                onBlur={() => marcarTocado("nombreCargo")}
              />
              {esCampoInvalido("nombreCargo") && (
                <span className="field__error" id="nombreCargo-error">
                  {errores.nombreCargo}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("tipoCargo", op);
                        marcarTocado("tipoCargo");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("tipoCargo") && (
                <span className="field__error" id="tipoCargo-error">
                  {errores.tipoCargo}
                </span>
              )}
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
                      marcarTocado("antiguedadCargo");
                    }}
                  />
                  <span>Menos de un año</span>
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="Años (si lleva más de 1)"
                  disabled={datos.antiguedadCargoMenosUnAnio}
                  className={`field__input ${esCampoInvalido("antiguedadCargo") ? "field__input--invalid" : ""}`}
                  maxLength={2}
                  value={datos.antiguedadCargoMenosUnAnio ? "" : datos.antiguedadCargo}
                  onChange={(e) => actualizarCampo("antiguedadCargo", soloDigitos(e.target.value, 2))}
                  onBlur={() => marcarTocado("antiguedadCargo")}
                />
              </div>
              {esCampoInvalido("antiguedadCargo") && (
                <span className="field__error" id="antiguedadCargo-error">
                  {errores.antiguedadCargo}
                </span>
              )}
            </div>

            {/* 16. Área / departamento de la empresa */}
            <div className={`ficha-field ${esCampoInvalido("areaODepartamento") ? "ficha-field-error" : ""}`}>
              <label>16. Nombre del departamento, área o sección de la empresa en el que trabaja</label>
              <input
                type="text"
                className={`field__input ${esCampoInvalido("areaODepartamento") ? "field__input--invalid" : ""}`}
                maxLength={120}
                value={datos.areaODepartamento}
                onChange={(e) => actualizarCampo("areaODepartamento", filtrarTextoLibre(e.target.value, 120))}
                onBlur={() => marcarTocado("areaODepartamento")}
              />
              {esCampoInvalido("areaODepartamento") && (
                <span className="field__error" id="areaODepartamento-error">
                  {errores.areaODepartamento}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("tipoContrato", op);
                        marcarTocado("tipoContrato");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("tipoContrato") && (
                <span className="field__error" id="tipoContrato-error">
                  {errores.tipoContrato}
                </span>
              )}
            </div>

            {/* 18. Horas diarias */}
            <div className={`ficha-field ${esCampoInvalido("horasDiarias") ? "ficha-field-error" : ""}`}>
              <label>18. Horas diarias de trabajo establecidas habitualmente por la empresa</label>
              <input
                type="text"
                inputMode="numeric"
                className={`field__input ${esCampoInvalido("horasDiarias") ? "field__input--invalid" : ""}`}
                maxLength={2}
                value={datos.horasDiarias}
                onChange={(e) => actualizarCampo("horasDiarias", soloDigitos(e.target.value, 2))}
                onBlur={() => marcarTocado("horasDiarias")}
              />
              {esCampoInvalido("horasDiarias") && (
                <span className="field__error" id="horasDiarias-error">
                  {errores.horasDiarias}
                </span>
              )}
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
                      onChange={() => {
                        actualizarCampo("tipoSalario", op);
                        marcarTocado("tipoSalario");
                      }}
                    />
                    <span>{op}</span>
                  </label>
                ))}
              </div>
              {esCampoInvalido("tipoSalario") && (
                <span className="field__error" id="tipoSalario-error">
                  {errores.tipoSalario}
                </span>
              )}
            </div>
          </div>

          {/* BOTONES */}
          <div className="questionnaire-navigation">
            <button className="previous-button" type="button" onClick={irAnterior}>
              ← Anterior
            </button>

            <button className="next-button" type="submit">
              Guardar y continuar →
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}