# -*- coding: utf-8 -*-
"""diagnostico_evaluaciones.py - Que existe hoy en el modulo de evaluaciones."""
import os, sys, django, re
from pathlib import Path

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import (
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
    IntentoEvaluacion, RespuestaIntento,
)


# ============================================================
# 1. MODELO actual
# ============================================================
print("=" * 70)
print("1. CAMPOS DEL MODELO PreguntaEvaluacion")
print("=" * 70)
for f in PreguntaEvaluacion._meta.fields:
    print("  {:<25s}  {}  {}".format(
        f.name, type(f).__name__, 
        "(blank)" if getattr(f, "blank", False) else ""
    ))
print("")

print("CAMPOS DE OpcionRespuesta:")
for f in OpcionRespuesta._meta.fields:
    print("  {:<25s}  {}".format(f.name, type(f).__name__))
print("")

# ¿Existe campo 'tipo'?
tiene_tipo = any(f.name == "tipo" for f in PreguntaEvaluacion._meta.fields)
print("PreguntaEvaluacion tiene campo 'tipo': {}".format("SI" if tiene_tipo else "NO"))
print("")


# ============================================================
# 2. Datos actuales
# ============================================================
print("=" * 70)
print("2. DATOS EN LA DB")
print("=" * 70)
print("Total evaluaciones:  {}".format(Evaluacion.objects.count()))
print("Total preguntas:     {}".format(PreguntaEvaluacion.objects.count()))
print("Total opciones:      {}".format(OpcionRespuesta.objects.count()))
print("Total intentos:      {}".format(IntentoEvaluacion.objects.count()))
print("")

# Distribucion de opciones correctas por pregunta
from collections import Counter
distr = Counter()
for p in PreguntaEvaluacion.objects.prefetch_related('opciones'):
    n_correctas = sum(1 for o in p.opciones.all() if o.es_correcta)
    n_total = p.opciones.count()
    distr[(n_total, n_correctas)] += 1

print("Distribucion (total_opciones, correctas) -> cantidad:")
for (t, c), n in sorted(distr.items()):
    print("  ({:>2}, {:>2}) -> {:>3} preguntas".format(t, c, n))
print("")


# ============================================================
# 3. Vistas y templates actuales
# ============================================================
print("=" * 70)
print("3. ARCHIVOS CLAVE")
print("=" * 70)

archivos = [
    "users/views_profesor.py",
    "users/forms_profesor.py",
    "templates/profesor/evaluacion_detalle.html",
    "templates/profesor/form_generico.html",
    "templates/courses/rendir_evaluacion.html",
]

for rel in archivos:
    f = BASE / rel
    if f.exists():
        n = len(f.read_text(encoding="utf-8").splitlines())
        print("  OK  {}  ({} lineas)".format(rel, n))
    else:
        print("  ERR {}  NO EXISTE".format(rel))
print("")


# ============================================================
# 4. URLs de evaluaciones
# ============================================================
print("=" * 70)
print("4. URLs DE EVALUACIONES")
print("=" * 70)

urls_txt = (BASE / "users" / "urls.py").read_text(encoding="utf-8")
nombres = [
    "profesor_evaluacion_detalle",
    "profesor_evaluacion_editar",
    "profesor_evaluacion_borrar",
    "profesor_pregunta_crear",
    "profesor_pregunta_editar",
    "profesor_pregunta_borrar",
    "profesor_opcion_crear",
    "profesor_opcion_editar",
    "profesor_opcion_borrar",
]
for n in nombres:
    print("  {}  users:{}".format(
        "OK " if n in urls_txt else "ERR", n
    ))
print("")


# ============================================================
# 5. Vista de rendir evaluacion
# ============================================================
print("=" * 70)
print("5. VISTA rendir_evaluacion (courses/views.py)")
print("=" * 70)

views_txt = (BASE / "courses" / "views.py").read_text(encoding="utf-8")
m = re.search(
    r"def rendir_evaluacion\(request.*?\n(?=def |@|\Z)",
    views_txt, re.DOTALL
)
if m:
    cuerpo = m.group(0)
    print("Existe, {} lineas".format(cuerpo.count(chr(10))))
    # Buscar palabras clave
    for kw in ["tipo", "multiple", "verdadero", "corta", "emparejar",
               "preguntas", "opciones", "es_correcta"]:
        print("  contiene '{}': {}".format(kw, kw in cuerpo.lower()))
else:
    print("NO ENCONTRADA")
print("")

print("LISTO")