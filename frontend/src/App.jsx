import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import SignIn from "./pages/SignIn";
import RestriccionRolLimitado from "./components/RestriccionRolLimitado";
import CierreInactividad from "./components/CierreInactividad";
import TituloPagina from "./components/TituloPagina";
import CompletarResolucion from "./components/CompletarResolucion";
import BienvenidaLogin from "./components/BienvenidaLogin";

// Las páginas se cargan bajo demanda para que el bundle inicial sea más liviano.
const CreateAccount = lazy(() => import("./pages/CreateAccount"));
const VerifyCode = lazy(() => import("./pages/VerifyCode"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Checkout = lazy(() => import("./pages/Checkout"));
const Catalogo = lazy(() => import("./pages/Catalogo"));
const Reportes = lazy(() => import("./pages/Reportes"));
const Respuestas = lazy(() => import("./pages/Respuestas"));
const Perfil = lazy(() => import("./pages/Perfil"));
const Soporte = lazy(() => import("./pages/Soporte"));
const VerificarNit = lazy(() => import("./pages/VerificarNit"));
const MisEmpresas = lazy(() => import("./pages/MisEmpresas"));
const CrearEmpresa = lazy(() => import("./pages/Crearempresa"));
const Panel = lazy(() => import("./pages/Panel"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const CuestionarioEstres = lazy(() => import("./pages/CuestionarioEstres"));
const CuestionarioExtralaboral = lazy(() => import("./pages/CuestionarioExtralaboral"));
const CuestionarioIntralaboral = lazy(() => import("./pages/CuestionarioIntralaboral"));
const CuestionarioEstresB = lazy(() => import("./pages/CuestionarioEstresB"));
const CuestionarioExtralaboralB = lazy(() => import("./pages/CuestionarioExtralaboralB"));
const CuestionarioIntralaboralB = lazy(() => import("./pages/CuestionarioIntralaboralB"));
const FichaDatosGenerales = lazy(() => import("./pages/Fichadatosgenerales"));
const Inicio = lazy(() => import("./pages/Inicio"));
const ResponderEnlace = lazy(() => import("./pages/ResponderEnlace"));
const VerificarInforme = lazy(() => import("./pages/VerificarInforme"));
const PoliticaDatos = lazy(() => import("./pages/PoliticaDatos"));




export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <TituloPagina />
        <CierreInactividad />
        <CompletarResolucion />
        <BienvenidaLogin />
        <RestriccionRolLimitado>
        <a href="#contenido-principal" className="skip-link">Saltar al contenido</a>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/iniciar-sesion" element={<SignIn />} />
          <Route path="/crear-cuenta" element={<CreateAccount />} />
          <Route path="/verificar-cuenta" element={<VerifyCode mode="register" />} />
          <Route path="/olvide-contrasena" element={<ForgotPassword />} />
          <Route path="/verificar-codigo" element={<VerifyCode mode="reset" />} />
          <Route path="/restablecer-contrasena" element={<ResetPassword />} />
          

          {/* Preguntas tipo A */}
          <Route path="/cuestionario-estres" element={<CuestionarioEstres />} />
          <Route path="/cuestionario-extralaboral" element={<CuestionarioExtralaboral />} />
          <Route path="/cuestionario-intralaboral" element={<CuestionarioIntralaboral />} />

          {/* Preguntas tipo B */}
          <Route path="/cuestionario-estresB" element={<CuestionarioEstresB />} />
          <Route path="/cuestionario-extralaboralB" element={<CuestionarioExtralaboralB />} />
          <Route path="/cuestionario-intralaboralB" element={<CuestionarioIntralaboralB />} />

          <Route path="/ficha-datos-generales" element={<FichaDatosGenerales />} />
          <Route path="/ficha-datos-generalesB" element={<FichaDatosGenerales />} />

          {/* Enlace público que el psicólogo comparte con sus pacientes (responden sin cuenta) */}
          <Route path="/responder/:token" element={<ResponderEnlace />} />
          <Route path="/verificar-informe/:codigo" element={<VerificarInforme />} />
          <Route path="/politica-de-datos" element={<PoliticaDatos />} />

           {/* apartado inicial tras iniciar sesion (protegido) */}
          <Route
            path="/Inicio"
            element={
              <ProtectedRoute>
                <Inicio />
              </ProtectedRoute>
            }
          />


          {/* portal de informacion en la web */}
          <Route path="/dashboard" element={<ProtectedRoute> <Dashboard /> </ProtectedRoute> } />

          <Route path="/pago"  element={<ProtectedRoute> <Checkout /> </ProtectedRoute> } />
          <Route path="/catalogo" element={<ProtectedRoute> <Catalogo /> </ProtectedRoute> } />
          <Route
            path="/reportes"
            element={
              <ProtectedRoute>
                <Reportes />
              </ProtectedRoute>
            }
          />
          {/* Respuestas individuales (confidencial): solo administrador y evaluador SST */}
          <Route
            path="/respuestas"
            element={
              <ProtectedRoute roles={["SUPER_ADMINISTRADOR", "EVALUADOR_SST", "RESPONSABLE_SST"]}>
                <Respuestas />
              </ProtectedRoute>
            }
          />
          <Route path="/perfil" element={<ProtectedRoute> <Perfil /> </ProtectedRoute>} />
          <Route path="/soporte" element={<ProtectedRoute> <Soporte /> </ProtectedRoute>} />
          <Route path="/mis-empresas" element={<ProtectedRoute> <MisEmpresas /> </ProtectedRoute>} />
          <Route path="/verificar-nit" element={<VerificarNit />} />
          <Route path="/crear-empresa" element={<CrearEmpresa />} />
          <Route
            path="/panel"
            element={
              <ProtectedRoute roles={["SUPER_ADMINISTRADOR"]}>
                <Panel />
              </ProtectedRoute>
            }
          />
          {/* Cualquier URL que no exista vuelve a la página principal */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </RestriccionRolLimitado>
      </BrowserRouter>
    </AuthProvider>
  );
}