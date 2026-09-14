const bcrypt = require("bcryptjs");
const prisma = require("../config/prisma");
const { isPasswordValid, isEmailValid } = require("../utils/password");
const {
  generateVerificationCode,
  signSessionToken,
  signResetToken,
  verifyToken,
} = require("../utils/tokens");
const { sendVerificationCode } = require("../services/email.service");

const CODE_TTL_MINUTES = 15;
const MAX_INTENTOS = 5;
const BLOQUEO_MINUTOS = 15;

function codeExpiryDate() {
  return new Date(Date.now() + CODE_TTL_MINUTES * 60 * 1000);
}

async function crearYEnviarCodigo(usuario, tipo) {
  const codigo = generateVerificationCode();
  await prisma.codigoVerificacion.create({
    data: {
      usuarioId: usuario.id,
      codigo,
      tipo,
      expiraEn: codeExpiryDate(),
    },
  });
  await sendVerificationCode({
    to: usuario.email,
    nombre: usuario.nombre,
    codigo,
    tipo,
  });
}

function publicUser(usuario) {
  return {
    id: usuario.id,
    nombre: usuario.nombre,
    apellido: usuario.apellido,
    email: usuario.email,
    rol: usuario.rol,
    emailVerificado: usuario.emailVerificado,
  };
}

// POST /api/auth/register
async function register(req, res) {
  const { nombre, apellido, email, password } = req.body;

  if (!nombre || !apellido || !email || !password) {
    return res.status(400).json({ error: "Todos los campos son obligatorios." });
  }
  if (!isEmailValid(email)) {
    return res.status(400).json({ error: "El formato del correo electrónico no es válido." });
  }
  if (!isPasswordValid(password)) {
    return res.status(400).json({
      error:
        "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
    });
  }

  const existente = await prisma.usuario.findUnique({ where: { email } });
  if (existente) {
    return res.status(409).json({ error: "Ya existe una cuenta registrada con este correo." });
  }

  const passwordHash = await bcrypt.hash(password, 10);
  const usuario = await prisma.usuario.create({
    data: { nombre, apellido, email, passwordHash },
  });

  await crearYEnviarCodigo(usuario, "VERIFICACION_EMAIL");

  return res.status(201).json({
    message: "Cuenta creada. Revisa tu correo para verificar tu cuenta.",
    email: usuario.email,
  });
}

// POST /api/auth/verify-email
async function verifyEmail(req, res) {
  const { email, codigo } = req.body;
  if (!email || !codigo) {
    return res.status(400).json({ error: "Correo y código son obligatorios." });
  }

  const usuario = await prisma.usuario.findUnique({ where: { email } });
  if (!usuario) {
    return res.status(404).json({ error: "No existe una cuenta con este correo." });
  }
  if (usuario.emailVerificado) {
    return res.status(200).json({ message: "La cuenta ya estaba verificada." });
  }

  const registro = await prisma.codigoVerificacion.findFirst({
    where: {
      usuarioId: usuario.id,
      tipo: "VERIFICACION_EMAIL",
      codigo,
      usado: false,
      expiraEn: { gt: new Date() },
    },
    orderBy: { creadoEn: "desc" },
  });

  if (!registro) {
    return res.status(400).json({ error: "El código es inválido o ha expirado." });
  }

  await prisma.$transaction([
    prisma.usuario.update({
      where: { id: usuario.id },
      data: { emailVerificado: true },
    }),
    prisma.codigoVerificacion.update({
      where: { id: registro.id },
      data: { usado: true },
    }),
  ]);

  return res.status(200).json({ message: "Cuenta verificada correctamente." });
}

// POST /api/auth/resend-code   { email, tipo: "VERIFICACION_EMAIL" | "RESET_PASSWORD" }
async function resendCode(req, res) {
  const { email, tipo } = req.body;
  if (!email || !["VERIFICACION_EMAIL", "RESET_PASSWORD"].includes(tipo)) {
    return res.status(400).json({ error: "Solicitud inválida." });
  }

  const usuario = await prisma.usuario.findUnique({ where: { email } });
  // Respuesta genérica: no revela si el correo existe o no.
  if (!usuario) {
    return res.status(200).json({ message: "Si el correo existe, se ha enviado un nuevo código." });
  }
  if (tipo === "VERIFICACION_EMAIL" && usuario.emailVerificado) {
    return res.status(200).json({ message: "La cuenta ya estaba verificada." });
  }

  await crearYEnviarCodigo(usuario, tipo);
  return res.status(200).json({ message: "Se ha enviado un nuevo código." });
}

// POST /api/auth/login
async function login(req, res) {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: "Correo y contraseña son obligatorios." });
  }

  const usuario = await prisma.usuario.findUnique({ where: { email } });
  if (!usuario) {
    return res.status(401).json({ error: "Credenciales incorrectas." });
  }

  if (usuario.bloqueadoHasta && usuario.bloqueadoHasta > new Date()) {
    const minutosRestantes = Math.ceil((usuario.bloqueadoHasta - new Date()) / 60000);
    return res.status(423).json({
      error: `Cuenta bloqueada temporalmente por múltiples intentos fallidos. Intenta de nuevo en ${minutosRestantes} minuto(s).`,
    });
  }

  if (usuario.estado !== "ACTIVO") {
    return res.status(403).json({ error: "Esta cuenta se encuentra inactiva." });
  }

  const passwordOk = await bcrypt.compare(password, usuario.passwordHash);
  if (!passwordOk) {
    const intentosFallidos = usuario.intentosFallidos + 1;
    const bloqueado = intentosFallidos >= MAX_INTENTOS;
    await prisma.usuario.update({
      where: { id: usuario.id },
      data: {
        intentosFallidos: bloqueado ? 0 : intentosFallidos,
        bloqueadoHasta: bloqueado
          ? new Date(Date.now() + BLOQUEO_MINUTOS * 60 * 1000)
          : null,
      },
    });
    if (bloqueado) {
      return res.status(423).json({
        error: `Cuenta bloqueada temporalmente por ${BLOQUEO_MINUTOS} minutos tras 5 intentos fallidos.`,
      });
    }
    return res.status(401).json({ error: "Credenciales incorrectas." });
  }

  if (!usuario.emailVerificado) {
    return res.status(403).json({
      error: "Debes verificar tu correo antes de iniciar sesión.",
      requiresVerification: true,
      email: usuario.email,
    });
  }

  await prisma.usuario.update({
    where: { id: usuario.id },
    data: { intentosFallidos: 0, bloqueadoHasta: null },
  });

  const token = signSessionToken(usuario);
  return res.status(200).json({ token, usuario: publicUser(usuario) });
}

// POST /api/auth/forgot-password
async function forgotPassword(req, res) {
  const { email } = req.body;
  if (!email) {
    return res.status(400).json({ error: "El correo es obligatorio." });
  }

  const usuario = await prisma.usuario.findUnique({ where: { email } });
  if (usuario) {
    await crearYEnviarCodigo(usuario, "RESET_PASSWORD");
  }

  // Respuesta genérica por seguridad, sin importar si el correo existe.
  return res.status(200).json({
    message: "Si el correo está registrado, recibirás un código para restablecer tu contraseña.",
  });
}

// POST /api/auth/verify-reset-code
async function verifyResetCode(req, res) {
  const { email, codigo } = req.body;
  if (!email || !codigo) {
    return res.status(400).json({ error: "Correo y código son obligatorios." });
  }

  const usuario = await prisma.usuario.findUnique({ where: { email } });
  if (!usuario) {
    return res.status(400).json({ error: "El código es inválido o ha expirado." });
  }

  const registro = await prisma.codigoVerificacion.findFirst({
    where: {
      usuarioId: usuario.id,
      tipo: "RESET_PASSWORD",
      codigo,
      usado: false,
      expiraEn: { gt: new Date() },
    },
    orderBy: { creadoEn: "desc" },
  });

  if (!registro) {
    return res.status(400).json({ error: "El código es inválido o ha expirado." });
  }

  await prisma.codigoVerificacion.update({
    where: { id: registro.id },
    data: { usado: true },
  });

  const resetToken = signResetToken(usuario);
  return res.status(200).json({ resetToken });
}

// POST /api/auth/reset-password
async function resetPassword(req, res) {
  const { resetToken, password } = req.body;
  if (!resetToken || !password) {
    return res.status(400).json({ error: "Solicitud inválida." });
  }
  if (!isPasswordValid(password)) {
    return res.status(400).json({
      error:
        "La contraseña debe tener mínimo 8 caracteres, e incluir mayúsculas, minúsculas y números.",
    });
  }

  let payload;
  try {
    payload = verifyToken(resetToken);
  } catch (err) {
    return res.status(400).json({ error: "El enlace de restablecimiento es inválido o expiró." });
  }
  if (payload.purpose !== "reset_password") {
    return res.status(400).json({ error: "Token inválido." });
  }

  const passwordHash = await bcrypt.hash(password, 10);
  await prisma.usuario.update({
    where: { id: payload.sub },
    data: { passwordHash, intentosFallidos: 0, bloqueadoHasta: null },
  });

  return res.status(200).json({ message: "Contraseña restablecida correctamente." });
}

// GET /api/auth/me  (requiere middleware de autenticación)
async function me(req, res) {
  const usuario = await prisma.usuario.findUnique({ where: { id: req.usuarioId } });
  if (!usuario) {
    return res.status(404).json({ error: "Usuario no encontrado." });
  }
  return res.status(200).json({ usuario: publicUser(usuario) });
}

module.exports = {
  register,
  verifyEmail,
  resendCode,
  login,
  forgotPassword,
  verifyResetCode,
  resetPassword,
  me,
};
