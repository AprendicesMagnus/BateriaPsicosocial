import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { guardarMiResolucion } from "../api/perfil";
import { soloDigitos } from "../utils/validaciones";

// Ventana obligatoria: el Psicologo que aún no tiene número de resolución debe registrarlo
// antes de usar el sistema. Se monta una sola vez dentro de <BrowserRouter>.
export default function CompletarResolucion() {
  const { token, usuario, loading, actualizarUsuario, cerrarSesion } = useAuth();
  const [numero, setNumero] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  const debeCompletar = !loading && usuario?.rol === "EVALUADOR_SST" && !usuario?.numeroResolucion;
  if (!debeCompletar) return null;

  async function guardar(e) {
    e.preventDefault();
    if (!/^\d{6}$/.test(numero)) {
      setError("El número de resolución debe tener exactamente 6 dígitos.");
      return;
    }
    setGuardando(true);
    setError("");
    try {
      const res = await guardarMiResolucion(token, numero);
      actualizarUsuario(res.usuario);
    } catch (err) {
      setError(err.message || "No se pudo guardar el número de resolución.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resolucion-titulo"
      style={{ position: "fixed", inset: 0, zIndex: 3000, display: "flex", alignItems: "center", justifyContent: "center", padding: 16, background: "rgba(15, 23, 42, 0.75)" }}
    >
      <form
        onSubmit={guardar}
        noValidate
        style={{ width: "100%", maxWidth: 420, display: "flex", flexDirection: "column", gap: 14, padding: "28px 24px", borderRadius: 16, background: "#fff", color: "#12314b", boxShadow: "0 20px 50px rgba(0,0,0,0.3)" }}
      >
        <h2 id="resolucion-titulo" style={{ margin: 0, fontSize: 20 }}>
          Completa tu número de resolución
        </h2>
        <p style={{ margin: 0, fontSize: 14, color: "#475569" }}>
          Para seguir usando la plataforma como Psicologo, registra tu número de resolución (6 dígitos). Será verificado por el administrador.
        </p>

        <label className="field">
          <span className="field__label">Número de Resolución</span>
          <input
            className={`field__input ${error ? "field__input--invalid" : ""}`.trim()}
            inputMode="numeric"
            maxLength={6}
            placeholder="Ej. 123456"
            value={numero}
            onChange={(e) => setNumero(soloDigitos(e.target.value, 6))}
            autoFocus
          />
          {error && <span className="field__error">{error}</span>}
        </label>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button type="submit" className="btn-primary" style={{ width: "auto", padding: "10px 22px" }} disabled={guardando}>
            {guardando ? "Guardando..." : "Guardar"}
          </button>
          <button type="button" className="app-btn-secondary" onClick={cerrarSesion} disabled={guardando}>
            Cerrar sesión
          </button>
        </div>
      </form>
    </div>
  );
}
