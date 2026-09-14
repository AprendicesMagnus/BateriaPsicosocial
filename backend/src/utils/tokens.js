const jwt = require("jsonwebtoken");

const JWT_SECRET = process.env.JWT_SECRET || "dev-secret-change-me";

function generateVerificationCode() {
  // Código numérico de 6 dígitos, como en los mockups ("Código de Verificación").
  return String(Math.floor(100000 + Math.random() * 900000));
}

function signSessionToken(usuario) {
  return jwt.sign(
    { sub: usuario.id, rol: usuario.rol, email: usuario.email },
    JWT_SECRET,
    { expiresIn: "2h" }
  );
}

function signResetToken(usuario) {
  return jwt.sign(
    { sub: usuario.id, purpose: "reset_password" },
    JWT_SECRET,
    { expiresIn: "15m" }
  );
}

function verifyToken(token) {
  return jwt.verify(token, JWT_SECRET);
}

module.exports = {
  generateVerificationCode,
  signSessionToken,
  signResetToken,
  verifyToken,
};
