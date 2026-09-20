#!/usr/bin/env python3
"""
Script de Guardia contra Regresiones — Batería de Riesgo Psicosocial
===================================================================
Este script verifica que los componentes y páginas clave del frontend no hayan
sufrido regresiones (sobrescritura por placeholders viejos, datos simulados o
validaciones perdidas) tras realizar un git pull o una fusión de ramas.

INSTRUCCIONES DE USO:
  Ejecutar siempre después de cualquier 'git pull' o 'git merge':
    python scripts/verificar_regresiones.py

Si algún chequeo falla, el script retornará código de salida 1 con una
explicación detallada del error y la ruta exacta del archivo afectado.
"""

import os
import re
import sys
from pathlib import Path

# Raíz del proyecto (un nivel arriba del directorio de este script)
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_SRC = ROOT_DIR / "frontend" / "src"

EXCEPCIONES_MOCK = {}


class Checker:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def check(self, condition: bool, description: str, error_msg: str):
        if condition:
            self.passed += 1
            print(f"  [OK] {description}")
        else:
            self.failed += 1
            print(f"  [FALLO] {description}")
            self.errors.append(f"FALTA / REGRESIÓN: {description}\n         Detalle: {error_msg}")


def main():
    print("==================================================================")
    print("[+] VERIFICACION DE REGRESIONES CONOCIDAS Y PUNTOS CALIENTES")
    print("==================================================================")

    checker = Checker()

    # ------------------------------------------------------------------
    # 1. CuestionarioTrabajador.jsx y ListaEvaluacionesTrabajador.jsx
    # ------------------------------------------------------------------
    print("\n1. Verificando componentes de vista Trabajador...")

    file_cuestionario = FRONTEND_SRC / "components" / "CuestionarioTrabajador.jsx"
    if not file_cuestionario.exists():
        checker.check(False, "CuestionarioTrabajador.jsx existe", f"El archivo no existe en {file_cuestionario}")
    else:
        content = file_cuestionario.read_text(encoding="utf-8")
        lines = content.splitlines()
        no_pronto = "(Pronto)" not in content
        line_count_ok = len(lines) >= 50
        checker.check(
            no_pronto and line_count_ok,
            "CuestionarioTrabajador.jsx completo y sin placeholder",
            f"Líneas: {len(lines)} (mínimo 50), Contiene '(Pronto)': {not no_pronto}. Ruta: {file_cuestionario}"
        )

    file_lista = FRONTEND_SRC / "components" / "ListaEvaluacionesTrabajador.jsx"
    if not file_lista.exists():
        checker.check(False, "ListaEvaluacionesTrabajador.jsx existe", f"El archivo no existe en {file_lista}")
    else:
        content = file_lista.read_text(encoding="utf-8")
        lines = content.splitlines()
        no_pronto = "(Pronto)" not in content
        line_count_ok = len(lines) >= 50
        checker.check(
            no_pronto and line_count_ok,
            "ListaEvaluacionesTrabajador.jsx completo y sin placeholder",
            f"Líneas: {len(lines)} (mínimo 50), Contiene '(Pronto)': {not no_pronto}. Ruta: {file_lista}"
        )

    # ------------------------------------------------------------------
    # 2. Dashboard.jsx
    # ------------------------------------------------------------------
    print("\n2. Verificando Dashboard.jsx y conexión real a backend...")
    file_dashboard = FRONTEND_SRC / "pages" / "Dashboard.jsx"
    if not file_dashboard.exists():
        checker.check(False, "Dashboard.jsx existe", f"El archivo no existe en {file_dashboard}")
    else:
        content = file_dashboard.read_text(encoding="utf-8")
        no_db_simulada = "DB_SIMULADA" not in content

        funciones_requeridas = [
            "fetchIndicadores",
            "fetchAnalisisPredictivo",
            "generarInformeAgrupado",
            "descargarInforme",
        ]
        funciones_presentes = [f for f in funciones_requeridas if f in content]
        todas_funciones = len_funciones = len(funciones_presentes) == len(funciones_requeridas)

        checker.check(
            no_db_simulada and todas_funciones,
            "Dashboard.jsx conectado al backend real con sus 4 funciones de API",
            f"Contiene 'DB_SIMULADA': {not no_db_simulada}. Funciones encontradas ({len(funciones_presentes)}/{len(funciones_requeridas)}): {funciones_presentes}. Ruta: {file_dashboard}"
        )

    # ------------------------------------------------------------------
    # 3. VerificarNit.jsx
    # ------------------------------------------------------------------
    print("\n3. Verificando VerificarNit.jsx y formato con Dígito Verificador...")
    file_nit = FRONTEND_SRC / "pages" / "VerificarNit.jsx"
    if not file_nit.exists():
        checker.check(False, "VerificarNit.jsx existe", f"El archivo no existe en {file_nit}")
    else:
        content = file_nit.read_text(encoding="utf-8")
        has_dv_pattern = r"\d{9}-\d" in content or r"\d{9}-\\d" in content or r"\d{9}-\\d" in content or r"^\d{9}-\d$" in content
        checker.check(
            has_dv_pattern,
            "VerificarNit.jsx contiene la validación con dígito verificador (\\d{9}-\\d)",
            f"No se encontró el patrón de NIT con dígito verificador. Ruta: {file_nit}"
        )

    # ------------------------------------------------------------------
    # 4. Escaneo general de MOCK, SIMULAD, _EJEMPLO en páginas y componentes
    # ------------------------------------------------------------------
    print("\n4. Escaneando páginas y componentes en busca de mocks no autorizados...")
    target_dirs = [FRONTEND_SRC / "pages", FRONTEND_SRC / "components"]
    patrones_sospechosos = [
        (r"\bMOCK\b", "palabra reservada MOCK"),
        (r"\bSIMULAD[OA]?\b", "datos simulados"),
        (r"_EJEMPLO\b", "constante de datos de ejemplo _EJEMPLO"),
    ]

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for filepath in target_dir.glob("*.jsx"):
            filename = filepath.name
            if filename in EXCEPCIONES_MOCK:
                print(f"  [EXCEPCIÓN CONOCIDA] {filename}: {EXCEPCIONES_MOCK[filename]}")
                continue

            file_text = filepath.read_text(encoding="utf-8")

            # Buscar patrones sospechosos
            for pattern, desc in patrones_sospechosos:
                if re.search(pattern, file_text, re.IGNORECASE):
                    # Ignorar comentarios si es sólo mención explícita que diga "no simulado"
                    checker.check(
                        False,
                        f"Sin datos simulados en {filename}",
                        f"Se detectó patrón de mock '{desc}' en {filepath}"
                    )
                    break
            else:
                checker.check(True, f"Código limpio en {filename}", "")

    # ------------------------------------------------------------------
    # RESUMEN Y RESULTADO
    # ------------------------------------------------------------------
    print("\n==================================================================")
    print("RESUMEN DE VERIFICACION DE REGRESIONES")
    print("==================================================================")
    print(f"  Total chequeos exitosos: {checker.passed}")
    print(f"  Total fallos detectados: {checker.failed}")

    if checker.failed > 0:
        print("\n[ERROR] SE DETECTARON REGRESIONES EN EL CODIGO:")
        for err in checker.errors:
            print(f"  - {err}")
        print("\nRevise y restaure los componentes afectados antes de continuar.")
        sys.exit(1)
    else:
        print("\n[OK] TODO LIMPIO. No se detectaron regresiones en los componentes clave.")
        sys.exit(0)


if __name__ == "__main__":
    main()
