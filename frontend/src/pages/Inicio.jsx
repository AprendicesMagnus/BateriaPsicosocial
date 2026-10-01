import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom"; // <-- AGREGADO AQUÍ "useNavigate"
import { VscBriefcase } from "react-icons/vsc";
import { BsCart4 } from "react-icons/bs";
import { BsCreditCard } from "react-icons/bs";
import { BsFillClipboard2Fill } from "react-icons/bs";
import {  HiOutlineUser,  HiOutlineDocumentText,  HiOutlineClipboardList,  HiOutlineClipboardCheck,  HiOutlineChartBar,} from "react-icons/hi";
import "../styles/Inicio.css";
import "../styles/app-shell.css";
import { useAuth } from "../context/AuthContext"; // <-- EN LÍNEA NUEVA: IMPORTADO "useAuth"
import { urlArchivo } from "../api/client";



const PASOS = [
  { titulo: "Crear perfil", texto: "Registro del colaborador", icono: HiOutlineUser },
  { titulo: "Registrar empresa", texto: "Registro de su empresa a cargo ", icono: HiOutlineDocumentText },
  { titulo: "Seleccionar cuestionario", texto: "Elegir que cuestionario presentaran los usuarios ", icono: HiOutlineClipboardList },
  { titulo: "Realiza los cuestionarios", texto: "Cuestionarios Formas A/B + extralaboral", icono: HiOutlineClipboardCheck },
  { titulo: "Recibir informe", texto: "Resultado individual confidencial", icono: HiOutlineClipboardCheck },
  { titulo: "Empresa consulta", texto: "Informe agregado, sin datos individuales", icono: HiOutlineChartBar },
];

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
  const [menuPerfilAbierto, setMenuPerfilAbierto] = useState(false);
  const menuEmpresasRef = useRef(null);
  const menuTiendaRef = useRef(null);
  const menuPerfilRef = useRef(null);

  // Ajusta "cerrarSesion" si tu AuthContext la expone con otro nombre.
  const { usuario, cerrarSesion } = useAuth();
  const navigate = useNavigate();

  // Cierra cualquier desplegable si se hace clic fuera de él.
  useEffect(() => {
    function handleClickFuera(e) {
      if (menuEmpresasRef.current && !menuEmpresasRef.current.contains(e.target)) {
        setMenuEmpresasAbierto(false);
      }
      if (menuTiendaRef.current && !menuTiendaRef.current.contains(e.target)) {
        setMenuTiendaAbierto(false);
      }
      if (menuPerfilRef.current && !menuPerfilRef.current.contains(e.target)) {
        setMenuPerfilAbierto(false);
      }
    }
    document.addEventListener("mousedown", handleClickFuera);
    return () => document.removeEventListener("mousedown", handleClickFuera);
  }, []);

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
                  fontWeight: "bold",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                 <VscBriefcase size={18} />
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
                    to="/verificar-nit"
                    onClick={() => setMenuEmpresasAbierto(false)}
                    className="boton-encuestas"
                    style={{
                      display: "block",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "var(--ink-900, #12314b)",
                    }}
                  >
                    Crear empresa
                  </Link>
                  <Link
                    to="/mis-empresas"
                    onClick={() => setMenuEmpresasAbierto(false)}
                    className="boton-encuestas"
                    style={{
                      display: "block",
                      padding: "10px 12px",
                      borderRadius: "8px",
                      fontSize: 14,
                      fontWeight: 600,
                      color: "var(--ink-900, #12314b)",
                    }}
                  >
                    Mis Empresas
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
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                <BsCart4   size={18} />
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
                    className="nav__dropdown-option boton-encuestas"
                    onClick={() => {
                      setMenuTiendaAbierto(false);
                      navigate("/pago");
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
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    
                    <BsCreditCard />
                      <Link to="/pago" className="boton-encuestas"> Comprar baterías</Link>
                    
                  </button>
                </div>
              )}
            </div>
            <Link  to="/dashboard"  onClick={() => setMenuTiendaAbierto(false)}  style={{
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
              gap: "8px",
              }}
              >
              <BsFillClipboard2Fill size={16} />
              <span>Encuestas</span>
            </Link>
            
          </nav>

          {/* =====================================================
              PERFIL DEL USUARIO (esquina derecha, ya logueado)
          ====================================================== */}
          <div className="app-profile-menu" ref={menuPerfilRef}>
            <button
              type="button"
              className="app-profile"
              onClick={() => setMenuPerfilAbierto((v) => !v)}
              aria-haspopup="true"
              aria-expanded={menuPerfilAbierto}
            >
              {usuario?.fotoUrl ? (
                <img
                  src={urlArchivo(usuario.fotoUrl)}
                  alt={nombreUsuario}
                  className="app-avatar app-avatar--foto"
                />
              ) : (
                <div className="app-avatar">{iniciales}</div>
              )}
              <div className="app-profile-text">
                <span className="app-profile-name">{nombreUsuario || "Usuario"}</span>
                {rolUsuario && <span className="app-profile-role">{rolUsuario}</span>}
              </div>
            </button>

            {menuPerfilAbierto && (
              <div className="app-profile-dropdown">
                <button type="button" onClick={handleVerPerfil}>
                  Ver perfil
                </button>
                <button
                  type="button"
                  className="app-profile-dropdown-danger"
                  onClick={handleCerrarSesion}
                >
                  Cerrar sesión
                </button>
              </div>
            )}
          </div>

        </div>
      </header>


      {/* =====================================================
          HERO + CARRUSEL DE FONDO
      ====================================================== */}

      <section className="hero">

        {/* VIDEO DE FONDO */}
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

              <Link
                className="cta-primary"
                to="/dashboard"
              >
                Más información — Encuestas
              </Link>
              {/* =====================================================
          pensar en que apartado mandar esta informacion o que hacer con ese boton
      ===================================================== */}
              <a
                className="cta-secondary"
                href="#"
              >
                Más información — Clientes
              </a>
            </div>
          </div>
        </div>

      </section>

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

        <section className="section como-funciona" id="como-funciona">
          <div className="container">

            <h2 className="como-funciona__titulo">Cómo funciona</h2>

            <div className="pasos">
              {PASOS.map((paso, index) => {
                const Icono = paso.icono;
                return (
                  <div className="paso" key={paso.titulo}>
                    <div className="paso__circulo">
                      <Icono size={28} />
                    </div>
                    <h4 className="paso__titulo">
                      {index + 1}. {paso.titulo}
                    </h4>
                    <p className="paso__texto">{paso.texto}</p>
                  </div>
                );
              })}
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

                <li>
                  <Link to="/iniciar-sesion">
                    Iniciar sesión
                  </Link>
                </li>
              </ul>
            </div>


            <div className="footer__col">

              <h5>    Contacto  </h5>
              <ul>
                <li>
                  direccion_software@fet.edu.co
                </li>
                <li>   Neiva, Huila — Colombia </li>
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
            <span className="texto-footer">
              © {new Date().getFullYear()} Magnus|SIG. Todos los derechos reservados.
            </span>
          </div>

        </div>

      </footer>

    </div>
  );
}