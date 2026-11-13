from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import Usuario
from app.schemas.common import SoporteDocumentoUpdate, SoporteItemCreate, SoporteItemUpdate, TicketSoporteCreate, TicketSoporteRespuesta
from app.services import soporte as soporte_service
from app.services import soporte_contenido as contenido_service
from app.services import soporte_documentos as documentos_service

router = APIRouter()


@router.post("")
def crear_ticket(
    data: TicketSoporteCreate,
    segundo_plano: BackgroundTasks,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(get_current_user),
):
    """Cualquier usuario autenticado envía un mensaje desde el Centro de ayuda."""
    ticket = soporte_service.crear_ticket(db, actual, data.mensaje)
    # El correo al buzón de soporte sale en segundo plano para no hacer esperar al usuario.
    segundo_plano.add_task(soporte_service.notificar_ticket, ticket, actual.email)
    return ticket



@router.get("/mios")
def listar_mis_tickets(db: Session = Depends(get_db), actual: Usuario = Depends(get_current_user)):
    return soporte_service.listar_tickets_usuario(db, actual.id)


@router.get("")
def listar_tickets(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    """Solo el Super Administrador ve los tickets (p. ej. desde el Panel)."""
    return soporte_service.listar_tickets(db)


@router.post("/{ticket_id}/resolver")
def marcar_resuelto(ticket_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return soporte_service.marcar_resuelto(db, ticket_id)


@router.post("/{ticket_id}/responder")
def responder_ticket(
    ticket_id: UUID,
    data: TicketSoporteRespuesta,
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_admin),
):
    return soporte_service.responder_ticket(db, ticket_id, data.respuesta, respondido_por=actual.id)


# --- Contenido editable del Centro de ayuda ---------------------------------------------------


@router.get("/contenido")
def contenido_publico(db: Session = Depends(get_db), _actual: Usuario = Depends(get_current_user)):
    """Guías, preguntas frecuentes, glosario, etc. visibles para cualquier usuario con sesión."""
    return contenido_service.contenido_publico(db)


@router.get("/contenido/admin")
def contenido_admin(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.listar_admin(db)


@router.post("/contenido")
def crear_contenido(data: SoporteItemCreate, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.crear_item(db, data)


@router.patch("/contenido/{item_id}")
def editar_contenido(item_id: UUID, data: SoporteItemUpdate, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.actualizar_item(db, item_id, data)


@router.delete("/contenido/{item_id}")
def eliminar_contenido(item_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return contenido_service.eliminar_item(db, item_id)


# --- Documentos descargables del Centro de ayuda -----------------------------------------------


@router.get("/documentos")
def documentos_publicos(db: Session = Depends(get_db), _actual: Usuario = Depends(get_current_user)):
    """Documentos visibles para cualquier usuario con sesión (solo metadatos)."""
    return documentos_service.listar_publico(db)


@router.get("/documentos/admin")
def documentos_admin(db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return documentos_service.listar_admin(db)


@router.post("/documentos")
async def subir_documento(
    archivo: UploadFile = File(...),
    titulo: str = Form(...),
    descripcion: str | None = Form(default=None),
    activo: bool = Form(default=True),
    db: Session = Depends(get_db),
    actual: Usuario = Depends(require_admin),
):
    """El Super Administrador sube un documento (PDF, Word, Excel o PowerPoint, máx. 10 MB)."""
    contenido = await archivo.read(documentos_service.MAX_DOCUMENTO_BYTES + 1)
    return documentos_service.crear(
        db,
        nombre=archivo.filename or "",
        contenido=contenido,
        titulo=titulo,
        descripcion=descripcion,
        activo=activo,
        usuario_id=actual.id,
    )


@router.get("/documentos/{doc_id}/descargar")
def descargar_documento(doc_id: UUID, db: Session = Depends(get_db), actual: Usuario = Depends(get_current_user)):
    doc = documentos_service.obtener_para_descarga(db, doc_id, es_admin=actual.rol.codigo == "SUPER_ADMINISTRADOR")
    return Response(
        content=doc.contenido,
        media_type=doc.tipo_mime,
        headers={
            # Siempre como descarga (nunca se abre dentro de la página) y con el tipo fijado por el servidor.
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(doc.nombre_archivo)}",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )


@router.patch("/documentos/{doc_id}")
def editar_documento(doc_id: UUID, data: SoporteDocumentoUpdate, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return documentos_service.actualizar(db, doc_id, data)


@router.delete("/documentos/{doc_id}")
def eliminar_documento(doc_id: UUID, db: Session = Depends(get_db), _actual: Usuario = Depends(require_admin)):
    return documentos_service.eliminar(db, doc_id)
