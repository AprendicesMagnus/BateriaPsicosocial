import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { fetchMisEmpresas } from "../api/perfil";
import { fetchIndicadores } from "../api/indicadores";
import "../styles/PrimerosPasos.css";

const ROLES_VISIBLES = ["JEFE", "ADMINISTRADOR", "EVALUADOR_SST"];

function construirPasos(rol, datos) {
  const tieneEmpresa = datos.empresas > 0;
  const pasos = [
    {
      id: "empresa",
      titulo: "Registra tu empresa",
      texto: "Crea la empresa que vas a evaluar.",
      ruta: "/verificar-nit",
      hecho: tieneEmpresa,
      bloqueado: false,
    },
  ];
  if (rol === "EVALUADOR_SST") {
    pasos.push({
      id: "enlace",
      titulo: "Genera un enlace para tu primer paciente",
      texto: "En Reportes, sección Enlaces para pacientes, usa Crear enlace.",
      ruta: "/reportes",
      hecho: datos.asignados > 0,
      bloqueado: !tieneEmpresa,
    });
  }
  pasos.push({
    id: "resultados",
    titulo: "Revisa los resultados en el Dashboard",
    texto: "Se activan cuando hay cuestionarios completados.",
    ruta: "/dashboard",
    hecho: datos.completados > 0,
    bloqueado: !tieneEmpresa,
  });
  return pasos;
}

export default function PrimerosPasos() {
  const { token, usuario } = useAuth();
  const rol = usuario?.rol;
  const organizacionId = usuario?.organizacionId ?? null;
  const visible = Boolean(token) && ROLES_VISIBLES.includes(rol);
  const [datos, setDatos] = useState(null);

  useEffect(() => {
    if (!visible) return undefined;
    let cancelado = false;

    async function cargar() {
      try {
        const empresas = (await fetchMisEmpresas(token)) || [];
        let asignados = 0;
        let completados = 0;
        // Sin empresa activa NO se consulta: el backend devolveria conteos de todas las empresas.
        if (empresas.length > 0 && organizacionId) {
          const resumen = await fetchIndicadores(token, organizacionId);
          asignados = resumen?.participacion?.totalAsignados ?? 0;
          completados = resumen?.participacion?.totalCompletados ?? 0;
        }
        if (!cancelado) setDatos({ empresas: empresas.length, asignados, completados });
      } catch {
        // Si falla la consulta la tarjeta simplemente no se muestra; el Inicio sigue funcionando.
        if (!cancelado) setDatos(null);
      }
    }

    cargar();
    return () => {
      cancelado = true;
    };
  }, [visible, token, organizacionId]);

  if (!visible || !datos) return null;

  const pasos = construirPasos(rol, datos);
  const hechos = pasos.filter((p) => p.hecho).length;
  if (hechos === pasos.length) return null;

  return (
    <section className="primeros-pasos" aria-labelledby="primeros-pasos-titulo">
      <div className="container">
        <div className="primeros-pasos__tarjeta">
          <div className="primeros-pasos__cabecera">
            <h2 id="primeros-pasos-titulo" className="primeros-pasos__titulo">Primeros pasos</h2>
            <span className="primeros-pasos__progreso">
              {hechos} de {pasos.length} completados
            </span>
          </div>
          <ol className="primeros-pasos__lista">
            {pasos.map((paso, indice) => {
              const estado = paso.hecho ? "Hecho" : paso.bloqueado ? "Primero registra tu empresa" : "Pendiente";
              const clase = paso.hecho
                ? "primeros-pasos__paso primeros-pasos__paso--hecho"
                : paso.bloqueado
                  ? "primeros-pasos__paso primeros-pasos__paso--bloqueado"
                  : "primeros-pasos__paso";
              const contenido = (
                <>
                  <span className="primeros-pasos__marca" aria-hidden="true">
                    {paso.hecho ? "✓" : indice + 1}
                  </span>
                  <span className="primeros-pasos__cuerpo">
                    <span className="primeros-pasos__nombre">{paso.titulo}</span>
                    <span className="primeros-pasos__descripcion">{paso.texto}</span>
                  </span>
                  <span className="primeros-pasos__estado">{estado}</span>
                </>
              );
              return (
                <li key={paso.id}>
                  {paso.bloqueado || paso.hecho ? (
                    <div className={clase} aria-disabled={paso.bloqueado ? "true" : undefined}>
                      {contenido}
                    </div>
                  ) : (
                    <Link className={clase} to={paso.ruta}>
                      {contenido}
                    </Link>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      </div>
    </section>
  );
}
