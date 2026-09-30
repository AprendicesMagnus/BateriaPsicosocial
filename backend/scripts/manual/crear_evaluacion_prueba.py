"""Crea una evaluación de prueba para un trabajador, lista para responder la batería.

Sin una evaluación asignada, las respuestas de los cuestionarios no se pueden guardar
(el backend no tiene a qué participante asociarlas). Este script:

1. Busca al trabajador por su correo.
2. Si no tiene organización, le asigna una (la del --nit indicado o la primera activa).
3. Crea una evaluación con ese trabajador como participante, usando el mismo servicio
   que POST /api/evaluaciones (así se crean los instrumentos Ficha, Estrés y Extralaboral).
4. Inicia la evaluación (estado EN_CURSO).

Uso (desde la carpeta backend, con el venv activo):
    python scripts\\manual\\crear_evaluacion_prueba.py correo.trabajador@ejemplo.com
    python scripts\\manual\\crear_evaluacion_prueba.py correo.trabajador@ejemplo.com --nit 900123456

Después: iniciar sesión en el frontend con ese trabajador y entrar a /ficha-datos-generales.
"""
import argparse
import sys
from pathlib import Path

# Permite importar "app" aunque el script se ejecute desde otra carpeta (backend/ es la raíz)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import func  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.evaluation import Evaluacion, EvaluacionParticipante  # noqa: E402
from app.models.organization import Organizacion  # noqa: E402
from app.models.user import Usuario  # noqa: E402
from app.schemas.common import EvaluacionCreate  # noqa: E402
from app.services import evaluaciones as evaluaciones_service  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea una evaluación de prueba para un trabajador.")
    parser.add_argument("email", help="Correo del usuario con rol TRABAJADOR")
    parser.add_argument("--nit", help="NIT de la organización a usar si el trabajador no tiene una")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # 1. Trabajador (el correo se compara sin importar mayúsculas)
        trabajador = db.query(Usuario).filter(func.lower(Usuario.email) == args.email.strip().lower()).first()
        if trabajador is None:
            sys.exit(f"No existe un usuario con el correo {args.email}.")
        if trabajador.rol.codigo != "TRABAJADOR":
            sys.exit(f"El usuario {args.email} tiene rol {trabajador.rol.codigo}; debe ser TRABAJADOR.")

        # Si ya tiene una evaluación sin finalizar, no se crea otra (evita duplicados al repetir el script)
        activa = (
            db.query(Evaluacion)
            .join(EvaluacionParticipante, EvaluacionParticipante.evaluacion_id == Evaluacion.id)
            .filter(EvaluacionParticipante.trabajador_id == trabajador.id, Evaluacion.estado != "FINALIZADA")
            .first()
        )
        if activa:
            print(f"El trabajador ya tiene la evaluación '{activa.nombre}' ({activa.estado}), id={activa.id}")
            return

        # 2. Organización: crear_evaluacion exige que el trabajador pertenezca a la organización
        if trabajador.organizacion_id is None:
            consulta = db.query(Organizacion).filter(Organizacion.activa.is_(True))
            organizacion = consulta.filter(Organizacion.nit == args.nit).first() if args.nit else consulta.first()
            if organizacion is None:
                sys.exit("No se encontró una organización activa (revisa el --nit).")
            trabajador.organizacion_id = organizacion.id
            db.flush()
            print(f"Organización asignada al trabajador: {organizacion.nombre} (NIT {organizacion.nit})")

        # 3. Se crea la evaluación como ADMINISTRADOR, igual que desde /docs
        admin = db.query(Usuario).filter(Usuario.rol.has(codigo="ADMINISTRADOR")).first()
        if admin is None:
            sys.exit("No hay un usuario ADMINISTRADOR; ejecuta primero python -m app.db.seed.")
        datos = EvaluacionCreate(
            organizacionId=trabajador.organizacion_id,
            nombre=f"Prueba batería - {trabajador.email}",
            trabajadoresIds=[trabajador.id],
        )
        # crear_evaluacion hace commit, incluido el cambio de organización del paso 2
        evaluacion = evaluaciones_service.crear_evaluacion(db, datos, admin)

        # 4. Se inicia para que quede EN_CURSO
        evaluaciones_service.iniciar_evaluacion(db, evaluacion["id"], admin)

        print(f"Evaluación creada e iniciada: id={evaluacion['id']}")
        if not trabajador.email_verificado:
            # El login rechaza cuentas sin verificar el correo
            print("Aviso: el correo del trabajador no está verificado; el login pedirá el código de verificación.")
        print("Siguiente paso: inicia sesión con este trabajador y entra a /ficha-datos-generales")
    finally:
        db.close()


if __name__ == "__main__":
    main()
