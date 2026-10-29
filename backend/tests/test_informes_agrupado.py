import io
import uuid
import zipfile

import pytest

from app.core.encryption import cifrar_json
from app.core.nit_utils import calcular_digito_verificador_nit
from app.db.seed import sembrar_todos_los_cuestionarios
from app.models.evaluation import Evaluacion, EvaluacionParticipante, Respuesta, ResultadoDimension
from app.models.organization import Area, Organizacion
from app.models.survey import CuestionarioVersion, Dimension, Pregunta
from app.models.user import Usuario


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    sembrar_todos_los_cuestionarios(db_session)
    db_session.commit()


@pytest.fixture
def datos_prueba_agrupado(client, db_session, crear_paciente):
    # 1. Login admin
    res_admin = client.post(
        "/api/auth/login",
        json={"email": "admin@magnussig.com", "password": "Admin1234"},
    )
    assert res_admin.status_code == 200, res_admin.text
    headers_admin = {"Authorization": f"Bearer {res_admin.json()['token']}"}

    # 2. Crear Organización y Áreas
    nit_base = f"9{str(uuid.uuid4().int)[:8]}"
    nit_rnd = f"{nit_base}-{calcular_digito_verificador_nit(nit_base)}"
    org = Organizacion(id=uuid.uuid4(), nombre="Empresa Informe Agrupado SAS", nit=nit_rnd)
    db_session.add(org)
    db_session.commit()

    area_ops = Area(id=uuid.uuid4(), organizacion_id=org.id, nombre="Operaciones")
    area_ventas = Area(id=uuid.uuid4(), organizacion_id=org.id, nombre="Ventas")
    db_session.add_all([area_ops, area_ventas])
    db_session.commit()

    # 3. Cuestionario INTRALABORAL_A: así los puntajes quedan asociados al participante
    # (informes_excel.py solo agrega ResultadoDimension de versiones INTRALABORAL_A/B).
    cuestionario = (
        db_session.query(CuestionarioVersion)
        .filter(CuestionarioVersion.codigo == "INTRALABORAL_A", CuestionarioVersion.vigente.is_(True))
        .first()
    )
    assert cuestionario is not None, "Debe existir la versión INTRALABORAL_A sembrada"
    dim = (
        db_session.query(Dimension)
        .filter(Dimension.version_id == cuestionario.id, Dimension.tipo == "DIMENSION")
        .order_by(Dimension.orden)
        .first()
    )
    assert dim is not None, "La versión INTRALABORAL_A debe tener dimensiones"

    admin_user = (
        db_session.query(Usuario)
        .filter(Usuario.email == "admin@magnussig.com")
        .first()
    )
    assert admin_user is not None

    evaluacion = Evaluacion(
        id=uuid.uuid4(),
        organizacion_id=org.id,
        evaluador_id=admin_user.id,
        version_id=cuestionario.id,
        nombre="Evaluación Agrupada Test 2026",
    )
    db_session.add(evaluacion)
    db_session.commit()

    # 4. Crear participantes para Operaciones (con respuestas, para que cuenten en el ZIP)
    participantes_ops_ids = [crear_paciente(org.id, area_id=area_ops.id)[0] for _ in range(5)]

    dimensiones = (
        db_session.query(Dimension)
        .filter(Dimension.version_id == cuestionario.id)
        .all()
    )
    pregunta = (
        db_session.query(Pregunta)
        .filter(Pregunta.dimension_id == dim.id)
        .order_by(Pregunta.orden)
        .first()
    )
    assert pregunta is not None, "La dimensión sembrada debe tener al menos una pregunta"

    def _crear_participante_con_resultados(trabajador_id):
        part = EvaluacionParticipante(
            id=uuid.uuid4(),
            evaluacion_id=evaluacion.id,
            trabajador_id=trabajador_id,
            estado="COMPLETADA",
        )
        db_session.add(part)
        db_session.flush()

        for d in dimensiones:
            res_dim = ResultadoDimension(
                participante_id=part.id,
                dimension_id=d.id,
                puntaje_bruto=45.0,
                puntaje_transformado=45.0,
                nivel="MEDIO",
            )
            db_session.add(res_dim)

        # Respuesta real: _participantes() solo incluye a quienes tienen al menos una.
        db_session.add(
            Respuesta(
                id=uuid.uuid4(),
                participante_id=part.id,
                pregunta_id=pregunta.id,
                valor_cifrado=cifrar_json(1),
            )
        )
        return part

    for tid in participantes_ops_ids:
        _crear_participante_con_resultados(tid)

    db_session.commit()

    yield {
        "headers_admin": headers_admin,
        "evaluacion_id": str(evaluacion.id),
        "area_ops_id": str(area_ops.id),
        "area_ventas_id": str(area_ventas.id),
    }


def test_informe_agrupado_devuelve_zip_de_excel(client, datos_prueba_agrupado):
    headers = datos_prueba_agrupado["headers_admin"]
    eval_id = datos_prueba_agrupado["evaluacion_id"]
    area_id = datos_prueba_agrupado["area_ops_id"]

    res = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": eval_id, "areaId": area_id},
    )
    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "application/zip"
    assert "attachment" in res.headers.get("content-disposition", "")

    zf = zipfile.ZipFile(io.BytesIO(res.content))
    nombres = zf.namelist()
    for esperado in ["Sociodemografica.xlsx", "Resultados.xlsx", "Consolidado trabajadores.xlsx"]:
        assert esperado in nombres


def test_informe_agrupado_sin_area_incluye_toda_la_evaluacion(client, datos_prueba_agrupado):
    headers = datos_prueba_agrupado["headers_admin"]
    eval_id = datos_prueba_agrupado["evaluacion_id"]

    res = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": eval_id, "areaId": None},
    )
    assert res.status_code == 200, res.text
    zf = zipfile.ZipFile(io.BytesIO(res.content))
    assert "Resultados.xlsx" in zf.namelist()


def test_informe_agrupado_area_sin_respuestas_rechaza(client, datos_prueba_agrupado):
    headers = datos_prueba_agrupado["headers_admin"]
    eval_id = datos_prueba_agrupado["evaluacion_id"]
    area_ventas_id = datos_prueba_agrupado["area_ventas_id"]

    res = client.post(
        "/api/informes/agrupado",
        headers=headers,
        json={"evaluacionId": eval_id, "areaId": area_ventas_id},
    )
    assert res.status_code == 400, res.text
