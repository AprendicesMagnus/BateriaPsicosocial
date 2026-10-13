import { useEffect, useState } from "react";

// Paginación en el cliente para cualquier lista.
//   const pag = usePaginacion(lista, 10, [filtro]);   // vuelve a la página 1 si cambia `filtro`
//   pag.items -> registros de la página actual
export function usePaginacion(lista, porPagina = 10, reiniciarCon = []) {
  const [pagina, setPagina] = useState(0);

  useEffect(() => {
    setPagina(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, reiniciarCon);

  const total = lista.length;
  const totalPaginas = Math.max(1, Math.ceil(total / porPagina));
  const paginaActual = Math.min(pagina, totalPaginas - 1); // nunca queda en una página que ya no existe
  const items = lista.slice(paginaActual * porPagina, (paginaActual + 1) * porPagina);

  return {
    items,
    total,
    porPagina,
    pagina: paginaActual,
    totalPaginas,
    irAnterior: () => setPagina(Math.max(0, paginaActual - 1)),
    irSiguiente: () => setPagina(Math.min(totalPaginas - 1, paginaActual + 1)),
  };
}