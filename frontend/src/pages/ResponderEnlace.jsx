
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ConsentimientoInformado from "../components/ConsentimientoInformado";
import { FormMessage, PrimaryButton } from "../components/FormControls";
import { useAuth } from "../context/AuthContext";

import {
  CLAVE_ENLACE,
  fetchEnlacePublico,
  iniciarEnlace,
} from "../api/enlaces";

import {
  fetchEvaluaciones,
  fetchInstrumentosParticipante,
} from "../api/evaluaciones";

import { RUTAS } from "../hooks/useCuestionarioBackend";

import "../styles/auth.css";
import "../styles/ResponderEnlace.css";

function enlaceGuardado() {
  try {
    return localStorage.getItem(CLAVE_ENLACE);
  } catch {
    return null;
  }
}

export default function ResponderEnlace() {
  const { token: tokenEnlace } = useParams();
  const navigate = useNavigate();

  const { token, usuario, loading, iniciarSesion } = useAuth();

  const [info, setInfo] = useState(null);
  const [error, setError] = useState(null);
  const [acepta, setAcepta] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const [avance, setAvance] = useState(null);

  const yaEmpezo =
    Boolean(usuario?.esInvitado) &&
    enlaceGuardado() === tokenEnlace;

  useEffect(() => {
    let activo = true;

    fetchEnlacePublico(tokenEnlace)
      .then((datos) => {
        if (activo) setInfo(datos);
      })
      .catch((e) => {
        if (activo) setError(e.message);
      });

    return () => {
      activo = false;
    };
  }, [tokenEnlace]);

  useEffect(() => {
    if (loading || !yaEmpezo || !token) return;

    let activo = true;

    async function cargarAvance() {
      try {
        const evaluaciones = await fetchEvaluaciones(token);
        const evaluacionId = evaluaciones[0]?.id;

        if (!evaluacionId) {
          if (activo) setAvance({ evaluacionId: null, siguiente: null });
          return;
        }

        const instrumentos = await fetchInstrumentosParticipante(
          token,
          evaluacionId
        );

        const siguiente = instrumentos.find(
          (instrumento) => instrumento.estado !== "COMPLETADA"
        );

        if (activo) {
          setAvance({
            evaluacionId,
            siguiente: siguiente ? RUTAS[siguiente.codigo] : null,
          });
        }
      } catch (e) {
        if (activo) setError(e.message);
      }
    }

    cargarAvance();

    return () => {
      activo = false;
    };
  }, [loading, yaEmpezo, token]);

  async function comenzar() {
    setIniciando(true);
    setError(null);

    try {
      const res = await iniciarEnlace(tokenEnlace, acepta);

      localStorage.setItem(CLAVE_ENLACE, tokenEnlace);
      iniciarSesion(res.token, res.usuario);

      navigate("/ficha-datos-generales", {
        state: { evaluacionId: res.evaluacionId },
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setIniciando(false);
    }
  }

  let contenido;

  if (!info || (yaEmpezo && !avance)) {
    contenido = !error ? (
      <div className="enlace__cargando">
        <span className="enlace__spinner" />
        <p>Preparando tu evaluación...</p>
      </div>
    ) : null;
  } else if (yaEmpezo && !avance.siguiente) {
    contenido = (
      <section className="enlace__estado">
        <div className="enlace__icono enlace__icono--exito">✓</div>
        <p className="enlace__eyebrow">Evaluación finalizada</p>
        <h1>¡Gracias por participar!</h1>
        <p className="enlace__texto">
          Completaste todos los cuestionarios. Tus respuestas quedaron
          guardadas y ya las puede consultar
          {info.evaluadorNombre
            ? ` ${info.evaluadorNombre}`
            : " tu psicólogo"}.
          Puedes cerrar esta página.
        </p>
      </section>
    );
  } else if (yaEmpezo && avance) {
    contenido = (
      <section className="enlace__estado">
        <div className="enlace__icono">↗</div>
        <p className="enlace__eyebrow">Tu progreso</p>
        <h1>Continúa tu evaluación</h1>
        <p className="enlace__texto">
          Ya comenzaste a responder. Puedes continuar desde el cuestionario
          que quedó pendiente.
        </p>

        <PrimaryButton
          type="button"
          onClick={() =>
            navigate(avance.siguiente, {
              state: { evaluacionId: avance.evaluacionId },
            })
          }
        >
          Continuar evaluación
        </PrimaryButton>
      </section>
    );
  } else if (!info.activo || info.enUso) {
    contenido = (
      <section className="enlace__estado">
        <div className="enlace__icono enlace__icono--alerta">!</div>
        <p className="enlace__eyebrow">Estado del enlace</p>
        <h1>{info.nombre}</h1>

        <FormMessage type="error">
          {info.activo
            ? "Este enlace ya está siendo usado por otro paciente. Solicita uno nuevo a tu psicólogo."
            : "Este enlace ya fue cerrado. Solicita uno nuevo a tu psicólogo."}
        </FormMessage>
      </section>
    );
  } else {
    contenido = (
      <>
        <div className="enlace__presentacion">
          <p className="enlace__eyebrow">
            EVALUACIÓN · {info.nombre}
          </p>

          <h1>Bienvenido a tu evaluación</h1>

          <p className="enlace__texto">
            {info.evaluadorNombre
              ? `${info.evaluadorNombre} te invitó`
              : "Te invitaron"}{" "}
            a responder la Batería de Riesgo Psicosocial
            {info.organizacionNombre
              ? ` de ${info.organizacionNombre}`
              : ""}.
            Primero completarás tus datos generales y después los
            cuestionarios.
          </p>
        </div>

        <div className="enlace__privacidad">
          <span className="enlace__privacidad-icono">✓</span>
          <div>
            <strong>Tu información es importante</strong>
            <p>
              Tus respuestas deben ser tratadas con confidencialidad y
              conforme a las condiciones del consentimiento informado.
            </p>
          </div>
        </div>

        {usuario && !usuario.esInvitado && (
          <FormMessage type="error">
            Al comenzar, se cerrará la sesión de {usuario.email} en este
            navegador.
          </FormMessage>
        )}

        <div className="enlace__consentimiento">
          <ConsentimientoInformado
            acepta={acepta}
            onChange={setAcepta}
            onComenzar={comenzar}
            iniciando={iniciando}
          />
        </div>
      </>
    );
  }

  return (
    <main className="enlace-shell">
      <header className="enlace__header">
        <div
          className="sidebar__logo"
          onClick={() => navigate("/Inicio")}
          style={{ cursor: "pointer" }}
        >
          <img src="/logo oscu.png" alt="Magnus" style={{ height: 70, marginRight: "auto" }} />
        </div>

        <div className="enlace__confidencial">
          <span className="enlace__punto" />
          Evaluación confidencial
        </div>
      </header>

      <div className="enlace__contenedor">
        <div className="enlace__tarjeta">
          <FormMessage type="error">{error}</FormMessage>
          {contenido}
        </div>

        <footer className="enlace__footer">
          <p>Magnus | SIG · Gestión de Riesgo Psicosocial</p>
          <span>Resolución 2764 de 2022</span>
        </footer>
      </div>
    </main>
  );
}
