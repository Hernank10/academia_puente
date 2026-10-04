# -*- coding: utf-8 -*-
"""vincular_evaluaciones.py
   Auto-vincula recursos interactivos con evaluaciones
   heredando los del curso + coincidencia por titulo.

   Uso:
     python scripts/vincular_evaluaciones.py             -> dry-run
     python scripts/vincular_evaluaciones.py --apply     -> aplica
     python scripts/vincular_evaluaciones.py --reset --apply -> desvincula
"""
import os, sys, re, unicodedata
from pathlib import Path

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from courses.models import Evaluacion, RecursoInteractivo

APPLY = '--apply' in sys.argv
RESET = '--reset' in sys.argv
MAX_RECURSOS = 6


def log(msg):
    print(msg)


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def palabras_significativas(texto):
    texto = normalizar(texto)
    palabras = re.findall(r'\b[a-z]{4,}\b', texto)
    stopwords = {
        'para', 'con', 'del', 'los', 'las', 'una', 'uno', 'que', 'por',
        'como', 'sus', 'mas', 'pero', 'este', 'esta', 'esos', 'esas',
        'muy', 'sin', 'sobre', 'entre', 'desde', 'hasta', 'todos',
        'evaluacion', 'evaluaciones', 'auto', 'mixta', 'unica',
        'multiple', 'corta', 'emparejar', 'test',
    }
    return [p for p in palabras if p not in stopwords]


if RESET:
    if not APPLY:
        log("AVISO: --reset requiere --apply")
        sys.exit(0)
    for e in Evaluacion.objects.all():
        e.recursos_complementarios.clear()
    log("OK: todas las vinculaciones de evaluaciones eliminadas")
    sys.exit(0)


log("=" * 70)
log("VINCULACION DE EVALUACIONES")
log("=" * 70)
log("Modo: {}".format("APPLY" if APPLY else "DRY-RUN"))
log("")

# Pre-calcular palabras clave de recursos
log("Pre-procesando recursos...")
recursos = list(RecursoInteractivo.objects.filter(activo=True))
recursos_kw = []
for r in recursos:
    texto = "{} {} {}".format(r.titulo or "", r.subtitulo or "", r.descripcion or "")
    recursos_kw.append({
        'r': r,
        'kw': set(palabras_significativas(texto)),
    })
log("OK: {} recursos".format(len(recursos)))
log("")

# Procesar evaluaciones
evaluaciones = Evaluacion.objects.all()
log("Evaluaciones a procesar: {}".format(evaluaciones.count()))
log("")

total_vinculos = 0
evals_con_match = 0
evals_con_herencia = 0
evals_sin_nada = 0

for i, ev in enumerate(evaluaciones, 1):
    # 1. Recursos del curso padre (heuristica principal)
    curso_recursos = list(ev.curso.recursos_relacionados.all()[:MAX_RECURSOS])

    # 2. Coincidencia por titulo de la evaluacion
    kw_eval = set(palabras_significativas(ev.titulo or ""))
    matches_titulo = []
    if kw_eval:
        scored = []
        for item in recursos_kw:
            comunes = len(kw_eval & item['kw'])
            if comunes >= 2:
                scored.append((comunes, item['r']))
        scored.sort(key=lambda x: -x[0])
        matches_titulo = [r for _, r in scored[:MAX_RECURSOS]]

    # Union: primero los del titulo, luego los del curso (sin duplicados)
    finales = list(matches_titulo)
    for r in curso_recursos:
        if r not in finales:
            finales.append(r)
    finales = finales[:MAX_RECURSOS]

    if matches_titulo:
        evals_con_match += 1
    elif curso_recursos:
        evals_con_herencia += 1
    else:
        evals_sin_nada += 1
        continue

    if APPLY:
        ev.recursos_complementarios.set(finales)
        total_vinculos += len(finales)

    if i % 100 == 0:
        log("  ...{}/{} evaluaciones".format(i, evaluaciones.count()))

log("")
log("RESUMEN")
log("=" * 70)
log("Evaluaciones con match directo:     {}".format(evals_con_match))
log("Evaluaciones por herencia del curso: {}".format(evals_con_herencia))
log("Evaluaciones sin ningun recurso:     {}".format(evals_sin_nada))
log("Vinculos creados:                    {}".format(total_vinculos))
log("")

if not APPLY:
    log("MODO DRY-RUN. Para aplicar:")
    log("  python scripts/vincular_evaluaciones.py --apply")
else:
    log("OK: vinculacion de evaluaciones completa")
