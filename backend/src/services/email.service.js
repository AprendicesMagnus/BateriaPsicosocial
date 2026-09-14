const nodemailer = require("nodemailer");

const smtpConfigured = Boolean(process.env.SMTP_HOST);

let transporter = null;
if (smtpConfigured) {
  transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT || 587),
    secure: Number(process.env.SMTP_PORT) === 465,
    auth: process.env.SMTP_USER
      ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
      : undefined,
  });
}

async function sendVerificationCode({ to, nombre, codigo, tipo }) {
  const asunto =
    tipo === "RESET_PASSWORD"
      ? "Magnus|SIG - Código para restablecer tu contraseña"
      : "Magnus|SIG - Verifica tu cuenta";

  const texto =
    tipo === "RESET_PASSWORD"
      ? `Hola ${nombre}, tu código para restablecer la contraseña es: ${codigo}. Vence en 15 minutos.`
      : `Hola ${nombre}, tu código de verificación de cuenta es: ${codigo}. Vence en 15 minutos.`;

  if (!smtpConfigured) {
    // Modo desarrollo: sin credenciales SMTP, el código se registra en la consola
    // del backend para poder probar el flujo completo sin un servidor de correo real.
    console.log("\n----- [DEV] Envío de correo simulado -----");
    console.log(`Para: ${to}`);
    console.log(`Asunto: ${asunto}`);
    console.log(`Código: ${codigo}`);
    console.log("-------------------------------------------\n");
    return { simulated: true };
  }

  await transporter.sendMail({
    from: process.env.SMTP_FROM || "Magnus|SIG <no-reply@magnussig.local>",
    to,
    subject: asunto,
    text: texto,
  });

  return { simulated: false };
}

module.exports = { sendVerificationCode };
