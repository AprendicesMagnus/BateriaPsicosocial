import uuid
import json
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.survey import CuestionarioVersion, Pregunta
from app.models.evaluation import EvaluacionParticipante, ParticipanteInstrumento, Respuesta
from app.core.encryption import descifrar_json
from app.core.nit_utils import calcular_digito_verificador_nit

from app.db.seed import sembrar_todos_los_cuestionarios

client = TestClient(app)
db = SessionLocal()
sembrar_todos_los_cuestionarios(db)
db.commit()

# Login Admin
res_login_admin = client.post('/api/auth/login', json={'email': 'admin@magnussig.com', 'password': 'Admin1234'})
token_admin = res_login_admin.json()['token']
headers_admin = {'Authorization': f'Bearer {token_admin}'}

# Crear org, area, trabajador
nit_base = f'9{str(uuid.uuid4().int)[:8]}'
nit_valido = f'{nit_base}-{calcular_digito_verificador_nit(nit_base)}'
res_org = client.post('/api/organizaciones', headers=headers_admin, json={'nombre': 'Empresa Demo Estres SAS', 'nit': nit_valido})
org_id = res_org.json()['id']

res_area = client.post('/api/organizaciones/areas', headers=headers_admin, json={'organizacionId': org_id, 'nombre': 'Salud'})
area_id = res_area.json()['id']

email_trab = f'trab_estres_{uuid.uuid4().hex[:4]}@test.com'
res_trab = client.post('/api/usuarios', headers=headers_admin, json={
    'nombre': 'Mario',
    'apellido': 'Pérez',
    'email': email_trab,
    'password': 'Trabajador1234',
    'rolCodigo': 'TRABAJADOR',
    'organizacionId': org_id,
    'areaId': area_id,
    'numeroIdentificacion': f'{str(uuid.uuid4().int)[:10]}',
    'cargo': 'Analista de Operaciones'
})
trab_id = res_trab.json()['id']

# Crear evaluacion e iniciar
res_eval = client.post('/api/evaluaciones', headers=headers_admin, json={'organizacionId': org_id, 'nombre': 'Evaluacion Estres 2026', 'trabajadoresIds': [trab_id]})
eval_id = res_eval.json()['id']
client.post(f'/api/evaluaciones/{eval_id}/iniciar', headers=headers_admin)

# Login trabajador y consentimiento
res_login_trab = client.post('/api/auth/login', json={'email': email_trab, 'password': 'Trabajador1234'})
token_trab = res_login_trab.json()['token']
headers_trab = {'Authorization': f'Bearer {token_trab}'}
client.post(f'/api/evaluaciones/{eval_id}/consentimiento', headers=headers_trab)

# Obtener version ESTRES y su primera pregunta E1
from app.models.survey import Dimension
v_estres = db.query(CuestionarioVersion).filter(CuestionarioVersion.codigo == 'ESTRES').first()
p_e1 = db.query(Pregunta).join(Dimension).filter(Pregunta.codigo == 'EST_1', Dimension.version_id == v_estres.id).first()

# Guardar respuesta a E1 desde el endpoint del frontend (/respuestas)
res_resp = client.post(f'/api/evaluaciones/{eval_id}/respuestas', headers=headers_trab, json={
    'preguntaId': str(p_e1.id),
    'valor': 4
})

# Consultar respuesta directamente en la BD para demostrar persistencia y cifrado
part = db.query(EvaluacionParticipante).filter(EvaluacionParticipante.evaluacion_id == eval_id, EvaluacionParticipante.trabajador_id == trab_id).first()
resp_db = db.query(Respuesta).filter(Respuesta.participante_id == part.id, Respuesta.pregunta_id == p_e1.id).first()

valor_descifrado = descifrar_json(resp_db.valor_cifrado)

resultado_demo = {
    'versionCodigo': v_estres.codigo,
    'versionNombre': v_estres.nombre,
    'preguntaId': str(p_e1.id),
    'preguntaCodigo': p_e1.codigo,
    'preguntaEnunciadoExacto': p_e1.enunciado,
    'valorEnviadoFrontend': 4,
    'valorDescifradoBD': valor_descifrado,
    'coincideTextoExacto': p_e1.enunciado == 'Dolores en el cuello y espalda o tensión muscular.'
}

print(json.dumps(resultado_demo, indent=2, ensure_ascii=False))

db.close()
