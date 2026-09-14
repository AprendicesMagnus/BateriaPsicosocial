const { verifyToken } = require("../utils/tokens");

function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;

  if (!token) {
    return res.status(401).json({ error: "No autenticado." });
  }

  try {
    const payload = verifyToken(token);
    req.usuarioId = payload.sub;
    req.usuarioRol = payload.rol;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Sesión inválida o expirada." });
  }
}

module.exports = { requireAuth };
