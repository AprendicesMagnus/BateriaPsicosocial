import { useState } from "react";
import { editarUsuarioAdmin, invitarUsuario } from "../api/perfil";
import { emailValido, filtrarNombrePersona, nombrePersonaValido, normalizarEmail, soloDigitos } from "../utils/validaciones";
import "../styles/PanelModal.css";

const ROLES_INVITAR = [
  { value: "SUPER_ADMINISTRADOR", label: "Super Administrador" },
  { value: "ADMINISTRADOR", label: "Administrador" },
  { value: "JEFE", label: "Jefe" },
  { value: "EVALUADOR_SST", label: "Psicólogo" },
];
const ROLES_EDITAR = [...ROLES_INVITAR, { value: "RESPONSABLE_SST", label: "Responsable SST" }];

// Invitar un usuario nuevo o editar uno existente (solo Super Administrador, desde el Panel).
export default function ModalUsuarioAdmin({ modo, usuario, token, onCerrar, onGuardado }) {
  const editando = modo === "editar";
  const [form, setForm] = useState({
    nombre: editando ? usuario.nombrePila ?? "" : "",
    apellido: editando ? usuario.apellido ?? "" : "",
    email: editando ? usuario.correo : "",
    rolCodigo: editando ? usuario.rol : "ADMINISTRADOR",
    estado: editando && usuario.estado === "INACTIVO" ? "INACTIVO" : "ACTIVO",
    numeroResolucion: "",
  });
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  async function guardar(e) {
    e.preventDefault();
    setError("");
    if (!nombrePersonaValido(form.nombre.trim(), 100)) return setError("Escribe un nombre válido (solo letras).");
    if (!nombrePersonaValido(form.apellido.trim(), 100)) return setError("Escribe un apellido válido (solo letras).");
    if (!editando && !emailValido(normalizarEmail(form.email))) return setError("Escribe un correo válido.");
    if (!editando && form.rolCodigo === "EVALUADOR_SST" && !/^\d{6}$/.test(form.numeroResolucion))
      return setError("El número de resolución del Psicólogo debe tener exactamente 6 dígitos.");

    setGuardando(true);
    try {
      if (editando) {
        await editarUsuarioAdmin(token, usuario.id, {
          nombre: form.nombre.trim(),
          apellido: form.apellido.trim(),
          rolCodigo: form.rolCodigo,
          estado: form.estado,
        });
        onGuardado("Usuario actualizado correctamente.");
      } else {
        await invitarUsuario(token, {
          nombre: form.nombre.trim(),
          apellido: form.apellido.trim(),
          email: normalizarEmail(form.email),
          rolCodigo: form.rolCodigo,
          ...(form.rolCodigo === "EVALUADOR_SST" ? { numeroResolucion: form.numeroResolucion } : {}),
        });
        onGuardado("Invitación enviada: el usuario recibirá un código en su correo para crear su contraseña.");
      }
    } catch (err) {
      setError(err.message || "No se pudo guardar.");
      setGuardando(false);
    }
  }

  return (
    <div className="adm-modal-fondo" role="dialog" aria-modal="true" aria-labelledby="adm-modal-titulo">
      <form className="adm-modal" onSubmit={guardar} noValidate>
        <h2 id="adm-modal-titulo">{editando ? "Editar usuario" : "Invitar usuario"}</h2>
        {!editando && (
          <p className="adm-modal__nota">
            Se crea la cuenta y se envía un código al correo para que la persona defina su contraseña.
          </p>
        )}

        <div className="adm-modal__fila">
          <label>
            Nombre
            <input maxLength={100} value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: filtrarNombrePersona(e.target.value, 100) }))} />
          </label>
          <label>
            Apellido
            <input maxLength={100} value={form.apellido} onChange={(e) => setForm((f) => ({ ...f, apellido: filtrarNombrePersona(e.target.value, 100) }))} />
          </label>
        </div>

        <label>
          Correo electrónico {editando && "(no se puede modificar)"}
          <input type="email" maxLength={180} value={form.email} onChange={cambiar("email")} disabled={editando} />
        </label>

        <div className="adm-modal__fila">
          <label>
            Rol
            <select value={form.rolCodigo} onChange={cambiar("rolCodigo")}>
              {(editando ? ROLES_EDITAR : ROLES_INVITAR).map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </label>
          {editando && (
            <label>
              Estado
              <select value={form.estado} onChange={cambiar("estado")}>
                <option value="ACTIVO">Activo</option>
                <option value="INACTIVO">Desactivado</option>
              </select>
            </label>
          )}
        </div>

        {!editando && form.rolCodigo === "EVALUADOR_SST" && (
          <label>
            Número de Resolución
            <input
              inputMode="numeric"
              maxLength={6}
              placeholder="Ej. 123456"
              value={form.numeroResolucion}
              onChange={(e) => setForm((f) => ({ ...f, numeroResolucion: soloDigitos(e.target.value, 6) }))}
            />
          </label>
        )}

        {error && <div className="adm-modal__error">{error}</div>}

        <div className="adm-modal__acciones">
          <button type="submit" className="adm-btn adm-btn--oscuro" disabled={guardando}>
            {guardando ? "Guardando..." : editando ? "Guardar cambios" : "Enviar invitación"}
          </button>
          <button type="button" className="adm-btn adm-btn--borde" onClick={onCerrar} disabled={guardando}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
