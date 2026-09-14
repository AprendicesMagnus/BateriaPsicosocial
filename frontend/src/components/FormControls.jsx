import { useState } from "react";

export function TextField({ label, ...props }) {
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <input className="field__input" {...props} />
    </label>
  );
}

export function PasswordField({ label, ...props }) {
  const [visible, setVisible] = useState(false);
  return (
    <label className="field">
      <span className="field__label">{label}</span>
      <div className="field__password-wrap">
        <input
          className="field__input"
          type={visible ? "text" : "password"}
          {...props}
        />
        <button
          type="button"
          className="field__eye"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        >
          {visible ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M3 3l18 18M10.6 10.6a3 3 0 004.24 4.24M6.5 6.7C4.3 8.2 2.7 10 2 12c1.6 3.8 5.5 7 10 7 1.6 0 3.1-.4 4.4-1.1M9.9 5.2A9.9 9.9 0 0112 5c4.5 0 8.4 3.2 10 7-1 1.7-2 3-3.4 4.2"
                stroke="#6B7290"
                strokeWidth="1.6"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M2 12c1.6-3.8 5.5-7 10-7s8.4 3.2 10 7c-1.6 3.8-5.5 7-10 7s-8.4-3.2-10-7z"
                stroke="#6B7290"
                strokeWidth="1.6"
              />
              <circle cx="12" cy="12" r="3" stroke="#6B7290" strokeWidth="1.6" />
            </svg>
          )}
        </button>
      </div>
    </label>
  );
}

export function PrimaryButton({ children, loading, ...props }) {
  return (
    <button className="btn-primary" disabled={loading || props.disabled} {...props}>
      {loading ? "Procesando..." : children}
    </button>
  );
}

export function SecondaryButton({ children, ...props }) {
  return (
    <button type="button" className="btn-secondary" {...props}>
      {children}
    </button>
  );
}

export function FormMessage({ type = "error", children }) {
  if (!children) return null;
  return <div className={`form-message form-message--${type}`}>{children}</div>;
}

export function CodeInput({ value, onChange, length = 6 }) {
  function handleChange(e) {
    const digits = e.target.value.replace(/\D/g, "").slice(0, length);
    onChange(digits);
  }
  return (
    <input
      className="field__input field__input--code"
      inputMode="numeric"
      maxLength={length}
      value={value}
      onChange={handleChange}
      placeholder={"•".repeat(length)}
    />
  );
}
