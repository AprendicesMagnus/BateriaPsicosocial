import { useId, useState } from "react";

export function TextField({ label, error, invalid, id, className, ...props }) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;
  const isInvalid = Boolean(invalid || error);

  return (
    <label className="field" htmlFor={inputId}>
      {label && <span className="field__label">{label}</span>}
      <input
        id={inputId}
        className={`field__input ${isInvalid ? "field__input--invalid" : ""} ${className || ""}`.trim()}
        aria-invalid={isInvalid ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error && (
        <span className="field__error" id={errorId}>
          {error}
        </span>
      )}
    </label>
  );
}

export function PasswordField({ label, error, invalid, id, className, ...props }) {
  const [visible, setVisible] = useState(false);
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;
  const isInvalid = Boolean(invalid || error);

  return (
    <label className="field" htmlFor={inputId}>
      {label && <span className="field__label">{label}</span>}
      <div className="field__password-wrap">
        <input
          id={inputId}
          className={`field__input ${isInvalid ? "field__input--invalid" : ""} ${className || ""}`.trim()}
          type={visible ? "text" : "password"}
          aria-invalid={isInvalid ? "true" : "false"}
          aria-describedby={error ? errorId : undefined}
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
      {error && (
        <span className="field__error" id={errorId}>
          {error}
        </span>
      )}
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

export function SecondaryButton({ children, loading, ...props }) {
  return (
    <button type="button" className="btn-secondary" disabled={loading || props.disabled} {...props}>
      {children}
    </button>
  );
}

export function FormMessage({ type = "error", children }) {
  if (!children) return null;
  return <div className={`form-message form-message--${type}`}>{children}</div>;
}

export function CodeInput({ value, onChange, length = 6, error, invalid, id, onBlur, ...props }) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;
  const isInvalid = Boolean(invalid || error);

  return (
    <label className="field" htmlFor={inputId}>
      <input
        id={inputId}
        className={`field__input field__input--code ${isInvalid ? "field__input--invalid" : ""}`.trim()}
        inputMode="numeric"
        maxLength={length}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        placeholder={"•".repeat(length)}
        aria-invalid={isInvalid ? "true" : "false"}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error && (
        <span className="field__error" id={errorId} style={{ textAlign: "center" }}>
          {error}
        </span>
      )}
    </label>
  );
}