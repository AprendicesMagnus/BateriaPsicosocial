import { useState } from "react";
import { PrimaryButton, SecondaryButton, FormMessage } from "./FormControls";
import { ROLES_REGISTRO } from "../utils/roles";

// Pantalla rápida que se muestra cuando alguien entra con Google por primera vez.
// La cuenta NO se crea hasta que confirme un rol.
export default function SeleccionRolGoogle({ email, loading, error, onConfirmar, onCancelar }) {
  const [rol, setRol] = useState("");
  const [intento, setIntento] = useState(false);

  function confirmar() {
    setIntento(true);
    if (!rol) return;
    onConfirmar(rol);
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="rol-google-titulo"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.55)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "16px",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "16px",
          padding: "28px 24px",
          width: "100%",
          maxWidth: "400px",
          boxShadow: "0 20px 50px rgba(0,0,0,0.25)",
        }}
      >
        <h2 id="rol-google-titulo" style={{ textAlign: "center", margin: "0 0 8px" }}>
          Selecciona tu rol
        </h2>
        <p style={{ textAlign: "center", fontSize: "14px", margin: "0 0 16px" }}>
          Para terminar de crear tu cuenta{email ? ` (${email})` : ""}, elige cómo vas a usar la plataforma.
        </p>

        <FormMessage type="error">{error}</FormMessage>

        <label className="field" htmlFor="rol-google">
          <span className="field__label">Rol</span>
          <select
            id="rol-google"
            className={`field__input ${intento && !rol ? "field__input--invalid" : ""}`.trim()}
            value={rol}
            onChange={(e) => setRol(e.target.value)}
          >
            <option value="">Selecciona un rol</option>
            {ROLES_REGISTRO.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
          {intento && !rol && <span className="field__error">Selecciona un rol para continuar.</span>}
        </label>

        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "16px" }}>
          <PrimaryButton type="button" loading={loading} onClick={confirmar}>
            Continuar
          </PrimaryButton>
          <SecondaryButton type="button" onClick={onCancelar} disabled={loading}>
            Cancelar
          </SecondaryButton>
        </div>
      </div>
    </div>
  );
}
