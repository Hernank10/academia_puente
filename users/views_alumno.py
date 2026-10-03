# -*- coding: utf-8 -*-
"""views_alumno.py - Panel web del estudiante."""
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from django.utils import timezone

from courses.models import (
    Curso, Leccion, ProgresoEstudiante, Inscripcion, Certificado,
    Tarea, Entrega, Evaluacion, IntentoEvaluacion,
)
from .models import Perfil, Logro, LogroUsuario


def _perfil(user):
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    return perfil


def _racha(user):
    fechas = ProgresoEstudiante.objects.filter(
        estudiante=user, completada=True, fecha_completado__isnull=False
    ).values_list('fecha_completado__date', flat=True).distinct()
    fechas = sorted(set(f for f in fechas if f), reverse=True)
    if not fechas:
        return 0
    hoy = timezone.now().date()
    ayer = hoy - timedelta(days=1)
    if fechas[0] not in (hoy, ayer):
        return 0
    racha = 1
    esperada = fechas[0] - timedelta(days=1)
    for f in fechas[1:]:
        if f == esperada:
            racha += 1
            esperada -= timedelta(days=1)
        else:
            break
    return racha


def _info_curso(user, curso):
    """Devuelve dict con progreso y estado de un curso para el alumno."""
    total = curso.lecciones.count()
    completadas = ProgresoEstudiante.objects.filter(
        estudiante=user, leccion__curso=curso, completada=True
    ).count()
    pct = int(completadas * 100 / total) if total else 0

    cert = Certificado.objects.filter(
        estudiante=user, curso=curso, estado='emitido'
    ).first()

    entregas = Entrega.objects.filter(
        estudiante=user, tarea__curso=curso
    ).select_related('tarea').order_by('-fecha_entrega')

    intentos = IntentoEvaluacion.objects.filter(
        estudiante=user, evaluacion__curso=curso, completado=True
    ).select_related('evaluacion').order_by('-fecha_inicio')

    return {
        'curso': curso,
        'total': total,
        'completadas': completadas,
        'pct': pct,
        'certificado': cert,
        'entregas': entregas,
        'intentos': intentos,
        'completado': pct >= 100,
    }


# ==================== HOME ====================
@login_required
def alumno_home(request):
    perfil = _perfil(request.user)

    inscripciones = Inscripcion.objects.filter(
        estudiante=request.user, activa=True
    ).select_related('curso', 'curso__materia')

    cursos_info = [_info_curso(request.user, ins.curso) for ins in inscripciones]

    total_lecciones_ok = sum(c['completadas'] for c in cursos_info)
    total_cursos = len(cursos_info)
    cursos_completos = sum(1 for c in cursos_info if c['completado'])
    total_certs = Certificado.objects.filter(
        estudiante=request.user, estado='emitido'
    ).count()
    total_logros = LogroUsuario.objects.filter(usuario=request.user).count()
    logros_disponibles = Logro.objects.filter(activo=True).count()

    # Rango
    puntos = perfil.puntos
    if puntos < 100:
        rango = ("Aprendiz de Idiomas", 100)
    elif puntos < 500:
        rango = ("Interprete Cultural", 500)
    else:
        rango = ("Sabio Licenciado", None)
    if rango[1]:
        sig_umbral = rango[1]
        pct_sig = int(puntos * 100 / sig_umbral)
        faltan = max(0, sig_umbral - puntos)
    else:
        sig_umbral = None
        pct_sig = 100
        faltan = 0

    # Actividad reciente
    actividad = ProgresoEstudiante.objects.filter(
        estudiante=request.user, completada=True
    ).select_related('leccion', 'leccion__curso').order_by('-fecha_completado')[:10]

    return render(request, 'users/alumno/home.html', {
        'seccion': 'home',
        'perfil': perfil,
        'cursos_info': cursos_info,
        'total_cursos': total_cursos,
        'total_lecciones_ok': total_lecciones_ok,
        'cursos_completos': cursos_completos,
        'total_certs': total_certs,
        'total_logros': total_logros,
        'logros_disponibles': logros_disponibles,
        'puntos': puntos,
        'rango_nombre': rango[0],
        'sig_umbral': sig_umbral,
        'pct_sig': pct_sig,
        'faltan': faltan,
        'racha': _racha(request.user),
        'actividad': actividad,
    })


# ==================== MIS CURSOS ====================
@login_required
def alumno_cursos(request):
    inscripciones = Inscripcion.objects.filter(
        estudiante=request.user, activa=True
    ).select_related('curso', 'curso__materia', 'curso__profesor')

    cursos_info = [_info_curso(request.user, ins.curso) for ins in inscripciones]

    return render(request, 'users/alumno/cursos.html', {
        'seccion': 'cursos',
        'cursos_info': cursos_info,
        'total': len(cursos_info),
    })


# ==================== MIS CERTIFICADOS ====================
@login_required
def alumno_certificados(request):
    certificados = Certificado.objects.filter(
        estudiante=request.user
    ).select_related('curso', 'curso__materia', 'curso__profesor').order_by('-fecha_emision')

    return render(request, 'users/alumno/certificados.html', {
        'seccion': 'certificados',
        'certificados': certificados,
        'total': certificados.count(),
    })


# ==================== MIS LOGROS ====================
@login_required
def alumno_logros(request):
    ganados = LogroUsuario.objects.filter(
        usuario=request.user
    ).select_related('logro').order_by('-fecha_desbloqueo')

    ganados_ids = [lu.logro_id for lu in ganados]
    pendientes = Logro.objects.filter(activo=True).exclude(id__in=ganados_ids)

    return render(request, 'users/alumno/logros.html', {
        'seccion': 'logros',
        'ganados': ganados,
        'pendientes': pendientes,
        'total_ganados': ganados.count(),
        'total_disponibles': Logro.objects.filter(activo=True).count(),
    })


# ==================== CERTIFICADO PUBLICO (mejorado) ====================
def certificado_publico(request, codigo):
    """Vista publica verificable del certificado."""
    cert = get_object_or_404(Certificado, codigo=codigo)
    # Comprobar si el que mira es el dueño o un profesor de sus cursos
    es_dueno = request.user.is_authenticated and request.user.id == cert.estudiante_id
    es_profesor = False
    if request.user.is_authenticated:
        if request.user.is_superuser or cert.curso.profesor_id == request.user.id:
            es_profesor = True

    return render(request, 'users/certificado_publico.html', {
        'cert': cert,
        'es_dueno': es_dueno,
        'es_profesor': es_profesor,
    })


# ==================== RANKING (alumno) ====================
@login_required
def alumno_curso_ranking(request, curso_id):
    """Ranking de estudiantes de un curso (vista del alumno)."""
    curso = get_object_or_404(Curso, id=curso_id)

    # Verificar que el alumno esta inscrito
    if not Inscripcion.objects.filter(
        estudiante=request.user, curso=curso, activa=True
    ).exists():
        messages.error(request, "No estas inscrito en este curso.")
        return redirect('users:alumno_cursos')

    from .ranking_utils import calcular_ranking
    ranking = calcular_ranking(curso, request.user)

    # Mi posicion
    mi_pos = None
    for r in ranking:
        if r['es_yo']:
            mi_pos = r
            break

    return render(request, 'users/alumno/ranking.html', {
        'seccion': 'cursos',
        'curso': curso,
        'ranking': ranking,
        'total': len(ranking),
        'mi_pos': mi_pos,
    })
