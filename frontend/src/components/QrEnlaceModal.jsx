import { useEffect, useRef } from "react";
import { QRCodeCanvas } from "qrcode.react";
import "../styles/QrEnlaceModal.css";

export default function QrEnlaceModal({ url, titulo, onCerrar }) {
  const contenedorRef = useRef(null);

  useEffect(() => {
    function alPresionarTecla(evento) {
      if (evento.key === "Escape") onCerrar();
    }
    window.addEventListener("keydown", alPresionarTecla);
    return () => window.removeEventListener("keydown", alPresionarTecla);
  }, [onCerrar]);

  function descargar() {
    const canvas = contenedorRef.current?.querySelector("canvas");
    if (!canvas) return;
    const nombreBase = (titulo || "enlace").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const vinculo = document.createElement("a");
    vinculo.href = canvas.toDataURL("image/png");
    vinculo.download = `qr-${nombreBase}.png`;
    vinculo.click();
  }

  return (
    <div className="qr-modal__fondo" onClick={onCerrar}>
      <div
        className="qr-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Código QR del enlace"
        onClick={(evento) => evento.stopPropagation()}
      >
        <h3 className="qr-modal__titulo">{titulo || "Código QR del enlace"}</h3>
        <div className="qr-modal__qr" ref={contenedorRef}>
          <QRCodeCanvas value={url} size={240} marginSize={4} level="M" />
        </div>
        <p className="qr-modal__url">{url}</p>
        <div className="qr-modal__acciones">
          <button type="button" onClick={descargar}>Descargar PNG</button>
          <button type="button" onClick={onCerrar}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}
