// Controles "Anterior / Página X de N / Siguiente". Recibe lo que devuelve usePaginacion.
// No se muestra si todos los registros caben en una sola página.
export default function Paginador({ paginacion }) {
  const { total, porPagina, pagina, totalPaginas, irAnterior, irSiguiente } = paginacion;
  if (total <= porPagina) return null;

  return (
    <div className="adm-paginacion">
      <button type="button" className="adm-btn adm-btn--borde" onClick={irAnterior} disabled={pagina === 0}>
        ← Anterior
      </button>
      <span className="adm-paginacion__info">
        Página {pagina + 1} de {totalPaginas} · {total} registros
      </span>
      <button
        type="button"
        className="adm-btn adm-btn--borde"
        onClick={irSiguiente}
        disabled={pagina >= totalPaginas - 1}
      >
        Siguiente →
      </button>
    </div>
  );
}