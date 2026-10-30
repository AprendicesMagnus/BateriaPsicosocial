"""contenido editable del Centro de ayuda (guías, FAQ, glosario, riesgo, novedades, atención)

Revision ID: d7a1c3e5f9b2
Revises: 61f92783b1c0
"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d7a1c3e5f9b2"
down_revision: Union[str, Sequence[str], None] = "61f92783b1c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (sección, título, texto, orden)
# None representa un título SQL NULL cuando no hay título.
SEMILLA = [
    [
        "guia_SUPER_ADMINISTRADOR",
        None,
        "Entra al Panel de administración desde este menú de perfil.",
        1,
    ],
    [
        "guia_SUPER_ADMINISTRADOR",
        None,
        "En 'Usuarios y roles' puedes invitar, editar o verificar usuarios.",
        2,
    ],
    [
        "guia_SUPER_ADMINISTRADOR",
        None,
        "En 'Planes de baterías' configuras lo que se ve en la página de precios.",
        3,
    ],
    [
        "guia_SUPER_ADMINISTRADOR",
        None,
        "En 'Auditoría y privacidad' revisas la actividad de la plataforma.",
        4,
    ],
    [
        "guia_JEFE",
        None,
        "Desde el Dashboard, registra o elige la empresa activa con la que vas a trabajar.",
        1,
    ],
    [
        "guia_JEFE",
        None,
        "Crea el Responsable SST de tu empresa al registrarla.",
        2,
    ],
    [
        "guia_JEFE",
        None,
        "Compra baterías desde 'Comprar baterías' según la cantidad de trabajadores.",
        3,
    ],
    [
        "guia_JEFE",
        None,
        "Genera enlaces para que los trabajadores respondan la batería.",
        4,
    ],
    [
        "guia_JEFE",
        None,
        "Consulta los resultados agregados en 'Reportes'.",
        5,
    ],
    [
        "guia_ADMINISTRADOR",
        None,
        "Desde el Dashboard, elige la empresa activa con la que vas a trabajar.",
        1,
    ],
    [
        "guia_ADMINISTRADOR",
        None,
        "Invita o gestiona usuarios según los permisos de tu rol.",
        2,
    ],
    [
        "guia_ADMINISTRADOR",
        None,
        "Consulta los resultados agregados en 'Reportes'.",
        3,
    ],
    [
        "guia_EVALUADOR_SST",
        None,
        "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
        1,
    ],
    [
        "guia_EVALUADOR_SST",
        None,
        "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
        2,
    ],
    [
        "guia_EVALUADOR_SST",
        None,
        "Desde el Dashboard eliges con qué empresa estás trabajando.",
        3,
    ],
    [
        "guia_EVALUADOR_SST",
        None,
        "Genera enlaces para que los trabajadores respondan la batería.",
        4,
    ],
    [
        "guia_EVALUADOR_SST",
        None,
        "Consulta los resultados agregados en 'Reportes'.",
        5,
    ],
    [
        "guia_RESPONSABLE_SST",
        None,
        "Tu número de resolución aparece en 'Ver perfil'; pídele a un administrador que lo verifique.",
        1,
    ],
    [
        "guia_RESPONSABLE_SST",
        None,
        "Una vez verificado, puedes corregirlo hasta 3 veces cada 5 días si lo necesitas.",
        2,
    ],
    [
        "guia_RESPONSABLE_SST",
        None,
        "Genera enlaces para que los trabajadores de tu empresa respondan la batería.",
        3,
    ],
    [
        "guia_RESPONSABLE_SST",
        None,
        "Consulta los resultados agregados en 'Reportes'.",
        4,
    ],
    [
        "faq",
        "¿Cómo cambio mi número de resolución?",
        "Solo Psicólogos y Responsables SST lo ven en 'Ver perfil'. Un administrador debe verificarlo primero; una vez verificado, puedes editarlo hasta 3 veces cada 5 días.",
        1,
    ],
    [
        "faq",
        "¿Cada cuánto puedo editar mi perfil (nombre, apellido, foto)?",
        "Una vez cada 5 días. El sistema te indica la fecha y hora exacta en que podrás volver a hacerlo.",
        2,
    ],
    [
        "faq",
        "¿Cómo cambio de empresa activa?",
        "Si manejas más de una empresa, el selector de 'Empresa activa' está en el Dashboard (o en tu perfil, según tu rol).",
        3,
    ],
    [
        "faq",
        "¿Cómo compro más baterías?",
        "Desde 'Comprar baterías' eliges la cantidad; el precio se ajusta automáticamente según el plan que corresponda.",
        4,
    ],
    [
        "faq",
        "¿Qué hago si no me llega el código de verificación?",
        "Revisa spam/correo no deseado. Si persiste, un administrador puede reenviarte las credenciales desde el Panel.",
        5,
    ],
    [
        "faq",
        "¿Son confidenciales las respuestas de los trabajadores?",
        "Sí. Las respuestas individuales son confidenciales; la empresa solo ve resultados agregados, nunca respuestas por persona.",
        6,
    ],
    [
        "faq",
        "¿Qué pasa si un trabajador pierde el enlace de la encuesta?",
        "El Psicólogo o Responsable SST puede volver a generar el enlace para ese trabajador desde su panel de enlaces.",
        7,
    ],
    [
        "faq",
        "¿Puedo tener varias empresas con la misma cuenta?",
        "Sí, si eres Jefe, Administrador o Psicólogo. Cada empresa tiene sus propios usuarios, enlaces y reportes por separado.",
        8,
    ],
    [
        "faq",
        "¿Qué hago si olvidé mi contraseña?",
        "En la pantalla de inicio de sesión usa '¿Olvidaste tu contraseña?' para recibir un código de recuperación.",
        9,
    ],
    [
        "riesgo",
        "Sin riesgo / Riesgo bajo",
        "Las condiciones son adecuadas. Mantén las acciones actuales y vuelve a medir según el programa de la empresa.",
        1,
    ],
    [
        "riesgo",
        "Riesgo medio",
        "Hay factores que conviene observar. Programa acciones preventivas y seguimiento periódico.",
        2,
    ],
    [
        "riesgo",
        "Riesgo alto",
        "Requiere intervención: define un plan de acción con responsables y fechas.",
        3,
    ],
    [
        "riesgo",
        "Riesgo muy alto",
        "Es prioritario: intervención inmediata, seguimiento cercano y revisión con el Psicólogo.",
        4,
    ],
    [
        "glosario",
        "Batería de riesgo psicosocial",
        "Conjunto de instrumentos validados (Resolución 2764 de 2022) que mide los factores de riesgo psicosocial intralaboral y extralaboral y el estrés.",
        1,
    ],
    [
        "glosario",
        "Intralaboral",
        "Condiciones del trabajo y de la organización: liderazgo, control sobre el trabajo, demandas y recompensas.",
        2,
    ],
    [
        "glosario",
        "Extralaboral",
        "Aspectos del entorno fuera del trabajo que influyen en el bienestar: familia, vivienda, transporte y relaciones.",
        3,
    ],
    [
        "glosario",
        "Anonimización",
        "Los resultados solo se muestran por grupos de al menos 5 participantes, para proteger la identidad de cada persona.",
        4,
    ],
    [
        "glosario",
        "Dominio y dimensión",
        "Cada dominio agrupa varias dimensiones, y cada dimensión resume preguntas relacionadas.",
        5,
    ],
    [
        "glosario",
        "Baremo",
        "Tabla de referencia que convierte el puntaje obtenido en un nivel de riesgo.",
        6,
    ],
    [
        "novedades",
        "Nuevo Centro de ayuda",
        "Ahora tienes guías por rol, preguntas frecuentes y un canal directo con soporte.",
        1,
    ],
    [
        "novedades",
        "Planes de baterías",
        "Consulta los planes y precios en la página principal y elige tu plan al momento de pagar.",
        2,
    ],
    [
        "atencion",
        "Horario de atención",
        "Lunes a viernes, de 8:00 a. m. a 5:00 p. m. (hora de Colombia).",
        1,
    ],
    [
        "atencion",
        "Canal principal",
        "Escríbenos desde esta página o a aprendizmagnus@gmail.com.",
        2,
    ],
    [
        "atencion",
        "Tiempo de respuesta",
        "Respondemos en un máximo de 2 días hábiles.",
        3,
    ],
]


def upgrade() -> None:
    tabla = op.create_table(
        "soporte_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("seccion", sa.String(length=40), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=True),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column(
            "orden",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_index(
        "ix_soporte_items_seccion",
        "soporte_items",
        ["seccion"],
    )

    op.bulk_insert(
        tabla,
        [
            {
                "id": uuid.uuid4(),
                "seccion": seccion,
                "titulo": titulo,
                "texto": texto,
                "orden": orden,
                "activo": True,
            }
            for seccion, titulo, texto, orden in SEMILLA
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_soporte_items_seccion",
        table_name="soporte_items",
    )
    op.drop_table("soporte_items")
