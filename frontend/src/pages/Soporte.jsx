import { useEffect, useState } from "react";
import {
  HiOutlineShieldCheck,
  HiOutlineBriefcase,
  HiOutlineUserGroup,
  HiOutlineClipboardCheck,
  HiOutlineAcademicCap,
  HiOutlineMail,
  HiOutlineChatAlt2,
  HiOutlineDownload,
  HiOutlineBookOpen,
  HiOutlineLightBulb,
  HiOutlineSpeakerphone,
  HiOutlineClock,
  HiOutlineSearch,
  HiOutlineQuestionMarkCircle,
  HiOutlineFlag,
  HiOutlineCollection,
  HiOutlineChevronDown,
} from "react-icons/hi";
import { useAuth } from "../context/AuthContext";
import { crearTicketSoporte, fetchContenidoSoporte, fetchMisTicketsSoporte } from "../api/soporte";
import Paginador from "../components/Paginador";
import { usePaginacion } from "../hooks/usePaginacion";
import { etiquetaRol } from "../utils/roles";
import { normalizar } from "../utils/encuestas";
import AppTopbar from "../components/AppTopbar";
import BotonRegresar from "../components/BotonRegresar";
import "../styles/app-shell.css";
import "../styles/Soporte.css";

// Guía paso a paso por rol. Cada una trae su propio ícono y color de acento.
const GUIAS_POR_ROL = {
  SUPER_ADMINISTRADOR: {
    icono: HiOutlineShieldCheck,
    color: "#7c3aed",
    pasos: [
      "Entra al Panel de administración desde este menú de perfil.",
      "En 'Usuarios y roles' puedes invitar, editar o verificar usuarios.",
      "En 'Planes de baterías' configuras lo que se ve en la página de precios.",
      "En 'Auditoría y privacidad' revisas la actividad de la plataforma.",
    ],
  },
  JEFE: {
    icono: HiOutlineBriefcase,
    color: "#dd8f13",
    pasos: [
      "Desde el Dashboard, registra o elige la empresa activa con la que vas a trabajar.",
      "Crea el Responsable SST de tu empresa al registrarla.",
      "Compra baterías desde 'Comprar baterías' según la cantidad de trabajadores.",
      "Genera enlaces para que los trabajadores respondan la batería.",
      "Consulta los resultados agregados en 'Reportes'.",
    ],
  },
  ADMINISTRADOR: {
    icono: HiOutlineUserGroup,
    color: "#2d3f82",
    pasos: [
      "Desde el Dashboard, elige la empresa activa con la que vas a trabajar.",
      "Invita o gestiona usuarios según los permisos de tu rol.",
      "Consulta los resultados agregados en 'Reportes'.",
    ],
  },
  EVALUADOR_SST: {
    icono: HiOutlineAcademicCap,
    color: "#1f9d55",
    pasos: [
      "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
      "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
      "Desde el Dashboard eliges con qué empresa estás trabajando.",
      "Genera enlaces para que los trabajadores respondan la batería.",
      "Consulta los resultados agregados en 'Reportes'.",
    ],
  },
  RESPONSABLE_SST: {
    icono: HiOutlineClipboardCheck,
    color: "#d64545",
    pasos: [
      "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
      "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
      "Genera enlaces para que los trabajadores de tu empresa respondan la batería.",
      "Consulta los resultados agregados en 'Reportes'.",
    ],
  },
};

const ORDEN_ROLES = ["SUPER_ADMINISTRADOR", "JEFE", "ADMINISTRADOR", "EVALUADOR_SST", "RESPONSABLE_SST"];

// El backend conserva EVALUADOR_SST como código interno; se aceptan también
// las variantes de nombre que pueden llegar desde perfiles o sesiones antiguas.
function normalizarRolSoporte(rol) {
  const codigo = String(rol?.codigo || rol || "")
    .trim()
    .toUpperCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[\s-]+/g, "_");
  if (["PSICOLOGO", "PSICOLOGA", "EVALUADOR", "EVALUADOR_SST"].includes(codigo)) return "EVALUADOR_SST";
  return ORDEN_ROLES.includes(codigo) ? codigo : null;
}

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
  {
    pregunta: "¿Son confidenciales las respuestas de los trabajadores?",
    respuesta:
      "Sí. Las respuestas individuales son confidenciales; la empresa solo ve resultados agregados, nunca respuestas por persona.",
  },
  {
    pregunta: "¿Qué pasa si un trabajador pierde el enlace de la encuesta?",
    respuesta: "El Psicólogo o Responsable SST puede volver a generar el enlace para ese trabajador desde su panel de enlaces.",
  },
  {
    pregunta: "¿Puedo tener varias empresas con la misma cuenta?",
    respuesta:
      "Sí, si eres Jefe, Administrador o Psicólogo. Cada empresa tiene sus propios usuarios, enlaces y reportes por separado.",
  },
  {
    pregunta: "¿Qué hago si olvidé mi contraseña?",
    respuesta: "En la pantalla de inicio de sesión usa '¿Olvidaste tu contraseña?' para recibir un código de recuperación.",
  },
];

// Secciones informativas nuevas (su contenido lo edita el Super Administrador desde el Panel).
const SECCIONES_INFO = [
  { clave: "riesgo", titulo: "Cómo interpretar los resultados", icono: HiOutlineLightBulb },
  { clave: "glosario", titulo: "Glosario", icono: HiOutlineBookOpen },
  { clave: "novedades", titulo: "Novedades y avisos", icono: HiOutlineSpeakerphone },
  { clave: "atencion", titulo: "Horarios y canales de atención", icono: HiOutlineClock },
];

function PreguntaFAQ({ item }) {
  const [abierta, setAbierta] = useState(false);
  return (
    <div className={`soporte-faq-item ${abierta ? "soporte-faq-item--abierta" : ""}`}>
      <button type="button" className="soporte-faq-pregunta" onClick={() => setAbierta((v) => !v)}>
        <span>{item.pregunta}</span>
        <span className="soporte-faq-icono">{abierta ? "−" : "+"}</span>
      </button>
      {abierta && <p className="soporte-faq-respuesta">{item.respuesta}</p>}
    </div>
  );
}

function formatearFechaMensaje(iso) {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "";
  return fecha.toLocaleString("es-CO", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Soporte() {
  const { usuario, token } = useAuth();
  const [mensaje, setMensaje] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState("");
  const rolUsuario = normalizarRolSoporte(usuario?.rol);
  const [rolActivo, setRolActivo] = useState(rolUsuario || "EVALUADOR_SST");

  // AuthContext puede cargar el usuario después del primer render. Sin este efecto,
  // el Centro de ayuda podía conservar una guía incorrecta al entrar.
  useEffect(() => {
    if (rolUsuario) setRolActivo(rolUsuario);
  }, [rolUsuario]);

  // Contenido editable (si el servidor no responde, se usan las guías y preguntas por defecto de este archivo).
  const [contenido, setContenido] = useState(null);
  const [busqueda, setBusqueda] = useState("");
  const [seccion, setSeccion] = useState("faq");
  const [abierto, setAbierto] = useState(null); // mensaje expandido en "Mis mensajes"
  const [misMensajes, setMisMensajes] = useState([]);

  function cargarMisMensajes() {
    if (!token) return;
    fetchMisTicketsSoporte(token)
      .then((res) => setMisMensajes(Array.isArray(res) ? res : []))
      .catch(() => {});
  }

  useEffect(() => {
    if (token) cargarMisMensajes();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    fetchContenidoSoporte(token)
      .then(setContenido)
      .catch(() => {});
  }, [token]);

  const guia = GUIAS_POR_ROL[rolActivo];
  const pasos = contenido?.[`guia_${rolActivo}`]?.length ? contenido[`guia_${rolActivo}`].map((i) => i.texto) : guia.pasos;
  const preguntas = contenido?.faq?.length
    ? contenido.faq.map((i) => ({ pregunta: i.titulo, respuesta: i.texto }))
    : FAQ;

  const consulta = normalizar(busqueda.trim());
  const buscando = consulta.length > 0;
  const coincide = (...campos) => campos.some((campo) => normalizar(campo).includes(consulta));
  const preguntasVisibles = buscando
    ? preguntas.filter((p) => coincide(p.pregunta, p.respuesta))
    : preguntas;
  const seccionesContenido = SECCIONES_INFO.map((seccion) => ({
    ...seccion,
    items: (contenido?.[seccion.clave] || []).filter(
      (item) => !buscando || coincide(item.titulo, item.texto)
    ),
  }));
  const seccionesVisibles = seccionesContenido.filter((seccion) => seccion.items.length > 0);
  const totalResultados =
    preguntasVisibles.length + seccionesVisibles.reduce((suma, seccion) => suma + seccion.items.length, 0);

  const pagMisMensajes = usePaginacion(misMensajes, 5, []);

  // Navegación por secciones: lista lateral en escritorio, selector desplegable en móvil.
  const opciones = [
    { id: "faq", titulo: "Preguntas frecuentes", icono: HiOutlineQuestionMarkCircle },
    { id: "pasos", titulo: "Primeros pasos", icono: HiOutlineFlag },
    ...SECCIONES_INFO.map(({ clave, titulo, icono }) => ({ id: clave, titulo, icono })),
    { id: "manual", titulo: "Manual de usuario", icono: HiOutlineDownload },
    { id: "contacto", titulo: "Contacto y mis mensajes", icono: HiOutlineChatAlt2 },
  ];
  const activa = opciones.some((o) => o.id === seccion) ? seccion : "faq";
  // Con una búsqueda se muestran los resultados de todas las secciones; sin ella, solo la elegida.
  const ver = (id) => (buscando ? ["faq", "contacto"].includes(id) || seccionesVisibles.some((x) => x.clave === id) : activa === id);

  async function handleEnviar(e) {
    e.preventDefault();
    setErrorEnvio("");
    setEnviado(false);
    setEnviando(true);
    try {
      await crearTicketSoporte(token, mensaje);
      setEnviado(true);
      setMensaje("");
      cargarMisMensajes();
    } catch (err) {
      setErrorEnvio(err.message || "No se pudo enviar tu mensaje. Intenta de nuevo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="app-shell-page soporte-fondo">
      <AppTopbar />
      <main id="contenido-principal" tabIndex={-1} className="app-hero">

        <div className="app-content soporte-page">
          <BotonRegresar tono="oscuro" />

          <header className="soporte-hero">
            <span className="soporte-hero-kicker">CENTRO DE AYUDA</span>
            <h1 className="app-title">¿En qué te podemos ayudar?</h1>
            <p className="app-subtitle">
              Guías paso a paso por rol, preguntas frecuentes y un canal directo con soporte.
            </p>
          </header>

          <div className="soporte-buscador">
            <HiOutlineSearch size={18} aria-hidden="true" />
            <input
              type="search"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar en el Centro de ayuda"
              aria-label="Buscar en el Centro de ayuda"
            />
          </div>
          {buscando && (
            <p className="soporte-resultados">
              {totalResultados === 0
                ? "No se encontraron resultados para tu búsqueda."
                : `${totalResultados} ${totalResultados === 1 ? "resultado" : "resultados"}`}
            </p>
          )}

          <div className="soporte-layout">
          {!buscando && (
            <>
              <nav className="soporte-nav" aria-label="Secciones del Centro de ayuda">
                {opciones.map(({ id, titulo, icono: Icono }) => (
                  <button
                    key={id}
                    type="button"
                    className={`soporte-nav__item ${activa === id ? "soporte-nav__item--activo" : ""}`}
                    aria-current={activa === id ? "page" : undefined}
                    onClick={() => setSeccion(id)}
                  >
                    <Icono size={18} aria-hidden="true" />
                    <span>{titulo}</span>
                  </button>
                ))}
              </nav>
              <div className="soporte-selector">
                <label htmlFor="soporte-seccion">Ir a la sección</label>
                <div className="soporte-selector__caja">
                  <select id="soporte-seccion" value={activa} onChange={(e) => setSeccion(e.target.value)}>
                    {opciones.map((o) => (
                      <option key={o.id} value={o.id}>{o.titulo}</option>
                    ))}
                  </select>
                  <HiOutlineChevronDown size={18} aria-hidden="true" />
                </div>
              </div>
            </>
          )}
          <div className="soporte-panel">
          {/* Preguntas frecuentes */}
          {ver("faq") && preguntasVisibles.length > 0 && (
            <section className="soporte-card">
              <h2>Preguntas frecuentes</h2>
              <div className="soporte-faq-lista">
                {preguntasVisibles.map((item) => (
                  <PreguntaFAQ key={item.pregunta} item={item} />
                ))}
              </div>
            </section>
          )}

          {/* Primeros pasos (solo sin búsqueda) */}
          {ver("pasos") && (
          <section className="soporte-card soporte-card--guia">
            <h2>Primeros pasos</h2>
            <div className="soporte-tabs">
              {ORDEN_ROLES.map((rol) => {
                const Icono = GUIAS_POR_ROL[rol].icono;
                const activo = rol === rolActivo;
                return (
                  <button
                    key={rol}
                    type="button"
                    className={`soporte-tab ${activo ? "soporte-tab--activo" : ""}`}
                    style={activo ? { "--tab-color": GUIAS_POR_ROL[rol].color } : undefined}
                    onClick={() => setRolActivo(rol)}
                  >
                    <Icono size={18} />
                    {etiquetaRol(rol)}
                    {rol === rolUsuario && <span className="soporte-tab-tu">tú</span>}
                  </button>
                );
              })}
            </div>

            <ol className="soporte-guia" style={{ "--guia-color": guia.color }}>
              {pasos.map((paso, i) => (
                <li key={i}>
                  <span className="soporte-guia-num">{i + 1}</span>
                  <span>{paso}</span>
                </li>
              ))}
            </ol>
          </section>
          )}

          {/* Secciones informativas: siempre se muestran en la navegación, aunque estén vacías. */}
          {seccionesContenido.filter((x) => ver(x.clave)).map(({ clave, titulo, icono: Icono, items }) => (
            <section className="soporte-card soporte-card--informativa" key={clave}>
              <h2 className="soporte-info-titulo">
                <span className="soporte-info-icono"><Icono size={20} /></span> {titulo}
              </h2>
              {items.length > 0 ? (
                <dl className="soporte-info-lista">
                  {items.map((item) => (
                    <div className="soporte-info-item" key={item.id}>
                      <dt>{item.titulo}</dt>
                      <dd>{item.texto}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <p className="soporte-seccion-vacia">Esta sección todavía no tiene contenido publicado.</p>
              )}
            </section>
          ))}

          {/* Recursos fijos: solo si el administrador aún no cargó secciones propias */}
          {ver("recursos") && seccionesVisibles.length === 0 && (
          <section className="soporte-card">
            <h2>Más recursos</h2>
            <div className="soporte-recursos">
              <div className="soporte-recurso">
                <strong>Glosario</strong>
                <p>Qué significa "resolución verificada", "empresa activa", "batería" y otros términos de la plataforma.</p>
              </div>
              <div className="soporte-recurso">
                <strong>Buenas prácticas de seguridad</strong>
                <p>Usa contraseñas únicas, no compartas tu enlace de empresa y verifica siempre el remitente del correo.</p>
              </div>
              <div className="soporte-recurso">
                <strong>Novedades de la plataforma</strong>
                <p>Últimos cambios: límite de 3 cambios de resolución cada 5 días, planes conectados al pago, Centro de ayuda.</p>
              </div>
            </div>
          </section>

          )}

          {ver("manual") && (
          <section className="soporte-card soporte-manual">
            <div className="soporte-manual-icono">
              <HiOutlineDownload size={24} />
            </div>
            <div className="soporte-manual-texto">
              <h2>Manual de usuario</h2>
              <p>Guía completa del sistema en PDF. Estará disponible muy pronto.</p>
            </div>
            <button type="button" className="soporte-btn-descarga" disabled title="Aún no hay manual disponible">
              Descargar PDF
              <span className="soporte-badge-pronto">Próximamente</span>
            </button>
          </section>
          )}

          {ver("contacto") && (
          <>
          <section className="soporte-card soporte-card--contacto">
            <div className="soporte-contacto-texto">
              <div className="soporte-contacto-cabecera">
                <div className="soporte-contacto-icono" aria-hidden="true">
                  <HiOutlineChatAlt2 size={26} />
                </div>
                <h2>¿No encontraste la respuesta?</h2>
              </div>
              <p>
                Escríbenos directamente a{" "}
                <a className="soporte-link" href="mailto:centrodeayudamagnus@gmail.com">
                  <HiOutlineMail size={16} /> centrodeayudamagnus@gmail.com
                </a>{" "}
                o cuéntanos aquí tu problema:
              </p>
              {enviado && (
                <p className="soporte-exito" role="status">¡Gracias! Recibimos tu mensaje, te responderemos pronto. Si necesitas algo más, puedes escribir otro abajo.</p>
              )}
              {(
                <form onSubmit={handleEnviar} className="soporte-form">
                  <textarea
                    rows={4}
                    aria-label="Describe tu problema o duda"
                    aria-required="true"
                    placeholder="Describe tu problema o duda..."
                    value={mensaje}
                    onChange={(e) => {
                      setMensaje(e.target.value);
                      if (enviado) setEnviado(false);
                    }}
                    required
                  />
                  {errorEnvio && <p className="soporte-error">{errorEnvio}</p>}
                  <button type="submit" className="soporte-btn-primary" disabled={enviando}>
                    {enviando ? "Enviando…" : "Enviar"}
                  </button>
                </form>
              )}
            </div>
          </section>

          <section className="soporte-card">
            <h2>Mis mensajes</h2>
            {misMensajes.length === 0 ? (
              <p className="soporte-mensajes__vacio">Aún no has enviado mensajes al soporte.</p>
            ) : (
              <ul className="soporte-mensajes__lista">
                {pagMisMensajes.items.map((m) => {
                  const expandible = Boolean(m.respuesta) || m.mensaje.length > 90;
                  const abierta = abierto === m.id;
                  return (
                    <li className={`soporte-mensajes__item ${abierta ? "soporte-mensajes__item--abierto" : ""}`} key={m.id}>
                      <button
                        type="button"
                        className="soporte-mensajes__fila"
                        aria-expanded={expandible ? abierta : undefined}
                        disabled={!expandible}
                        onClick={() => setAbierto(abierta ? null : m.id)}
                      >
                        <span className="soporte-mensajes__texto">{m.mensaje}</span>
                        <span className="soporte-mensajes__meta">
                          <span className="soporte-mensajes__fecha">{formatearFechaMensaje(m.creadoEn)}</span>
                          <span className={`soporte-mensajes__chip soporte-mensajes__chip--${m.estado === "RESUELTO" ? "resuelto" : "pendiente"}`}>
                            {m.estado === "RESUELTO" ? "Resuelto" : "Pendiente"}
                          </span>
                          {expandible && (
                            <span className="soporte-mensajes__mas">{abierta ? "Ocultar" : m.respuesta ? "Ver respuesta" : "Ver más"}</span>
                          )}
                        </span>
                      </button>
                      {abierta && m.respuesta && (
                        <div className="soporte-mensajes__respuesta">
                          <strong>Respuesta del administrador</strong>
                          <p>{m.respuesta}</p>
                          <span className="soporte-mensajes__fecha">{formatearFechaMensaje(m.respondidoEn)}</span>
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}
            <div className="soporte-mensajes__paginacion">
              <Paginador paginacion={pagMisMensajes} />
            </div>
          </section>
          </>
          )}
          </div>
          </div>
        </div>
      </main>
    </div>
  );
}