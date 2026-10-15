import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchVerificacionInforme } from "../api/informes";
import "../styles/VerificarInforme.css";

const ETIQUETAS_TIPO = {
  INDIVIDUAL: "Informe individual",
  AGRUPADO: "Informe agrupado",
};

async function calcularSha256(archivo) {
  if (!window.crypto?.subtle) {
    throw new Error("Este navegador no permite calcular la huella del archivo en una conexión no segura.");
  }
  const contenido = await archivo.arrayBuffer();
  const huella = await window.crypto.subtle.digest("SHA-256", contenido);
  return Array.from(new Uint8Array(huella))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export default function VerificarInforme() {
  const { codigo } = useParams();
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [calculando, setCalculando] = useState(false);
  const [comparacion, setComparacion] = useState(null);
  const [errorArchivo, setErrorArchivo] = useState(null);

  useEffect(() => {
    let activo = true;
    fetchVerificacionInforme(codigo)
      .then((respuesta) => {
        if (activo) setDatos(respuesta);
      })
      .catch((err) => {
        if (activo) setError(err.message || "No se pudo verificar el informe.");
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [codigo]);

  async function compararArchivo(evento) {
    const archivo = evento.target.files?.[0];
    if (!archivo || !datos?.hashSha256) return;
    setCalculando(true);
    setComparacion(null);
    setErrorArchivo(null);
    try {
      const huella = await calcularSha256(archivo);
      setComparacion(huella === datos.hashSha256 ? "coincide" : "no_coincide");
    } catch (err) {
      setErrorArchivo(err.message || "No se pudo calcular la huella del archivo.");
    } finally {
      setCalculando(false);
    }
  }

  return (
    <main className="verificacion">
      <section className="verificacion__tarjeta">
        <h1 className="verificacion__titulo">Verificación de informe</h1>

        {cargando && <p className="verificacion__estado">Verificando informe...</p>}

        {error && (
          <p className="verificacion__error" role="alert">
            {error}
          </p>
        )}

        {datos && (
          <>
            <p className="verificacion__ok">Este informe fue emitido por la plataforma.</p>
            <dl className="verificacion__datos">
              <div>
                <dt>Empresa</dt>
                <dd>{datos.organizacionNombre}</dd>
              </div>
              <div>
                <dt>Tipo</dt>
                <dd>
                  {ETIQUETAS_TIPO[datos.tipo] || datos.tipo} ({datos.formato})
                </dd>
              </div>
              <div>
                <dt>Fecha de emisión</dt>
                <dd>{new Date(datos.generadoEn).toLocaleString("es-CO")}</dd>
              </div>
              <div>
                <dt>Huella SHA-256 del archivo</dt>
                <dd className="verificacion__hash">
                  {datos.hashSha256 || "No registrada para este informe."}
                </dd>
              </div>
            </dl>

            {datos.hashSha256 && (
              <div className="verificacion__comparar">
                <label htmlFor="archivo-informe" className="verificacion__etiqueta">
                  Comparar con el archivo que usted tiene
                </label>
                <input id="archivo-informe" type="file" onChange={compararArchivo} disabled={calculando} />
                <p className="verificacion__nota">
                  El archivo no se envía al servidor: la huella se calcula en su navegador.
                </p>
                {calculando && <p className="verificacion__estado">Calculando huella...</p>}
                {comparacion === "coincide" && (
                  <p className="verificacion__ok" role="status">
                    El archivo coincide con el informe emitido. No ha sido modificado.
                  </p>
                )}
                {comparacion === "no_coincide" && (
                  <p className="verificacion__error" role="alert">
                    El archivo no coincide con el informe emitido. Pudo haber sido modificado.
                  </p>
                )}
                {errorArchivo && (
                  <p className="verificacion__error" role="alert">
                    {errorArchivo}
                  </p>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
