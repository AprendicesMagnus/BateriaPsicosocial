import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import Toast from "./Toast";

const CLAVE = "magnussing_bienvenida";
const FRASES = [
  "Qué bueno tenerte de vuelta.",
  "Que tengas una excelente jornada.",
  "Cuidar el bienestar de tu equipo empieza aquí.",
  "Cada paso cuenta para un entorno laboral más saludable.",
];

// Saludo corto tras iniciar sesión: "Buenos días, Cristian. Qué bueno tenerte de vuelta."
export default function BienvenidaLogin() {
  const { usuario } = useAuth();
  const [mensaje, setMensaje] = useState("");

  useEffect(() => {
    if (!usuario || usuario.esInvitado) return;
    if (sessionStorage.getItem(CLAVE) !== "1") return;
    sessionStorage.removeItem(CLAVE);

    const hora = new Date().getHours();
    const saludo = hora < 12 ? "Buenos días" : hora < 19 ? "Buenas tardes" : "Buenas noches";
    const primerNombre = (usuario.nombre || "").trim().split(/\s+/)[0].toLowerCase();
    const nombre = primerNombre.charAt(0).toUpperCase() + primerNombre.slice(1);
    const frase = FRASES[Math.floor(Math.random() * FRASES.length)];
    setMensaje(`${saludo}${nombre ? `, ${nombre}` : ""}. ${frase}`);
  }, [usuario]);

  useEffect(() => {
    if (!mensaje) return undefined;
    const espera = setTimeout(() => setMensaje(""), 5000);
    return () => clearTimeout(espera);
  }, [mensaje]);

  return mensaje ? <Toast mensaje={mensaje} tipo="exito" duracion={5000} /> : null;
}
