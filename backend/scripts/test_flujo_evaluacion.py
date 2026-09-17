import sys
import httpx
import uuid

BASE_URL = 'http://127.0.0.1:4000/api'

def main():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    print('--- PASO 1: Login como administrador ---')
    res = client.post('/auth/login', json={
        'email': 'admin@magnussig.com',
        'password': 'Admin1234'
    })
    assert res.status_code == 200, f'Error login admin: {res.text}'
    data_login = res.json()
    token_admin = data_login['token']
    headers_admin = {'Authorization': f'Bearer {token_admin}'}
    print('  [OK] Admin autenticado:', data_login['usuario']['email'])

    print('--- PASO 2: Crear Organizacion y Trabajador ---')
    nit_rnd = f'900{uuid.uuid4().hex[:6]}'
    res = client.post('/organizaciones', headers=headers_admin, json={
        'nombre': 'MiPyme Huila Innovadora SAS',
        'nit': nit_rnd,
        'sector': 'Servicios',
        'municipio': 'Neiva',
        'telefono': '3101234567',
        'email': f'contacto_{nit_rnd}@pyme.com'
    })
    assert res.status_code == 200, f'Error crear org: {res.text}'
    org = res.json()
    org_id = org['id']
    print(f'  [OK] Organizacion creada: {org["nombre"]} (ID: {org_id})')

    # Crear Area
    res = client.post('/organizaciones/areas', headers=headers_admin, json={
        'organizacionId': org_id,
        'nombre': 'Operaciones y Produccion'
    })
    assert res.status_code == 200, f'Error crear area: {res.text}'
    area = res.json()
    area_id = area['id']
    print(f'  [OK] Area creada: {area["nombre"]} (ID: {area_id})')

    # Crear Trabajador
    email_trabajador = f'trabajador_{uuid.uuid4().hex[:5]}@pyme.com'
    pass_trabajador = 'Trabajador1234'
    res = client.post('/usuarios', headers=headers_admin, json={
        'nombre': 'Carlos',
        'apellido': 'Perez',
        'email': email_trabajador,
        'password': pass_trabajador,
        'rolCodigo': 'TRABAJADOR',
        'organizacionId': org_id,
        'areaId': area_id,
        'numeroIdentificacion': f'CC{uuid.uuid4().hex[:8]}',
        'cargo': 'Analista de Operaciones'
    })
    assert res.status_code == 200, f'Error crear trabajador: {res.text}'
    trabajador = res.json()
    trabajador_id = trabajador['id']
    print(f'  [OK] Trabajador creado: {trabajador["nombre"]} {trabajador["apellido"]} (ID: {trabajador_id})')

    print('--- PASO 3: Crear Evaluacion asociada al cuestionario BRP ---')
    res = client.get('/cuestionarios', headers=headers_admin)
    assert res.status_code == 200, f'Error listar cuestionarios: {res.text}'
    cuestionarios = res.json()
    assert len(cuestionarios) > 0, 'No hay cuestionarios disponibles'
    version_id = cuestionarios[0]['id']

    res = client.post('/evaluaciones', headers=headers_admin, json={
        'organizacionId': org_id,
        'nombre': 'Evaluacion BRP Anual 2026',
        'versionId': version_id,
        'trabajadoresIds': [trabajador_id]
    })
    assert res.status_code == 200, f'Error crear evaluacion: {res.text}'
    evaluacion = res.json()
    eval_id = evaluacion['id']
    print(f'  [OK] Evaluacion creada: {evaluacion["nombre"]} (ID: {eval_id}, Estado: {evaluacion["estado"]})')

    print('--- PASO 4: Iniciar Evaluacion y Notificar ---')
    res = client.post(f'/evaluaciones/{eval_id}/iniciar', headers=headers_admin)
    assert res.status_code == 200, f'Error iniciar evaluacion: {res.text}'
    print('  [OK] Evaluacion iniciada (Estado: EN_CURSO)')

    res = client.post(f'/evaluaciones/{eval_id}/notificar', headers=headers_admin)
    assert res.status_code == 200, f'Error notificar participantes: {res.text}'
    print('  [OK] Participantes notificados')

    print('--- PASO 5: Flujo como Trabajador ---')
    res = client.post('/auth/login', json={
        'email': email_trabajador,
        'password': pass_trabajador
    })
    assert res.status_code == 200, f'Error login trabajador: {res.text}'
    token_trabajador = res.json()['token']
    headers_trabajador = {'Authorization': f'Bearer {token_trabajador}'}
    print('  [OK] Trabajador autenticado con token JWT')

    res = client.post(f'/evaluaciones/{eval_id}/consentimiento', headers=headers_trabajador)
    assert res.status_code == 200, f'Error consentimiento: {res.text}'
    print('  [OK] Consentimiento informado registrado digitalmente')

    res = client.get(f'/evaluaciones/{eval_id}/cuestionario', headers=headers_trabajador)
    assert res.status_code == 200, f'Error cuestionario asignado: {res.text}'
    cuestionario_asignado = res.json()
    preguntas = cuestionario_asignado['preguntas']
    assert len(preguntas) == 9, f'Se esperaban 9 preguntas, se recibieron {len(preguntas)}'
    print(f'  [OK] Cuestionario cargado ({len(preguntas)} preguntas)')

    respuestas_a_enviar = {
        'P1': 1, 'P2': 1, 'P3': 5,
        'P4': 3, 'P5': 3, 'P6': 3,
        'P7': 1, 'P8': 1, 'P9': 1,
    }

    for preg in preguntas:
        codigo = preg['codigo']
        val = respuestas_a_enviar.get(codigo, 3)
        res = client.post(f'/evaluaciones/{eval_id}/respuestas', headers=headers_trabajador, json={
            'preguntaId': preg['id'],
            'valor': val
        })
        assert res.status_code == 200, f'Error guardar respuesta para {codigo}: {res.text}'
    print('  [OK] Todas las respuestas guardadas (cifradas en BD)')

    res = client.post(f'/evaluaciones/{eval_id}/finalizar-cuestionario', headers=headers_trabajador)
    assert res.status_code == 200, f'Error finalizar cuestionario: {res.text}'
    cierre = res.json()
    print('  [OK] Cuestionario finalizado exitosamente')

    print('--- PASO 6: Validacion de Tabulacion y Baremos ---')
    resultados = cierre['resultados']
    assert len(resultados) == 3, f'Se esperaban 3 resultados de dimension, se obtuvieron {len(resultados)}'

    for r in resultados:
        print(f'  -> Dimension: {r["dimension"]} | Bruto: {r["puntajeBruto"]} | Transf: {r["puntajeTransformado"]} | Nivel: {r["nivel"]}')

    r_liderazgo = [r for r in resultados if 'Liderazgo' in r['dominio']][0]
    assert r_liderazgo['puntajeTransformado'] == 100.0, f'Liderazgo debio ser 100.0, fue {r_liderazgo["puntajeTransformado"]}'
    assert r_liderazgo['nivel'] == 'MUY_ALTO', f'Nivel esperado MUY_ALTO, obtenido {r_liderazgo["nivel"]}'

    r_demandas = [r for r in resultados if 'Demandas' in r['dominio']][0]
    assert r_demandas['puntajeTransformado'] == 0.0, f'Demandas debio ser 0.0, fue {r_demandas["puntajeTransformado"]}'
    assert r_demandas['nivel'] == 'SIN_RIESGO', f'Nivel esperado SIN_RIESGO, obtenido {r_demandas["nivel"]}'
    print('  [OK] Verificacion de calculos matematicos y baremos correcta al 100%')

    print('--- PASO 7: Consultar Resultados como Administrador ---')
    res = client.get(f'/evaluaciones/{eval_id}/resultados', headers=headers_admin)
    assert res.status_code == 200, f'Error consultar resultados como admin: {res.text}'
    resultados_eval = res.json()
    assert len(resultados_eval) == 1, f'Se esperaba 1 participante en resultados, hay {len(resultados_eval)}'
    print(f'  [OK] Consulta exitosa como Admin. Participante: {resultados_eval[0]["trabajadorId"]}')

    print('\n============================================================')
    print('FLUJO DE EVALUACION END-TO-END VERIFICADO EXITOSAMENTE')
    print('============================================================')

if __name__ == '__main__':
    main()
