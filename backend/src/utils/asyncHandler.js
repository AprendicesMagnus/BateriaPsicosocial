// Envuelve controladores async para que las excepciones lleguen al middleware de errores de Express.
function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

module.exports = asyncHandler;
