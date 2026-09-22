import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Landing from "./pages/Landing";
import SignIn from "./pages/SignIn";
import CreateAccount from "./pages/CreateAccount";
import VerifyCode from "./pages/VerifyCode";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Checkout from "./pages/Checkout";
import Reportes from "./pages/Reportes";
import Perfil from "./pages/Perfil";
import VerificarNit from "./pages/VerificarNit";
import CrearEmpresa from "./pages/Crearempresa";
import Panel from "./pages/Panel";
import Dashboard from "./pages/Dashboard";
import CuestionarioEstres from "./pages/CuestionarioEstres";
import CuestionarioExtralaboral from "./pages/CuestionarioExtralaboral";
import CuestionarioIntralaboral from "./pages/CuestionarioIntralaboral";

import CuestionarioEstresB from "./pages/CuestionarioEstresB";
import CuestionarioExtralaboralB from "./pages/CuestionarioExtralaboralB";
import CuestionarioIntralaboralB from "./pages/CuestionarioIntralaboralB";
import FichaDatosGenerales from "./pages/Fichadatosgenerales";
import Inicio from "./pages/Inicio";



export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
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

          <Route
            path="/pago"
            element={
              <ProtectedRoute>
                <Checkout />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reportes"
            element={
              <ProtectedRoute>
                <Reportes />
              </ProtectedRoute>
            }
          />
          <Route path="/perfil" element={<Perfil />} />
          <Route path="/verificar-nit" element={<VerificarNit />} />
          <Route path="/crear-empresa" element={<CrearEmpresa />} />
          <Route
            path="/panel"
            element={
              <ProtectedRoute>
                <Panel />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}