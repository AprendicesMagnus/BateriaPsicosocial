// Reglas de RF01: mínimo 8 caracteres, mayúsculas, minúsculas y números.
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;

function isPasswordValid(password) {
  return typeof password === "string" && PASSWORD_REGEX.test(password);
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isEmailValid(email) {
  return typeof email === "string" && EMAIL_REGEX.test(email);
}

module.exports = { isPasswordValid, isEmailValid };
