/**
 * Página pública del enlace que el psicólogo comparte con sus pacientes (/responder/:token).
 *
 * - Paciente nuevo: ve el consentimiento informado y pulsa "Comenzar". El backend crea un
 *   usuario invitado y le abre sesión; empieza por la Ficha de datos generales (que dice quién es)
 *   y sigue con los demás cuestionarios.
 * - Paciente que ya empezó en este navegador: ve "Continuar" hacia el cuestionario pendiente,
 *   o el mensaje de agradecimiento si ya terminó toda la batería.
 */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import { FormMessage, PrimaryButton } from "../components/FormControls";
import { useAuth } from "../context/AuthContext";
import { CLAVE_ENLACE, fetchEnlacePublico, iniciarEnlace } from "../api/enlaces";
import { fetchEvaluaciones, fetchInstrumentosParticipante } from "../api/evaluaciones";
import { RUTAS } from "../hooks/useCuestionarioBackend";

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
  // Avance del paciente que ya empezó: { evaluacionId, siguiente } (siguiente = null si terminó)
  const [avance, setAvance] = useState(null);

  const yaEmpezo = Boolean(usuario?.esInvitado) && enlaceGuardado() === tokenEnlace;

  useEffect(() => {
    fetchEnlacePublico(tokenEnlace)
      .then(setInfo)
      .catch((e) => setError(e.message));
  }, [tokenEnlace]);

  // Si el paciente ya empezó en este navegador, se busca su siguiente cuestionario pendiente
  useEffect(() => {
    if (loading || !yaEmpezo || !token) return;
    fetchEvaluaciones(token)
      .then(async (evs) => {
        const evaluacionId = evs[0]?.id;
        if (!evaluacionId) return;
        const instrumentos = await fetchInstrumentosParticipante(token, evaluacionId);
        const siguiente = instrumentos.find((i) => i.estado !== "COMPLETADA");
        setAvance({ evaluacionId, siguiente: siguiente ? RUTAS[siguiente.codigo] : null });
      })
      .catch((e) => setError(e.message));
  }, [loading, yaEmpezo, token]);

  async function comenzar() {
    setIniciando(true);
    setError(null);
    try {
      const res = await iniciarEnlace(tokenEnlace, acepta);
      localStorage.setItem(CLAVE_ENLACE, tokenEnlace);
      iniciarSesion(res.token, res.usuario);
      // Primero la Ficha de datos: ahí el paciente dice quién es
      navigate("/ficha-datos-generales", { state: { evaluacionId: res.evaluacionId } });
    } catch (e) {
      setError(e.message);
    } finally {
      setIniciando(false);
    }
  }

  let contenido;
  if (!info || (yaEmpezo && !avance)) {
    contenido = !error && <p className="auth-subtitle">Cargando…</p>;
  } else if (yaEmpezo && avance && !avance.siguiente) {
    contenido = (
      <>
        <h1>¡Gracias!</h1>
        <p className="auth-subtitle">
          Completaste todos los cuestionarios. Tus respuestas quedaron guardadas y ya las puede ver
          {info.evaluadorNombre ? ` ${info.evaluadorNombre}` : " tu psicólogo"}. Puedes cerrar esta página.
        </p>
      </>
    );
  } else if (yaEmpezo && avance) {
    contenido = (
      <>
        <h1>{info.nombre}</h1>
        <p className="auth-subtitle">Ya empezaste a responder. Continúa donde quedaste.</p>
        <PrimaryButton
          type="button"
          onClick={() => navigate(avance.siguiente, { state: { evaluacionId: avance.evaluacionId } })}
        >
          Continuar
        </PrimaryButton>
      </>
    );
  } else if (!info.activo || info.enUso) {
    // Cada enlace es para un solo paciente y se cierra cuando termina la batería
    contenido = (
      <>
        <h1>{info.nombre}</h1>
        <FormMessage type="error">
          {info.activo
            ? "Este enlace ya está siendo usado por otro paciente. Pide un enlace nuevo a tu psicólogo."
            : "Este enlace ya fue cerrado. Pide un enlace nuevo a tu psicólogo."}
        </FormMessage>
      </>
    );
  } else {
    contenido = (
      <>
        <h1>{info.nombre}</h1>
        <p className="auth-subtitle">
          {info.evaluadorNombre ? `${info.evaluadorNombre} te invitó` : "Te invitaron"} a responder la
          Batería de riesgo psicosocial
          {info.organizacionNombre ? ` (${info.organizacionNombre})` : ""}. No necesitas crear una cuenta.
          Primero llenarás tus datos generales y luego los cuestionarios; tus respuestas se guardan a medida
          que avanzas.
        </p>

        {usuario && !usuario.esInvitado && (
          <FormMessage type="error">
            Al comenzar se cerrará la sesión de {usuario.email} en este navegador.
          </FormMessage>
        )}

        <label style={{ display: "flex", gap: 10, alignItems: "flex-start", margin: "16px 0", lineHeight: 1.4 }}>
          <input type="checkbox" checked={acepta} onChange={(e) => setAcepta(e.target.checked)} />
          <span>
            Acepto el consentimiento informado: autorizo el uso de mis respuestas para la evaluación de
            factores de riesgo psicosocial. La información es confidencial y solo la consulta el psicólogo
            responsable.
          </span>
        </label>

        <PrimaryButton type="button" onClick={comenzar} loading={iniciando} disabled={!acepta || iniciando}>
          Comenzar
        </PrimaryButton>
      </>
    );
  }

  return (
    <AuthLayout>
      <FormMessage type="error">{error}</FormMessage>
      {contenido}
    </AuthLayout>
  );
}
