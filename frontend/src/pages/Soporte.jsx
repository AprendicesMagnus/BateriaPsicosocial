import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { etiquetaRol } from "../utils/roles";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import "../styles/app-shell.css";
import "../styles/Soporte.css";

// Guía paso a paso según el rol de quien está viendo la página.
const GUIAS_POR_ROL = {
  SUPER_ADMINISTRADOR: [
    "Entra al Panel de administración desde este menú de perfil.",
    "En 'Usuarios y roles' puedes invitar, editar o verificar usuarios.",
    "En 'Planes de baterías' configuras lo que se ve en la página de precios.",
    "En 'Auditoría y privacidad' revisas la actividad de la plataforma.",
  ],
  JEFE: [
    "Desde el Dashboard, registra o elige la empresa activa con la que vas a trabajar.",
    "Crea el Responsable SST de tu empresa al registrarla.",
    "Compra baterías desde 'Comprar baterías' según la cantidad de trabajadores.",
    "Genera enlaces para que los trabajadores respondan la batería.",
    "Consulta los resultados agregados en 'Reportes'.",
  ],
  ADMINISTRADOR: [
    "Desde el Dashboard, elige la empresa activa con la que vas a trabajar.",
    "Invita o gestiona usuarios según los permisos de tu rol.",
    "Consulta los resultados agregados en 'Reportes'.",
  ],
  EVALUADOR_SST: [
    "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
    "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
    "Desde el Dashboard eliges con qué empresa estás trabajando.",
    "Genera enlaces para que los trabajadores respondan la batería.",
    "Consulta los resultados agregados en 'Reportes'.",
  ],
  RESPONSABLE_SST: [
    "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
    "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
    "Genera enlaces para que los trabajadores de tu empresa respondan la batería.",
    "Consulta los resultados agregados en 'Reportes'.",
  ],
};

const FAQ = [
  {
    pregunta: "¿Cómo cambio mi número de resolución?",
    respuesta:
      "Solo Psicólogos y Responsables SST lo ven en 'Ver perfil'. Un administrador debe verificarlo primero; una vez verificado, puedes editarlo hasta 3 veces cada 5 días.",
  },
  {
    pregunta: "¿Cada cuánto puedo editar mi perfil (nombre, apellido, foto)?",
    respuesta: "Una vez cada 5 días. El sistema te indica la fecha y hora exacta en que podrás volver a hacerlo.",
  },
  {
    pregunta: "¿Cómo cambio de empresa activa?",
    respuesta:
      "Si manejas más de una empresa, el selector de 'Empresa activa' está en el Dashboard (o en tu perfil, según tu rol).",
  },
  {
    pregunta: "¿Cómo compro más baterías?",
    respuesta:
      "Desde 'Comprar baterías' eliges la cantidad; el precio se ajusta automáticamente según el plan que corresponda.",
  },
  {
    pregunta: "¿Qué hago si no me llega el código de verificación?",
    respuesta: "Revisa spam/correo no deseado. Si persiste, un administrador puede reenviarte las credenciales desde el Panel.",
  },
];

function PreguntaFAQ({ item }) {
  const [abierta, setAbierta] = useState(false);
  return (
    <div className="soporte-faq-item">
      <button type="button" className="soporte-faq-pregunta" onClick={() => setAbierta((v) => !v)}>
        <span>{item.pregunta}</span>
        <span>{abierta ? "−" : "+"}</span>
      </button>
      {abierta && <p className="soporte-faq-respuesta">{item.respuesta}</p>}
    </div>
  );
}

export default function Soporte() {
  const { usuario } = useAuth();
  const [mensaje, setMensaje] = useState("");
  const [enviado, setEnviado] = useState(false);

  const guia = GUIAS_POR_ROL[usuario?.rol] ?? [];

  function handleEnviar(e) {
    e.preventDefault();
    // Vista previa (solo frontend): todavía no se envía a ningún lado.
    setEnviado(true);
    setMensaje("");
  }

  return (
    <div className="app-shell-page">
      <AppTopbar />
      <main className="app-hero">
        <div className="app-decor app-decor--1" />
        <div className="app-decor app-decor--2" />
        <div className="app-decor app-decor--3" />

        <div className="app-content soporte-page">
          <BotonRegresar />
          <h1 className="app-title">Centro de ayuda</h1>
          <p className="app-subtitle">
            Guía rápida para tu rol ({etiquetaRol(usuario?.rol)}), preguntas frecuentes y contacto con soporte.
          </p>

          {guia.length > 0 && (
            <section className="app-card soporte-card">
              <h2>Primeros pasos — {etiquetaRol(usuario?.rol)}</h2>
              <ol className="soporte-guia">
                {guia.map((paso, i) => (
                  <li key={i}>{paso}</li>
                ))}
              </ol>
            </section>
          )}

          <section className="app-card soporte-card">
            <h2>Preguntas frecuentes</h2>
            <div className="soporte-faq-lista">
              {FAQ.map((item) => (
                <PreguntaFAQ key={item.pregunta} item={item} />
              ))}
            </div>
          </section>

          <section className="app-card soporte-card">
            <h2>¿No encontraste la respuesta?</h2>
            <p>Escríbenos directamente a <strong>aprendizmagnus@gmail.com</strong>, o cuéntanos aquí tu problema:</p>
            {enviado ? (
              <p className="soporte-exito">¡Gracias! (vista previa — aún no se envía a soporte)</p>
            ) : (
              <form onSubmit={handleEnviar} className="soporte-form">
                <textarea
                  rows={4}
                  placeholder="Describe tu problema o duda..."
                  value={mensaje}
                  onChange={(e) => setMensaje(e.target.value)}
                  required
                />
                <button type="submit" className="soporte-btn-primary">
                  Enviar
                </button>
              </form>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
