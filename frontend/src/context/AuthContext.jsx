import { createContext, useContext, useEffect, useState } from "react";
import { fetchMe } from "../api/auth";

const AuthContext = createContext(null);
const STORAGE_KEY = "magnussing_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [usuario, setUsuario] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetchMe(token)
      .then((data) => setUsuario(data.usuario))
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  function iniciarSesion(nuevoToken, nuevoUsuario) {
    localStorage.setItem(STORAGE_KEY, nuevoToken);
    // Un inicio de sesión normal ya no es el de un paciente del enlace
    if (!nuevoUsuario?.esInvitado) localStorage.removeItem("magnussing_enlace");
    setToken(nuevoToken);
    setUsuario(nuevoUsuario);
  }

  function cerrarSesion() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUsuario(null);
  }

  return (
    <AuthContext.Provider
      value={{ token, usuario, loading, iniciarSesion, cerrarSesion }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
