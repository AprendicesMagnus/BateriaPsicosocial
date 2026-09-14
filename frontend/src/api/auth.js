import request from "./client";

export const register = (data) => request("/auth/register", { method: "POST", body: data });

export const verifyEmail = (data) =>
  request("/auth/verify-email", { method: "POST", body: data });

export const resendCode = (data) =>
  request("/auth/resend-code", { method: "POST", body: data });

export const login = (data) => request("/auth/login", { method: "POST", body: data });

export const forgotPassword = (data) =>
  request("/auth/forgot-password", { method: "POST", body: data });

export const verifyResetCode = (data) =>
  request("/auth/verify-reset-code", { method: "POST", body: data });

export const resetPassword = (data) =>
  request("/auth/reset-password", { method: "POST", body: data });

export const fetchMe = (token) => request("/auth/me", { token });
