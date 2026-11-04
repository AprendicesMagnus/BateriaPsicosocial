import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const MARCA = "Magnus|SIG";
const TITULO_BASE = "Magnus|SIG — Batería de Riesgo Psicosocial";

// Título de la pestaña por ruta. La ruta se compara en minúsculas y sin barra final.
const TITULOS = {
  "/iniciar-sesion": "Iniciar sesión",
  "/crear-cuenta": "Crear cuenta",
  "/verificar-cuenta": "Verificar cuenta",
  "/olvide-contrasena": "Recuperar contraseña",
  "/verificar-codigo": "Verificar código",
  "/restablecer-contrasena": "Restablecer contraseña",
  "/cuestionario-estres": "Cuestionario de estrés",
  "/cuestionario-estresb": "Cuestionario de estrés",
  "/cuestionario-extralaboral": "Cuestionario extralaboral",
  "/cuestionario-extralaboralb": "Cuestionario extralaboral",
  "/cuestionario-intralaboral": "Cuestionario intralaboral",
  "/cuestionario-intralaboralb": "Cuestionario intralaboral",
  "/ficha-datos-generales": "Ficha de datos generales",
  "/ficha-datos-generalesb": "Ficha de datos generales",
  "/politica-de-datos": "Política de tratamiento de datos",
  "/inicio": "Inicio",
  "/dashboard": "Dashboard",
  "/pago": "Pago",
  "/catalogo": "Catálogo",
  "/reportes": "Reportes",
  "/respuestas": "Respuestas",
  "/perfil": "Mi perfil",
  "/soporte": "Soporte",
  "/mis-empresas": "Mis empresas",
  "/verificar-nit": "Verificar NIT",
  "/crear-empresa": "Crear empresa",
  "/panel": "Panel de administración",
};

// Rutas con parámetro (token o código): se comparan por prefijo y el parámetro no aparece en el título.
const TITULOS_POR_PREFIJO = [
  ["/responder/", "Responder evaluación"],
  ["/verificar-informe/", "Verificar informe"],
];

function tituloDeRuta(pathname) {
  const ruta = pathname.toLowerCase().replace(/\/+$/, "") || "/";
  const exacto = TITULOS[ruta];
  if (exacto) return `${exacto} — ${MARCA}`;
  const porPrefijo = TITULOS_POR_PREFIJO.find(([inicio]) => ruta.startsWith(inicio));
  if (porPrefijo) return `${porPrefijo[1]} — ${MARCA}`;
  return TITULO_BASE;
}

// Va dentro de <BrowserRouter>. No dibuja nada: solo actualiza document.title al cambiar de ruta.
export default function TituloPagina() {
  const { pathname } = useLocation();

  useEffect(() => {
    document.title = tituloDeRuta(pathname);
  }, [pathname]);

  return null;
}
