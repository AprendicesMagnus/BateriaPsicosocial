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
<<<<<<< HEAD
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/cuestionario-estres" element={<CuestionarioEstres />}/>
          
=======
          {/* TEMPORAL: sin ProtectedRoute para poder ver el diseño sin loguearse.
              Volver a envolver con <ProtectedRoute> cuando se termine de revisar. */}
          <Route path="/pago" element={<Checkout />} />
>>>>>>> 2773a46ea68b457a2f1b4a4574f859f9ddd4d40e
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
