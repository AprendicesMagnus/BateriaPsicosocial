/**
 * Tarjeta de consentimiento informado que se muestra antes de comenzar la batería.
 * Incluye una fila que abre el texto legal completo en una ventana modal y el botón para comenzar.
 */
import { useEffect, useState } from "react";
import {
  HiOutlineShieldCheck,
  HiOutlineChevronRight,
  HiOutlineArrowRight,
  HiX,
} from "react-icons/hi";
import "../styles/Consentimiento.css";

function TextoConsentimiento() {
  return (
    <>
      <p>
        El profesional de Psicología responsable de la evaluación te invita a participar en la aplicación
        de la Batería de Instrumentos para la Evaluación de Factores de Riesgo Psicosocial, conforme a la
        normativa colombiana aplicable.
      </p>
      <p>
        Para iniciar, deberás diligenciar tus datos generales y responder los cuestionarios
        correspondientes. No es necesario crear una cuenta. La información proporcionada será tratada de
        manera confidencial y utilizada exclusivamente para los fines de evaluación, análisis y prevención
        de los factores de riesgo psicosocial, de acuerdo con las finalidades autorizadas.
      </p>
      <p>
        <strong>Protección de datos personales:</strong> En cumplimiento de la Ley 1581 de 2012 y sus
        normas reglamentarias, tus datos personales serán tratados bajo principios de confidencialidad,
        seguridad y acceso restringido. El acceso estará limitado al personal autorizado, de acuerdo con
        sus funciones y responsabilidades. La información será conservada durante el tiempo legalmente
        aplicable y conforme a las políticas de tratamiento de datos del responsable.
      </p>
      <p>
        <strong>Consentimiento informado:</strong> Antes de continuar, declara que has leído y comprendido
        la información suministrada, que conoces la finalidad de la evaluación y el tratamiento de tus
        datos personales, y que has tenido la oportunidad de resolver tus dudas. Tu participación deberá
        contar con el consentimiento informado correspondiente y las garantías de confidencialidad
        aplicables.
      </p>
      <p>
        Al seleccionar la opción de aceptación, manifiestas tu consentimiento para el tratamiento de tus
        datos personales conforme a la autorización y política de tratamiento de datos aplicables.
      </p>
    </>
  );
}

export default function ConsentimientoInformado({ acepta, onChange, onComenzar, iniciando = false }) {
  const [abierto, setAbierto] = useState(false);

  useEffect(() => {
    if (!abierto) return;
    const cerrarConEsc = (e) => e.key === "Escape" && setAbierto(false);
    window.addEventListener("keydown", cerrarConEsc);
    return () => window.removeEventListener("keydown", cerrarConEsc);
  }, [abierto]);

  function aceptarDesdeModal() {
    onChange(true);
    setAbierto(false);
  }

  return (
    <section className="consentimiento">
      <header className="consentimiento__header">
        <span className="consentimiento__icono-caja" aria-hidden="true">
          <HiOutlineShieldCheck />
        </span>
        <div>
          <h2>Consentimiento informado</h2>
          <p className="consentimiento__sub">Protección de datos personales · Ley 1581 de 2012</p>
        </div>
      </header>

      <div className="consentimiento__cuerpo">
        <p className="consentimiento__intro">
          Antes de comenzar, revisa cómo se recolectarán, usarán y protegerán tus datos personales y tus
          respuestas. Tu participación es voluntaria y la información se tratará de forma confidencial.
        </p>

        <button type="button" className="consentimiento__leer" onClick={() => setAbierto(true)}>
          <strong className="consentimiento__leer-texto">Leer consentimiento informado</strong>
          <HiOutlineChevronRight className="consentimiento__leer-flecha" aria-hidden="true" />
        </button>

        <label className={`consentimiento__check${acepta ? " is-checked" : ""}`}>
          <input type="checkbox" checked={acepta} onChange={(e) => onChange(e.target.checked)} />
          <span className="consentimiento__caja" aria-hidden="true" />
          <span>
            He leído y comprendido el consentimiento informado y la política de tratamiento de datos
            personales, y autorizo el tratamiento de mis datos conforme a las finalidades informadas.
          </span>
        </label>
      </div>

      <footer className="consentimiento__pie">
        <span className="consentimiento__pista">
          {acepta ? "Todo listo, puedes comenzar." : "Acepta el consentimiento para continuar."}
        </span>
        <button
          type="button"
          className="consentimiento__comenzar"
          onClick={onComenzar}
          disabled={!acepta || iniciando}
        >
          {iniciando ? "Procesando..." : "Comenzar evaluación"}
          {!iniciando && <HiOutlineArrowRight aria-hidden="true" />}
        </button>
      </footer>

      {abierto && (
        <div className="consentimiento-modal" onClick={() => setAbierto(false)}>
          <div
            className="consentimiento-modal__caja"
            role="dialog"
            aria-modal="true"
            aria-labelledby="consentimiento-modal-titulo"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="consentimiento-modal__top">
              <span className="consentimiento__icono-caja" aria-hidden="true">
                <HiOutlineShieldCheck />
              </span>
              <h3 id="consentimiento-modal-titulo">
                Consentimiento informado para la aplicación de la Batería de Riesgo Psicosocial
              </h3>
              <button
                type="button"
                className="consentimiento-modal__cerrar"
                onClick={() => setAbierto(false)}
                aria-label="Cerrar"
              >
                <HiX />
              </button>
            </div>
            <div className="consentimiento-modal__cuerpo">
              <TextoConsentimiento />
            </div>
            <div className="consentimiento-modal__acciones">
              <button type="button" className="btn-secondary-lite" onClick={() => setAbierto(false)}>
                Cerrar
              </button>
              <button type="button" className="consentimiento__comenzar" onClick={aceptarDesdeModal}>
                Acepto el consentimiento
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
