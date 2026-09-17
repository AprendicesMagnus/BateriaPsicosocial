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
import Panel from "./pages/Panel";
import Dashboard from "./pages/Dashboard";
import CuestionarioEstres from "./pages/CuestionarioEstres";
import CuestionarioExtralaboral from "./pages/CuestionarioExtralaboral";
import CuestionarioIntralaboral from "./pages/CuestionarioIntralaboral";

import CuestionarioEstresB from "./pages/CuestionarioEstresB";
import CuestionarioExtralaboralB from "./pages/CuestionarioExtralaboralB";
import CuestionarioIntralaboralB from "./pages/CuestionarioIntralaboralB";

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
          {/* preguntas tipo a. */}
          <Route path="/cuestionario-estres" element={<CuestionarioEstres />} />
          <Route path="/cuestionario-extralaboral" element={<CuestionarioExtralaboral />} />
          <Route path="/cuestionario-intralaboral" element={<CuestionarioIntralaboral />} />

{/* preguntas tipo B. */}
          <Route path="/cuestionario-estresB" element={<CuestionarioEstresB />} />
          <Route path="/cuestionario-extralaboralB" element={<CuestionarioExtralaboralB />} />
          <Route path="/cuestionario-intralaboralB" element={<CuestionarioIntralaboralB />} />
          {/* TEMPORAL: sin ProtectedRoute para poder ver el diseño sin loguearse.
              Volver a envolver con <ProtectedRoute> cuando se termine de revisar. */}
          <Route path="/pago" element={<Checkout />} />

          <Route path="/dashboard" element={<Dashboard />} />

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