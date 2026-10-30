import request from "./client";

export const register = (data) => request("/auth/register", { method: "POST", body: data });

export const verifyEmail = (data) =>
  request("/auth/verify-email", { method: "POST", body: data });

export const resendCode = (data) =>
  request("/auth/resend-code", { method: "POST", body: data });

export const login = (data) => request("/auth/login", { method: "POST", body: data });

export const loginConGoogle = (data) => request("/auth/google", { method: "POST", body: data });

export const forgotPassword = (data) =>
  request("/auth/forgot-password", { method: "POST", body: data });

export const verifyResetCode = (data) =>
  request("/auth/verify-reset-code", { method: "POST", body: data });

export const resetPassword = (data) =>
  request("/auth/reset-password", { method: "POST", body: data });

export const fetchMe = (token) => request("/auth/me", { token });
export const verificarCodigoLogin = (data) =>
  request("/auth/verify-login-code", { method: "POST", body: data });

export const reenviarCodigoLogin = (challengeToken) =>
  request("/auth/resend-login-code", { method: "POST", body: { challengeToken } });

export const listarSesionesActivas = (token) => request("/auth/sessions", { token });
export const cerrarSesionActiva = (token, id) =>
  request(`/auth/sessions/${id}`, { method: "DELETE", token });
export const cerrarOtrasSesiones = (token) =>
  request("/auth/sessions/close-others", { method: "POST", token });
export const cerrarSesionServidor = (token) =>
  request("/auth/logout", { method: "POST", token });
export const revocarDispositivosConfiables = (token) =>
  request("/auth/trusted-devices", { method: "DELETE", token });
