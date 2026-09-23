import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import "../styles/Inicio.css";


const FACTORES = [
  {
    titulo: "Intralaboral",
    items: [
      "Liderazgo y relaciones sociales",
      "Control sobre el trabajo",
      "Demandas del trabajo",
      "Recompensas",
    ],
  },
  {
    titulo: "Extralaboral",
    items: [
      "Tiempo fuera del trabajo",
      "Relaciones familiares",
      "Situación económica del grupo familiar",
    ],
  },
  {
    titulo: "Individual",
    items: [
      "Características sociodemográficas",
      "Estilos de afrontamiento",
      "Síntomas de estrés",
    ],
  },
];

const PASOS = [
  {
    titulo: "Crear perfil",
    texto:
      "El administrador registra la organización y el evaluador SST.",
  },
  {
    titulo: "Aplicar batería",
    texto:
      "Cada trabajador diligencia el cuestionario en línea.",
  },
  {
    titulo: "Recibir informe",
    texto:
      "El sistema tabula, analiza y genera resultados automáticos.",
  },
  {
    titulo: "Empresa consulta",
    texto:
      "El equipo SST revisa indicadores y planes de intervención.",
  },
];

const CONFIANZA = [
  {
    titulo: "Cifrado extremo a extremo",
    texto:
      "Datos protegidos en tránsito y en reposo (HTTPS/TLS).",
  },
  {
    titulo: "Resultados anonimizados",
    texto:
      "Los reportes grupales agregan la información y protegen la identidad.",
  },
  {
    titulo: "Custodia profesional",
    texto:
      "Solo el evaluador SST y el administrador acceden a resultados individuales.",
  },
  {
    titulo: "Cumplimiento Ley 1581",
    texto:
      "Tratamiento de datos conforme a la normativa colombiana vigente.",
  },
];

export default function Inicio() {
  const [slide, setSlide] = useState(0);
  const [menuEmpresasAbierto, setMenuEmpresasAbierto] = useState(false);
  const [menuTiendaAbierto, setMenuTiendaAbierto] = useState(false);
  const menuEmpresasRef = useRef(null);
  const menuTiendaRef = useRef(null);

  const nombreUsuario = usuario
    ? `${usuario.nombre ?? ""} ${usuario.apellido ?? ""}`.trim()
    : "";
  const rolUsuario = usuario?.rol ?? "";
  const iniciales =
    nombreUsuario
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase())
      .join("") || "U";

  function handleVerPerfil() {
    setMenuPerfilAbierto(false);
    navigate("/perfil");
  }

  function handleCerrarSesion() {
    setMenuPerfilAbierto(false);
    cerrarSesion?.();
    navigate("/iniciar-sesion");
  }

  return (
    <div className="landing">

      {/* =====================================================
          NAVBAR
      ====================================================== */}

      <header className="nav">
        <div className="container nav__inner">

          <div
            className="nav__logos"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 15,
            }}
          >
            <img
              src="/logo a 2_Mesa de trabajo 1.jpg"
              alt="Magnus"
              style={{
                height: 120,
                marginRight: "auto",
              }}
            />

            <img
              src="/logo javeriana.jpg"
              alt="Javeriana"
              style={{
                height: 50,
              }}
            />

            <img
              src="/ministerio.jpg"
              alt="Ministerio"
              style={{
                height: 110,
              }}
            />
          </div>

          <nav className="nav__links">
            <a href="#como-funciona">Cómo funciona</a>

            <div className="nav__dropdown" ref={menuEmpresasRef} style={{ position: "relative" }}>
              <button
                type="button"
                className="nav__dropdown-trigger"
                onClick={() => setMenuEmpresasAbierto((v) => !v)}
                aria-haspopup="true"
                aria-expanded={menuEmpresasAbierto}
                style={{
                  background: "none",
                  border: "none",
                  font: "inherit",
                  color: "inherit",
                  cursor: "pointer",
                  padding: 0,
                  fontWeight: "bold"
                }}
              >
                Empresas
              </button>

              {menuEmpresasAbierto && (
                <div
                  className="nav__dropdown-menu"
                  style={{
                    position: "absolute",
                    top: "calc(100% + 12px)",
                    left: 0,
                    background: "var(--white)",
                    borderRadius: "var(--radius-md, 10px)",
                    boxShadow: "var(--shadow-card, 0 8px 24px rgba(15,26,61,0.12))",
                    padding: 6,
                    minWidth: 170,
                    zIndex: 20,
                  }}
                >
                  <Link
                    to="/crear-empresa"
                    onClick={() => setMenuEmpresasAbierto(false)}
                    style={{
                      display: "block",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "var(--ink-900, #12314b)",
                    }}
                  >
                    <Link to="/crear-empresa" className="boton-encuestas"> Crear empresa</Link>
                  </Link>
                </div>
              )}
            </div>

            <div className="nav__dropdown" ref={menuTiendaRef} style={{ position: "relative" }}>
              <button
                type="button"
                className="nav__dropdown-trigger"
                onClick={() => setMenuTiendaAbierto((v) => !v)}
                aria-haspopup="true"
                aria-expanded={menuTiendaAbierto}
                style={{
                  background: "none",
                  border: "none",
                  font: "inherit",
                  fontWeight: 600,
                  color: "var(--ink-900, #12314b)",
                  cursor: "pointer",
                  padding: 0,
                }}
              >
                Tienda
              </button>

              {menuTiendaAbierto && (
                <div
                  className="nav__dropdown-menu"
                  style={{
                    position: "absolute",
                    top: "calc(100% + 12px)",
                    left: 0,
                    background: "var(--white)",
                    borderRadius: "var(--radius-md, 10px)",
                    boxShadow: "var(--shadow-card, 0 8px 24px rgba(15,26,61,0.12))",
                    padding: 6,
                    minWidth: 170,
                    zIndex: 20,
                  }}
                >
                  <button
                    type="button"
                    className="nav__dropdown-option"
                    onClick={() => {
                      // Aquí puedes colocar la acción para comprar
                      setMenuTiendaAbierto(false);
                    }}
                    style={{
                      display: "block",
                      width: "100%",
                      textAlign: "left",
                      background: "none",
                      border: "none",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "var(--ink-900, #12314b)",
                      cursor: "pointer",
                    }}
                  >
                     <Link to="/pago" className="boton-encuestas"> Comprar baterías</Link>
                    
                  </button>
                </div>
              )}
            </div>

            <Link to="/dashboard" className="boton-encuestas"> Encuestas</Link>
          </nav>

          
        </div>
      </header>


      {/* =====================================================
          HERO + CARRUSEL DE FONDO
      ====================================================== */}

      <section className="hero">

        {/* CARRUSEL DE IMÁGENES */}
        <div className="hero__background">
          <video
            className="hero__background-video"
            src="/fondo-seguridad.mp4"
            poster="/pasare1.jpg"
            autoPlay
            muted
            loop
            playsInline
          />
        </div>


        {/* CAPA OSCURA AZUL */}
        <div className="hero__overlay"></div>


        {/* CONTENIDO DEL HERO */}
        <div className="container hero__inner">

          <div className="hero__content">

            <span className="hero__tag">
              Batería de Riesgo Psicosocial · Res. 2764 de 2022
            </span>

            <h1>
              Promover entornos laborales{" "}
              <span className="accent">
                saludables
              </span>
            </h1>

            {usuario ? (
              <p>Bienvenido de nuevo, {nombreUsuario.split(" ")[0] || "de nuevo"}.</p>
            ) : (
              <p>
                hola este es el inicio 
              </p>
            )}

            <div className="hero__cta">

              {usuario ? (
                <>
                  <Link className="cta-primary" to="/pago">
                    Comprar batería
                  </Link>
                  <Link className="cta-secondary" to="/reportes">
                    Ver mis reportes
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    className="cta-primary"
                    to="/crear-cuenta"
                  >
                    Más información — Empresas
                  </Link>

                  <a
                    className="cta-secondary"
                    href="#psicologos"
                  >
                    Más información — Clientes
                  </a>
                </>
              )}
            </div>
          </div>
        </div>

      </section>


      {/* =====================================================
          ESTADÍSTICAS
      ====================================================== */}

      <div className="stats-band">

        <div className="container stats-band__inner">

          <div className="stat">
            <strong>+40</strong>
            <span>
              MiPymes objetivo del piloto en el Huila
            </span>
          </div>

          <div className="stat">
            <strong>+15</strong>
            <span>
              Psicólogos evaluadores SST vinculados
            </span>
          </div>

          <div className="stat">
            <strong>+500</strong>
            <span>
              Trabajadores evaluados en fase piloto
            </span>
          </div>

        </div>

      </div>


      {/* =====================================================
          ICONOS
      ====================================================== */}

      <div className="container icon-row">

        <div className="icon-chip">
          Intralaboral
        </div>

        <div className="icon-chip">
          Extralaboral
        </div>

        <div className="icon-chip">
          Sociodemográfico
        </div>

        <div className="icon-chip">
          Informes
        </div>

      </div>


      {/* =====================================================
          FACTORES
      ====================================================== */}

      <section
        className="section"
        id="normativa"
      >

        <div className="container">

          <div className="section__header">

            <span className="section__eyebrow">
              Resolución 2764 de 2022
            </span>

            <h2>
              Factores evaluados por la batería
            </h2>

            <p>
              Según la Resolución 2646 de 2008 y su
              actualización, Resolución 2764 de 2022,
              la batería evalúa tres dimensiones
              complementarias del riesgo psicosocial.
            </p>

          </div>


          <div className="factor-grid">

            {FACTORES.map((factor) => (

              <div
                className="factor-card"
                key={factor.titulo}
              >

                <h3>
                  {factor.titulo}
                </h3>

                <ul>

                  {factor.items.map((item) => (

                    <li key={item}>
                      {item}
                    </li>

                  ))}

                </ul>

              </div>

            ))}

          </div>

        </div>

      </section>


      {/* =====================================================
          CÓMO FUNCIONA
      ====================================================== */}

      <section
        className="section"
        id="como-funciona"
        style={{
          background: "var(--white)",
        }}
      >

        <div className="container">

          <div className="section__header">

            <span className="section__eyebrow">
              Proceso
            </span>

            <h2>
              Cómo funciona
            </h2>

            <p>
              De la aplicación digital del cuestionario
              al informe de resultados, en cuatro pasos.
            </p>

          </div>


          <div className="steps-grid">

            {PASOS.map((paso, index) => (

              <div
                className="step-card"
                key={paso.titulo}
              >

                <div className="step-card__num">
                  {index + 1}
                </div>

                <h4>
                  {paso.titulo}
                </h4>

                <p>
                  {paso.texto}
                </p>

              </div>

            ))}

          </div>

        </div>

      </section>


      {/* =====================================================
          CONFIDENCIALIDAD
      ====================================================== */}

      <section className="section confidence-section">

        <div className="container">

          <div className="section__header">

            <span
              className="section__eyebrow"
              style={{
                color: "var(--gold-500)",
              }}
            >
              Ley 1581 de 2012
            </span>

            <h2
              style={{
                color: "var(--white)",
              }}
            >
              Confidencialidad y manejo de tus datos
            </h2>

            <p
              style={{
                color: "#b7bdd6",
              }}
            >
              Tratamiento de datos personales conforme
              a la Ley 1581 de 2012 y la Resolución 2646
              de 2008.
            </p>

          </div>


          <div className="confidence-grid">

            {CONFIANZA.map((confianza) => (

              <div
                className="confidence-card"
                key={confianza.titulo}
              >

                <div className="confidence-card__icon">
                  ✓
                </div>

                <h4>
                  {confianza.titulo}
                </h4>

                <p>
                  {confianza.texto}
                </p>

              </div>

            ))}

          </div>

        </div>

      </section>


      {/* =====================================================
          FOOTER
      ====================================================== */}

      <footer className="footer">

        <div className="container">

          <div className="footer__grid">

            <div className="footer__brand">

              <img
                src="/logo oscuro.png"
                alt="Magnus"
                style={{
                  height: 80,
                }}
              />

              <p>
                Prototipo digital para la aplicación
                de la Batería de Riesgo Psicosocial.
              </p>

            </div>


            <div className="footer__col">

              <h5>
                Plataforma
              </h5>

              <ul>

                <li>
                  <a href="#como-funciona">
                    Cómo funciona
                  </a>
                </li>

                <li>
                  <Link to="/crear-cuenta">
                    Crear cuenta
                  </Link>
                </li>

                <li>
                  <a href="#normativa">
                    Normativa
                  </a>
                </li>

              </ul>

            </div>


            <div className="footer__col">

              <h5>
                Empresas
              </h5>

              <ul>

                <li>
                  <Link to="/verificar-nit">
                    Para MiPymes
                  </Link>
                </li>

                <li>
                  <a href="#psicologos">
                    Para clientes
                  </a>
                </li>

                {usuario ? (
                  <li>
                    <Link to="/perfil">
                      Mi perfil
                    </Link>
                  </li>
                ) : (
                  <li>
                    <Link to="/iniciar-sesion">
                      Iniciar sesión
                    </Link>
                  </li>
                )}

              </ul>

            </div>


            <div className="footer__col">

              <h5>
                Contacto
              </h5>

              <ul>

                <li>
                  direccion_software@fet.edu.co
                </li>

                <li>
                  Neiva, Huila — Colombia
                </li>

              </ul>


              <div className="footer__social">

                <a
                  href="#"
                  aria-label="Facebook"
                >
                  f
                </a>

              </div>

            </div>

          </div>


          <div className="footer__bottom">

            <span>
              © {new Date().getFullYear()} Magnus|SIG.
              Todos los derechos reservados.
            </span>

            <span></span>

          </div>

        </div>

      </footer>

    </div>
  );
}