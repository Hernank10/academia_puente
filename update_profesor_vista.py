# -*- coding: utf-8 -*-
"""update_profesor_vista.py"""
from pathlib import Path
import re

p = Path(r"E:\02_proyectos\academia_puente\_original\users\views.py")
txt = p.read_text(encoding="utf-8")

# Verificar si ya esta actualizada
if "'tab_activa'" in txt:
    print("Vista ya actualizada")
else:
    # Buscar el inicio de la funcion profesor_curso_detalle
    patron = re.compile(
        r"(def profesor_curso_detalle\(request, curso_id\):)(.*?)(?=\n@|\ndef |\Z)",
        re.DOTALL
    )
    match = patron.search(txt)
    if not match:
        print("ERROR: no se encontro profesor_curso_detalle")
    else:
        nueva_funcion = '''def profesor_curso_detalle(request, curso_id):
    """Vista del curso con pestanas: estudiantes, lecciones, evaluaciones, tareas."""
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar que el curso pertenece al profesor
    if not request.user.is_superuser and curso.profesor != request.user:
        messages.error(request, "No tienes permiso para ver este curso.")
        return redirect('users:dashboard_profesor')

    # Pestana activa
    tab_activa = request.GET.get('tab', 'estudiantes')

    # Inscripciones y estudiantes
    inscripciones = Inscripcion.objects.filter(
        curso=curso, activa=True
    ).select_related('estudiante')

    total_lecciones = curso.lecciones.count()

    # Info por estudiante
    estudiantes_info = []
    for ins in inscripciones:
        estudiante = ins.estudiante
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=estudiante, leccion__curso=curso, completada=True
        ).count()
        progreso_pct = round((completadas / total_lecciones * 100)) if total_lecciones else 0

        # Entregas del estudiante en este curso
        entregas = Entrega.objects.filter(
            estudiante=estudiante, tarea__curso=curso
        )
        entregas_pendientes = entregas.filter(estado='entregada', calificacion__isnull=True).count()
        entregas_calificadas = entregas.filter(estado='calificada').count()

        # Promedio de calificaciones
        from django.db.models import Avg
        promedio = entregas.filter(calificacion__isnull=False).aggregate(avg=Avg('calificacion'))['avg']
        promedio = round(promedio, 1) if promedio else 0

        estudiantes_info.append({
            'estudiante': estudiante,
            'completadas': completadas,
            'total': total_lecciones,
            'progreso_pct': progreso_pct,
            'entregas_pendientes': entregas_pendientes,
            'entregas_calificadas': entregas_calificadas,
            'promedio': promedio,
        })

    # Ordenar por progreso desc
    estudiantes_info.sort(key=lambda x: -x['progreso_pct'])

    # Lecciones
    lecciones = curso.lecciones.all().order_by('orden')

    # Evaluaciones
    evaluaciones = curso.evaluaciones.all().order_by('-creada')

    # Tareas
    tareas = curso.tareas.all().order_by('orden', '-creada')

    # Certificados emitidos en este curso
    certificados_curso = Certificado.objects.filter(
        curso=curso, estado='emitido'
    ).count()

    # Progreso promedio del curso
    if estudiantes_info:
        progreso_promedio = round(sum(e['progreso_pct'] for e in estudiantes_info) / len(estudiantes_info))
    else:
        progreso_promedio = 0

    context = {
        'curso': curso,
        'tab_activa': tab_activa,
        'inscripciones': inscripciones,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': inscripciones.count(),
        'total_lecciones': total_lecciones,
        'total_evaluaciones': evaluaciones.count(),
        'lecciones': lecciones,
        'evaluaciones': evaluaciones,
        'tareas': tareas,
        'certificados_curso': certificados_curso,
        'progreso_promedio': progreso_promedio,
    }
    return render(request, 'users/profesor_curso_detalle.html', context)
'''
        txt = txt[:match.start()] + nueva_funcion + txt[match.end():]
        p.write_text(txt, encoding="utf-8")
        print("OK: profesor_curso_detalle actualizada")
        print("OK: nueva funcion con pestanas")

import ast
try:
    ast.parse(p.read_text(encoding="utf-8"))
    print("OK: views.py compila")
except SyntaxError as e:
    print("ERROR sintaxis: " + str(e))