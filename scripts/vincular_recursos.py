# -*- coding: utf-8 -*-
"""vincular_recursos.py
   Auto-vincula recursos interactivos con cursos y lecciones
   por similitud de palabras clave en el titulo/descripcion.

   Uso:
     python scripts/vincular_recursos.py             -> dry-run
     python scripts/vincular_recursos.py --apply     -> aplica
     python scripts/vincular_recursos.py --reset     -> desvincula todo
"""
import os, sys, re, unicodedata
from pathlib import Path
from collections import Counter

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from courses.models import Curso, Leccion, RecursoInteractivo

APPLY = '--apply' in sys.argv
RESET = '--reset' in sys.argv
MAX_RECURSOS_POR_CURSO = 10
MAX_RECURSOS_POR_LECCION = 3


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
    """Extrae palabras de 4+ letras, filtra comunes."""
    texto = normalizar(texto)
    palabras = re.findall(r'\b[a-z]{4,}\b', texto)

    stopwords = {
        'para', 'con', 'del', 'los', 'las', 'una', 'uno', 'que', 'por',
        'como', 'sus', 'mas', 'pero', 'este', 'esta', 'esos', 'esas',
        'muy', 'sin', 'sobre', 'entre', 'desde', 'hasta', 'todos',
        'todas', 'estos', 'estas', 'donde', 'cuando', 'porque',
        'tiene', 'puede', 'hacer', 'segun', 'sera', 'esta', 'sido',
    }
    return [p for p in palabras if p not in stopwords]


def similitud(texto1, texto2):
    """Cuenta palabras compartidas."""
    p1 = set(palabras_significativas(texto1))
    p2 = set(palabras_significativas(texto2))
    if not p1 or not p2:
        return 0
    return len(p1 & p2)


# ============================================================
# RESET
# ============================================================
if RESET:
    if not APPLY:
        log("AVISO: --reset requiere --apply")
        sys.exit(0)
    for c in Curso.objects.all():
        c.recursos_relacionados.clear()
    for l in Leccion.objects.all():
        l.recursos_complementarios.clear()
    log("OK: todas las vinculaciones eliminadas")
    sys.exit(0)


# ============================================================
# Recursos (cacheados)
# ============================================================
log("=" * 70)
log("VINCULACION AUTOMATICA DE RECURSOS")
log("=" * 70)
log("Modo: {}".format("APPLY" if APPLY else "DRY-RUN"))
log("")

recursos = list(RecursoInteractivo.objects.filter(activo=True))
log("Recursos activos en DB: {}".format(len(recursos)))
log("")

# Pre-calcular palabras clave de cada recurso
log("Pre-procesando recursos...")
recursos_kw = []
for r in recursos:
    texto = "{} {} {}".format(r.titulo or "", r.subtitulo or "", r.descripcion or "")
    recursos_kw.append({
        'r': r,
        'kw': set(palabras_significativas(texto)),
        'titulo_norm': normalizar(r.titulo or ""),
    })
log("OK")
log("")


# ============================================================
# Vincular cursos
# ============================================================
log("=" * 70)
log("VINCULANDO CURSOS")
log("=" * 70)

cursos = Curso.objects.all()
total_vinculos = 0
cursos_sin_match = 0

for i, curso in enumerate(cursos, 1):
    texto_curso = "{} {} {}".format(
        curso.titulo or "",
        curso.materia.nombre if curso.materia else "",
        curso.get_idioma_display() or "",
    )
    kw_curso = set(palabras_significativas(texto_curso))

    if not kw_curso:
        cursos_sin_match += 1
        continue

    # Calcular score de cada recurso
    scored = []
    for item in recursos_kw:
        comunes = len(kw_curso & item['kw'])
        if comunes >= 2:
            scored.append((comunes, item['r']))

    scored.sort(key=lambda x: -x[0])
    matches = [r for _, r in scored[:MAX_RECURSOS_POR_CURSO]]

    if not matches:
        cursos_sin_match += 1
        continue

    log("  [{:3d}/{}] {} -> {} recursos".format(i, cursos.count(), curso.titulo[:45], len(matches)))

    if APPLY:
        curso.recursos_relacionados.set(matches)
        total_vinculos += len(matches)

log("")
log("Total cursos procesados: {}".format(cursos.count() - cursos_sin_match))
log("Cursos sin match:        {}".format(cursos_sin_match))
log("Vinculos creados:        {}".format(total_vinculos))
log("")


# ============================================================
# Vincular lecciones
# ============================================================
log("=" * 70)
log("VINCULANDO LECCIONES")
log("=" * 70)

lecciones = Leccion.objects.all()
total_lec_vinculos = 0
lecciones_sin_match = 0

for i, lec in enumerate(lecciones, 1):
    # Palabras clave del titulo de la leccion
    kw_leccion = set(palabras_significativas(lec.titulo or ""))
    if not kw_leccion:
        lecciones_sin_match += 1
        continue

    scored = []
    for item in recursos_kw:
        comunes = len(kw_leccion & item['kw'])
        if comunes >= 2:
            scored.append((comunes, item['r']))

    scored.sort(key=lambda x: -x[0])
    matches = [r for _, r in scored[:MAX_RECURSOS_POR_LECCION]]

    # FALLBACK: si no hay match, heredar recursos del curso
    if not matches:
        curso_recursos = list(lec.curso.recursos_relacionados.all()[:3])
        if curso_recursos:
            matches = curso_recursos
            lecciones_sin_match += 1
        else:
            lecciones_sin_match += 1
            continue

    if APPLY:
        lec.recursos_complementarios.set(matches)
        total_lec_vinculos += len(matches)

    if i % 200 == 0:
        log("  ...{}/{} lecciones".format(i, lecciones.count()))

log("")
log("Total lecciones vinculadas: {}".format(lecciones.count() - lecciones_sin_match))
log("Lecciones sin match:        {}".format(lecciones_sin_match))
log("Vinculos creados:           {}".format(total_lec_vinculos))
log("")

if not APPLY:
    log("MODO DRY-RUN: nada fue modificado.")
    log("Para aplicar: python scripts/vincular_recursos.py --apply")
else:
    log("OK: vinculacion completa")