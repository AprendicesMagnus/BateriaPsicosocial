import { useState } from "react";
import { editarEmpresaAdmin } from "../api/perfil";
import "../styles/PanelModal.css";

export default function ModalEmpresaAdmin({ empresa, token, onCerrar, onGuardado }) {
  const [form, setForm] = useState({
    nombre: empresa.nombre || "",
    nit: empresa.nit || "",
    sector: empresa.sector || "",
    municipio: empresa.municipio || "",
    telefono: empresa.telefono || "",
    email: empresa.email || "",
    activa: empresa.activa !== false,
  });
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function guardar(e) {
    e.preventDefault();
    setError("");
    if (!form.nombre.trim()) return setError("El nombre de la empresa es obligatorio.");
    if (!/^\d{9}(-\d)?$/.test(form.nit.trim())) return setError("El NIT debe tener 9 dígitos y su dígito de verificación opcional.");
    setGuardando(true);
    try {
      await editarEmpresaAdmin(token, empresa.id, {
        nombre: form.nombre.trim(), nit: form.nit.trim(),
        sector: form.sector.trim() || null, municipio: form.municipio.trim() || null,
        telefono: form.telefono.trim() || null, email: form.email.trim() || null,
        activa: form.activa,
      });
      onGuardado("Empresa actualizada correctamente.");
    } catch (err) {
      setError(err.message || "No se pudo actualizar la empresa.");
      setGuardando(false);
    }
  }

  return (
    <div className="adm-modal-fondo" role="dialog" aria-modal="true" aria-labelledby="adm-empresa-titulo">
      <form className="adm-modal" onSubmit={guardar} noValidate>
        <h2 id="adm-empresa-titulo">Editar empresa</h2>
        <label>Nombre de la empresa<input maxLength={180} value={form.nombre} onChange={cambiar("nombre")} /></label>
        <label>NIT<input inputMode="numeric" maxLength={11} value={form.nit} onChange={cambiar("nit")} /></label>
        <div className="adm-modal__fila">
          <label>Sector<input maxLength={80} value={form.sector} onChange={cambiar("sector")} /></label>
          <label>Municipio<input maxLength={80} value={form.municipio} onChange={cambiar("municipio")} /></label>
        </div>
        <div className="adm-modal__fila">
          <label>Teléfono<input maxLength={10} inputMode="numeric" value={form.telefono} onChange={(e) => setForm((f) => ({ ...f, telefono: soloDigitos(e.target.value, 10) }))} /></label>
          <label>Correo<input type="email" maxLength={180} value={form.email} onChange={cambiar("email")} /></label>
        </div>
        <label className="adm-modal__check"><input type="checkbox" checked={form.activa} onChange={(e) => setForm((f) => ({ ...f, activa: e.target.checked }))} /> Empresa activa</label>
        {error && <div className="adm-modal__error">{error}</div>}
        <div className="adm-modal__acciones">
          <button type="submit" className="adm-btn adm-btn--oscuro adm-modal__confirmar" disabled={guardando}>{guardando ? "Guardando..." : "Confirmar cambios"}</button>
          <button type="button" className="adm-btn adm-btn--borde" onClick={onCerrar} disabled={guardando}>Cancelar</button>
        </div>
      </form>
    </div>
  );
}
