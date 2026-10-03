# -*- coding: utf-8 -*-
"""Utilidades para el ranking."""
from django.db.models import Avg
from courses.models import (
    Curso, ProgresoEstudiante, Inscripcion,
    IntentoEvaluacion, Entrega,
)


def calcular_ranking(curso, request_user=None):
    """Devuelve lista de dicts ordenados por ranking."""
    inscripciones = Inscripcion.objects.filter(
        curso=curso, activa=True
    ).select_related('estudiante')

    total_lecciones = curso.lecciones.count()
    datos = []

    for ins in inscripciones:
        est = ins.estudiante
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=est, leccion__curso=curso, completada=True
        ).count()
        pct = int(completadas * 100 / total_lecciones) if total_lecciones else 0

        intentos = IntentoEvaluacion.objects.filter(
            estudiante=est, evaluacion__curso=curso, completado=True
        )
        prom_eval = intentos.aggregate(a=Avg('puntaje'))['a']
        prom_eval = round(prom_eval, 1) if prom_eval else 0

        entregas = Entrega.objects.filter(
            estudiante=est, tarea__curso=curso,
            calificacion__isnull=False
        )
        prom_ent = entregas.aggregate(a=Avg('calificacion'))['a']
        prom_ent = round(prom_ent, 1) if prom_ent else 0

        # Puntos totales del alumno en este curso
        puntos_curso = completadas * 5

        datos.append({
            'estudiante': est,
            'completadas': completadas,
            'total': total_lecciones,
            'pct': pct,
            'promedio_eval': prom_eval,
            'promedio_entregas': prom_ent,
            'puntos_curso': puntos_curso,
            'es_yo': (request_user and request_user.id == est.id),
        })

    # Ordenar: pct desc, prom_eval desc, nombre asc
    datos.sort(key=lambda x: (-x['pct'], -x['promedio_eval'], x['estudiante'].username))

    for i, d in enumerate(datos, 1):
        d['posicion'] = i

    return datos
