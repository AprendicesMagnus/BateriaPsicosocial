import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/AuthLayout";
import {
  TextField,
  PasswordField,
  PrimaryButton,
  FormMessage
} from "../components/FormControls";
import { register, loginConGoogle } from "../api/auth";
import {
  TEXTO_AYUDA_PASSWORD,
  emailValido,
  filtrarNombrePersona,
  nombrePersonaValido,
  normalizarEmail,
  passwordValida,
} from "../utils/validaciones";

const GOOGLE_CLIENT_ID =
  "615740449491-340ojlb2h90f13j4ut7u0rhtm2k90589.apps.googleusercontent.com";

function cargarScriptGoogle() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }

    const existente = document.getElementById("google-identity-script");

    if (existente) {
      existente.addEventListener("load", resolve);
      existente.addEventListener("error", reject);
      return;
    }

    const script = document.createElement("script");

    script.id = "google-identity-script";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;

    script.onload = resolve;
    script.onerror = reject;

    document.head.appendChild(script);
  });
}

export default function CreateAccount() {
  const [form, setForm] = useState({
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    confirmPassword: ""
  });

  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingGoogle, setLoadingGoogle] = useState(false);

  const googleButtonRef = useRef(null);

  const navigate = useNavigate();

  const marcar = (campo) => {
    setTocados((prev) => ({ ...prev, [campo]: true }));
  };

  const errores = {
    nombre: !form.nombre
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(form.nombre.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",

    apellido: !form.apellido
      ? "Este campo es obligatorio."
      : !nombrePersonaValido(form.apellido.trim(), 100)
      ? "Solo letras y espacios (mínimo 2 caracteres)."
      : "",

    email: !form.email
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(form.email))
      ? "Ingresa un correo válido."
      : "",

    password: !form.password
      ? "Este campo es obligatorio."
      : !passwordValida(form.password)
      ? TEXTO_AYUDA_PASSWORD
      : "",

    confirmPassword: !form.confirmPassword
      ? "Este campo es obligatorio."
      : form.password !== form.confirmPassword
      ? "Las contraseñas no coinciden."
      : ""
  };

  const mostrarError = (campo) =>
    Boolean((tocados[campo] || intento) && errores[campo]);

  async function handleSubmit(e) {
    if (e) e.preventDefault();

    setError("");
    setIntento(true);

    const hayErrores = Object.keys(errores).some((campo) =>
      Boolean(errores[campo])
    );

    if (hayErrores) {
      setTimeout(() => {
        document.querySelector(".field__input--invalid")?.focus();
      }, 0);

      return;
    }

    const nomTrim = form.nombre.trim();
    const apeTrim = form.apellido.trim();
    const correoNorm = normalizarEmail(form.email);

    setLoading(true);

    try {
      await register({
        nombre: nomTrim,
        apellido: apeTrim,
        email: correoNorm,
        password: form.password
      });

      navigate("/Inicio", { state: { email: correoNorm } });
    } catch (err) {
      setError(err.message || "No se pudo crear la cuenta.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleCredential(response) {
    setError("");
    setLoadingGoogle(true);

    try {
      if (!response?.credential) {
        throw new Error(
          "Google no devolvió las credenciales necesarias."
        );
      }

      const data = await loginConGoogle({
        credential: response.credential
      });

      navigate("/Inicio");
    } catch (err) {
      console.error(
        "Error creando cuenta con Google:",
        err
      );

      setError(
        err.message ||
          "No se pudo crear la cuenta con Google."
      );
    } finally {
      setLoadingGoogle(false);
    }
  }

  useEffect(() => {
    let cancelado = false;

    async function configurarGoogle() {
      try {
        await cargarScriptGoogle();

        if (
          cancelado ||
          !googleButtonRef.current ||
          !window.google?.accounts?.id
        ) {
          return;
        }

        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredential,
          ux_mode: "popup"
        });

        googleButtonRef.current.innerHTML = "";

        window.google.accounts.id.renderButton(
          googleButtonRef.current,
          {
            type: "standard",
            theme: "outline",
            size: "large",
            text: "continue_with",
            shape: "rectangular",
            logo_alignment: "left",
            width: 296,
            locale: "es"
          }
        );
      } catch (err) {
        console.error(
          "Error cargando Google Identity Services:",
          err
        );

        if (!cancelado) {
          setError(
            "No se pudo cargar el inicio de sesión de Google."
          );
        }
      }
    }

    configurarGoogle();

    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <AuthLayout illustration="network">
      <img
        src="/logo oscu.png"
        alt="Magnus SIG"
        className="login-logo"
      />

      <h1 style={{ textAlign: "center" }}>
        Crear Cuenta
      </h1>

      <FormMessage type="error">
        {error}
      </FormMessage>

      <form
        className="auth-form"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="form-row">
          <TextField
            label="Nombre"
            maxLength={100}
            value={form.nombre}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                nombre: filtrarNombrePersona(
                  e.target.value,
                  100
                )
              }))
            }
            onBlur={() => marcar("nombre")}
            error={
              mostrarError("nombre")
                ? errores.nombre
                : ""
            }
            placeholder="Nombre"
          />

          <TextField
            label="Apellido"
            maxLength={100}
            value={form.apellido}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                apellido: filtrarNombrePersona(
                  e.target.value,
                  100
                )
              }))
            }
            onBlur={() => marcar("apellido")}
            error={
              mostrarError("apellido")
                ? errores.apellido
                : ""
            }
            placeholder="Apellido"
          />
        </div>

        <TextField
          label="Correo electrónico"
          type="email"
          maxLength={180}
          value={form.email}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              email: normalizarEmail(e.target.value)
            }))
          }
          onBlur={() => marcar("email")}
          error={
            mostrarError("email")
              ? errores.email
              : ""
          }
          placeholder="nombre@empresa.com"
        />

        <PasswordField
          label="Contraseña"
          maxLength={72}
          value={form.password}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              password: e.target.value.slice(0, 72)
            }))
          }
          onBlur={() => marcar("password")}
          error={
            mostrarError("password")
              ? errores.password
              : ""
          }
          placeholder="••••••••"
        />

        <PasswordField
          label="Confirmar contraseña"
          maxLength={72}
          value={form.confirmPassword}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              confirmPassword: e.target.value.slice(0, 72)
            }))
          }
          onBlur={() => marcar("confirmPassword")}
          error={
            mostrarError("confirmPassword")
              ? errores.confirmPassword
              : ""
          }
          placeholder="••••••••"
        />

        <div className="auth-links">
          <span>
            ¿Ya tienes cuenta?{" "}

            <Link
              className="link-accent"
              to="/iniciar-sesion"
            >
              Inicia sesión
            </Link>
          </span>
        </div>

        <PrimaryButton
          type="submit"
          loading={loading}
        >
          Crear Cuenta
        </PrimaryButton>

        <div className="divider">
          <span>o</span>
        </div>

        <div
          ref={googleButtonRef}
          style={{
            width: "100%",
            minHeight: "44px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center"
          }}
        />

        {loadingGoogle && (
          <div
            style={{
              textAlign: "center",
              marginTop: "8px",
              fontSize: "13px"
            }}
          >
            Conectando con Google...
          </div>
        )}
      </form>
    </AuthLayout>
  );
}