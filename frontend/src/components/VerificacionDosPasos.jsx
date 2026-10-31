import { useState } from "react";
import { verificarCodigoLogin, reenviarCodigoLogin } from "../api/auth";

export default function VerificacionDosPasos({ challenge, onSuccess, onCancelar }) {
  const [codigo, setCodigo] = useState("");
  const [confiar, setConfiar] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [reenviando, setReenviando] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  async function verificar(e) {
    e.preventDefault();
    setError("");
    setMensaje("");
    if (!/^\d{6}$/.test(codigo)) {
      setError("Ingresa el código de seis dígitos.");
      return;
    }
    setCargando(true);
    try {
      const resultado = await verificarCodigoLogin({
        challengeToken: challenge.challengeToken,
        codigo,
        confiarDispositivo: confiar,
      });
      onSuccess(resultado);
    } catch (err) {
      setError(err.message || "No se pudo verificar el código.");
    } finally {
      setCargando(false);
    }
  }

  async function reenviar() {
    setError("");
    setMensaje("");
    setReenviando(true);
    try {
      const resultado = await reenviarCodigoLogin(challenge.challengeToken);
      setMensaje(resultado.message || "Se envió un nuevo código.");
      setCodigo("");
    } catch (err) {
      setError(err.message || "No se pudo reenviar el código.");
    } finally {
      setReenviando(false);
    }
  }

  return (
    <div className="login-2fa">
      <div className="login-2fa__icon" aria-hidden="true">🔐</div>
      <h2>Verificación en dos pasos</h2>
      <p>Enviamos un código de seguridad a <strong>{challenge.email}</strong>. El código vence en cinco minutos.</p>
      <form className="auth-form" onSubmit={verificar}>
        <label className="field">
          <span className="field__label">Código de seguridad</span>
          <input
            className="field__input login-2fa__code"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            placeholder="000000"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))}
            autoFocus
          />
        </label>
        <label className="login-2fa__trust">
          <input type="checkbox" checked={confiar} onChange={(e) => setConfiar(e.target.checked)} />
          <span>Confiar en este dispositivo durante 4 horas</span>
        </label>
        {error && <div className="login-2fa__error" role="alert">{error}</div>}
        {mensaje && <div className="login-2fa__success" role="status">{mensaje}</div>}
        <button className="btn-primary" type="submit" disabled={cargando || codigo.length !== 6}>
          {cargando ? "Verificando..." : "Verificar y continuar"}
        </button>
        <button className="login-2fa__link" type="button" onClick={reenviar} disabled={reenviando}>
          {reenviando ? "Enviando..." : "Reenviar código"}
        </button>
        <button className="login-2fa__cancel" type="button" onClick={onCancelar}>Cancelar e ir al inicio de sesión</button>
      </form>
    </div>
  );
}
