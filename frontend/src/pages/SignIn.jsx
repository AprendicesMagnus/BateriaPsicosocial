import { useState, useEffect, useRef } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

import AuthLayout from "../components/AuthLayout";
import { rutaInicial } from "../utils/roles";
import {
  TextField,
  PasswordField,
  PrimaryButton,
  SecondaryButton,
  FormMessage
} from "../components/FormControls";

import SeleccionRolGoogle from "../components/SeleccionRolGoogle";
import { login, loginConGoogle } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { emailValido, normalizarEmail } from "../utils/validaciones";

// Client ID de Google Cloud.
const GOOGLE_CLIENT_ID =
  "615740449491-340ojlb2h90f13j4ut7u0rhtm2k90589.apps.googleusercontent.com";

// Carga el script de Google Identity Services.
function cargarScriptGoogle() {
  return new Promise((resolve, reject) => {
    // Si Google ya está cargado
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }

    // Si el script ya existe pero todavía está cargando
    const existente = document.getElementById("google-identity-script");

    if (existente) {
      existente.addEventListener("load", resolve);
      existente.addEventListener("error", reject);
      return;
    }

    // Crear el script
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

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tocados, setTocados] = useState({});
  const [intento, setIntento] = useState(false);

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingGoogle, setLoadingGoogle] = useState(false);

  // Referencia donde Google va a dibujar su botón.
  const googleButtonRef = useRef(null);

  // Datos de Google pendientes de que la persona elija su rol (cuenta nueva).
  const [googlePendiente, setGooglePendiente] = useState(null);
  const [errorRolGoogle, setErrorRolGoogle] = useState("");

  const { iniciarSesion } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const successMessage = location.state?.message;

  const marcar = (campo) => {
    setTocados((prev) => ({
      ...prev,
      [campo]: true
    }));
  };

  const errores = {
    email: !email
      ? "Este campo es obligatorio."
      : !emailValido(normalizarEmail(email))
      ? "Ingresa un correo válido."
      : "",

    password: !password
      ? "Este campo es obligatorio."
      : ""
  };

  const mostrarError = (campo) =>
    Boolean((tocados[campo] || intento) && errores[campo]);

  /*
   * ---------------------------------------------------------
   * LOGIN NORMAL
   * ---------------------------------------------------------
   */

  async function handleSubmit(e) {
    if (e) e.preventDefault();

    setError("");
    setIntento(true);

    const hayErrores = Object.keys(errores).some((campo) =>
      Boolean(errores[campo])
    );

    if (hayErrores) {
      setTimeout(() => {
        document
          .querySelector(".field__input--invalid")
          ?.focus();
      }, 0);

      return;
    }

    const correoNorm = normalizarEmail(email);

    setLoading(true);

    try {
      const data = await login({
        email: correoNorm,
        password
      });

      iniciarSesion(data.token, data.usuario);

      navigate(rutaInicial(data.usuario?.rol));
    } catch (err) {
      if (err.payload?.requiresVerification) {
        navigate("/verificar-cuenta", {
          state: {
            email: err.payload.email
          }
        });

        return;
      }

      setError(
        err.message || "No se pudo iniciar sesión."
      );
    } finally {
      setLoading(false);
    }
  }

  /*
   * ---------------------------------------------------------
   * RESPUESTA DE GOOGLE
   * ---------------------------------------------------------
   *
   * Google devuelve:
   *
   * response.credential
   *
   * Ese valor es el ID Token JWT que necesita
   * nuestro backend.
   */

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

      // Cuenta nueva: primero se pide el rol, todavía no se crea nada.
      if (data.requiereRol) {
        setGooglePendiente({
          credential: response.credential,
          email: data.email
        });
        return;
      }

      iniciarSesion(
        data.token,
        data.usuario
      );

      navigate(rutaInicial(data.usuario?.rol));
    } catch (err) {
      console.error(
        "Error iniciando sesión con Google:",
        err
      );

      setError(
        err.message ||
          "No se pudo iniciar sesión con Google."
      );
    } finally {
      setLoadingGoogle(false);
    }
  }

  async function confirmarRolGoogle(rol) {
    if (!googlePendiente) return;
    setErrorRolGoogle("");
    setLoadingGoogle(true);

    try {
      const data = await loginConGoogle({
        credential: googlePendiente.credential,
        rol
      });

      iniciarSesion(data.token, data.usuario);
      setGooglePendiente(null);
      navigate(rutaInicial(data.usuario?.rol));
    } catch (err) {
      setErrorRolGoogle(err.message || "No se pudo crear la cuenta con Google.");
    } finally {
      setLoadingGoogle(false);
    }
  }

  /*
   * ---------------------------------------------------------
   * CONFIGURAR GOOGLE
   * ---------------------------------------------------------
   *
   * Aquí usamos:
   *
   * google.accounts.id
   *
   * NO:
   *
   * google.accounts.oauth2
   *
   * porque nuestro backend necesita un ID Token.
   */

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

        /*
         * Inicializamos Google Identity Services.
         *
         * ux_mode: "popup"
         *
         * hace que el inicio de sesión se realice
         * mediante una ventana emergente.
         */
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredential,
          ux_mode: "popup"
        });

        /*
         * Limpiamos el contenedor por si React
         * vuelve a renderizar el componente.
         */
        googleButtonRef.current.innerHTML = "";

        /*
         * Google crea aquí su botón oficial.
         *
         * Este botón es el que abre correctamente
         * la ventana de selección de cuenta.
         */
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

  /*
   * ---------------------------------------------------------
   * INTERFAZ
   * ---------------------------------------------------------
   */

  return (
    <AuthLayout volverA="/">
      <div className="login-container">

        <img
          src="/logo oscu.png"
          alt="Magnus SIG"
          className="login-logo"
        />

        <h1>Inicio de Sesión</h1>

        <FormMessage type="success">
          {successMessage}
        </FormMessage>

        <FormMessage type="error">
          {error}
        </FormMessage>

        <form
          className="auth-form"
          onSubmit={handleSubmit}
          noValidate
        >

          <TextField
            label="Correo"
            type="email"
            maxLength={180}
            value={email}
            onChange={(e) =>
              setEmail(
                normalizarEmail(e.target.value)
              )
            }
            onBlur={() => marcar("email")}
            error={
              mostrarError("email")
                ? errores.email
                : ""
            }
            placeholder="Correo"
          />

          <PasswordField
            label="Contraseña"
            maxLength={72}
            value={password}
            onChange={(e) =>
              setPassword(
                e.target.value.slice(0, 72)
              )
            }
            onBlur={() => marcar("password")}
            error={
              mostrarError("password")
                ? errores.password
                : ""
            }
            placeholder="Contraseña"
          />

          <div className="auth-links">

            <span>
              ¿No tienes cuenta?{" "}

              <Link
                className="link-accent"
                to="/crear-cuenta"
              >
                Crea una cuenta
              </Link>
            </span>

            <Link
              className="link-accent"
              to="/olvide-contrasena"
            >
              ¿Olvidaste tu contraseña?
            </Link>

          </div>

          <PrimaryButton
            type="submit"
            loading={loading}
          >
            Iniciar Sesión
          </PrimaryButton>

          <div className="divider">
            <span>o</span>
          </div>

          {/*
           * -------------------------------------------------
           * BOTÓN OFICIAL DE GOOGLE
           * -------------------------------------------------
           *
           * Google lo dibuja dentro de este div.
           *
           * Al pulsarlo se abre el popup de Google.
           */}

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
      </div>

      {googlePendiente && (
        <SeleccionRolGoogle
          email={googlePendiente.email}
          loading={loadingGoogle}
          error={errorRolGoogle}
          onConfirmar={confirmarRolGoogle}
          onCancelar={() => {
            setGooglePendiente(null);
            setErrorRolGoogle("");
          }}
        />
      )}
    </AuthLayout>
  );
}