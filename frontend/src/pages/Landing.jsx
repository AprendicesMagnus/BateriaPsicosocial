import { Link } from "react-router-dom";
import Logo from "../components/Logo";
import "../styles/landing.css";

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
  { titulo: "Crear perfil", texto: "El administrador registra la organización y el evaluador SST." },
  { titulo: "Aplicar batería", texto: "Cada trabajador diligencia el cuestionario en línea." },
  { titulo: "Recibir informe", texto: "El sistema tabula, analiza y genera resultados automáticos." },
  { titulo: "Empresa consulta", texto: "El equipo SST revisa indicadores y planes de intervención." },
];

const CONFIANZA = [
  { titulo: "Cifrado extremo a extremo", texto: "Datos protegidos en tránsito y en reposo (HTTPS/TLS)." },
  { titulo: "Resultados anonimizados", texto: "Los reportes grupales agregan la información y protegen la identidad." },
  { titulo: "Custodia profesional", texto: "Solo el evaluador SST y el administrador acceden a resultados individuales." },
  { titulo: "Cumplimiento Ley 1581", texto: "Tratamiento de datos conforme a la normativa colombiana vigente." },
];

export default function Landing() {
  return (
    <div className="landing">
      <header className="nav">
        <div className="container nav__inner">
          <Logo />
          <nav className="nav__links">
            <a href="#como-funciona">Cómo funciona</a>
            <a href="#empresas">Para empresas</a>
            <a href="#psicologos">Psicólogos</a>
            <a href="#normativa">Normativa</a>
          </nav>
          <div className="nav__actions">
            <Link className="btn-nav-secondary" to="/iniciar-sesion">
              Iniciar sesión
            </Link>
            <Link className="btn-nav-primary" to="/crear-cuenta">
              Crear cuenta
            </Link>
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="container hero__inner">
          <span className="hero__tag">Batería de Riesgo Psicosocial · Res. 2764 de 2022</span>
          <h1>
            Promover entornos laborales <span className="accent">saludables</span>
          </h1>
          <p>
            Aplica, tabula y analiza la batería de riesgo psicosocial de forma digital y
            automatizada. Resultados agregados para MiPymes, sin sobrecostos ni procesos manuales.
          </p>
          <div className="hero__cta">
            <Link className="cta-primary" to="/crear-cuenta">
              Más información — Empresas
            </Link>
            <a className="cta-secondary" href="#psicologos">
              Más información — Psicólogos
            </a>
          </div>
        </div>
      </section>

      <div className="stats-band">
        <div className="container stats-band__inner">
          <div className="stat">
            <strong>+40</strong>
            <span>MiPymes objetivo del piloto en el Huila</span>
          </div>
          <div className="stat">
            <strong>+15</strong>
            <span>Psicólogos evaluadores SST vinculados</span>
          </div>
          <div className="stat">
            <strong>+500</strong>
            <span>Trabajadores evaluados en fase piloto</span>
          </div>
        </div>
      </div>

      <div className="container icon-row">
        <div className="icon-chip">📋 Intralaboral</div>
        <div className="icon-chip">🏠 Extralaboral</div>
        <div className="icon-chip">👤 Sociodemográfico</div>
        <div className="icon-chip">📊 Informes</div>
      </div>

      <section className="section" id="normativa">
        <div className="container">
          <div className="section__header">
            <span className="section__eyebrow">Resolución 2764 de 2022</span>
            <h2>Factores evaluados por la batería</h2>
            <p>
              Según la Resolución 2646 de 2008 y su actualización, Resolución 2764 de 2022, la
              batería evalúa tres dimensiones complementarias del riesgo psicosocial.
            </p>
          </div>
          <div className="factor-grid">
            {FACTORES.map((f) => (
              <div className="factor-card" key={f.titulo}>
                <h3>{f.titulo}</h3>
                <ul>
                  {f.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section" id="como-funciona" style={{ background: "var(--white)" }}>
        <div className="container">
          <div className="section__header">
            <span className="section__eyebrow">Proceso</span>
            <h2>Cómo funciona</h2>
            <p>De la aplicación digital del cuestionario al informe de resultados, en cuatro pasos.</p>
          </div>
          <div className="steps-grid">
            {PASOS.map((paso, i) => (
              <div className="step-card" key={paso.titulo}>
                <div className="step-card__num">{i + 1}</div>
                <h4>{paso.titulo}</h4>
                <p>{paso.texto}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section confidence-section">
        <div className="container">
          <div className="section__header">
            <span className="section__eyebrow" style={{ color: "var(--gold-500)" }}>
              Ley 1581 de 2012
            </span>
            <h2 style={{ color: "var(--white)" }}>Confidencialidad y manejo de tus datos</h2>
            <p style={{ color: "#b7bdd6" }}>
              Tratamiento de datos personales conforme a la Ley 1581 de 2012 y la Resolución 2646
              de 2008.
            </p>
          </div>
          <div className="confidence-grid">
            {CONFIANZA.map((c) => (
              <div className="confidence-card" key={c.titulo}>
                <div className="confidence-card__icon">✓</div>
                <h4>{c.titulo}</h4>
                <p>{c.texto}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div className="footer__grid">
            <div className="footer__brand">
              <Logo variant="light" />
              <p>
                Prototipo digital para la aplicación de la Batería de Riesgo Psicosocial,
                desarrollado en el marco del trabajo de grado en Ingeniería de Software, FET.
              </p>
            </div>
            <div className="footer__col">
              <h5>Plataforma</h5>
              <ul>
                <li><a href="#como-funciona">Cómo funciona</a></li>
                <li><Link to="/crear-cuenta">Crear cuenta</Link></li>
                <li><a href="#normativa">Normativa</a></li>
              </ul>
            </div>
            <div className="footer__col">
              <h5>Empresas</h5>
              <ul>
                <li><a href="#empresas">Para MiPymes</a></li>
                <li><a href="#psicologos">Para psicólogos</a></li>
                <li><Link to="/iniciar-sesion">Iniciar sesión</Link></li>
              </ul>
            </div>
            <div className="footer__col">
              <h5>Contacto</h5>
              <ul>
                <li>direccion_software@fet.edu.co</li>
                <li>Neiva, Huila — Colombia</li>
              </ul>
              <div className="footer__social">
                <a href="#" aria-label="Facebook">f</a>
                <a href="#" aria-label="Instagram">in</a>
                <a href="#" aria-label="X">x</a>
              </div>
            </div>
          </div>
          <div className="footer__bottom">
            <span>© {new Date().getFullYear()} Magnus|SIG. Todos los derechos reservados.</span>
            <span>FET — Fundación Escuela Tecnológica de Neiva</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
