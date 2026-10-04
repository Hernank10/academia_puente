# -*- coding: utf-8 -*-
"""views_panel.py - Panel administrativo del profesor (fuera del admin Django)."""
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Q
from django.utils import timezone

from courses.models import (
    Curso, Leccion, ProgresoEstudiante, Inscripcion, Certificado,
    Tarea, Entrega, Evaluacion, IntentoEvaluacion,
)
from .models import Perfil
from .views_profesor import profesor_required


def _mis_cursos(request):
    if request.user.is_superuser:
        return Curso.objects.all()
    return Curso.objects.filter(profesor=request.user)


def _mis_cursos_ids(request):
    return list(_mis_cursos(request).values_list('id', flat=True))


def _mis_estudiantes_ids(request):
    return Inscripcion.objects.filter(
        curso_id__in=_mis_cursos_ids(request), activa=True
    ).values_list('estudiante_id', flat=True).distinct()


# ==================== HOME ====================
@login_required
@profesor_required
def panel_home(request):
    cursos_ids = _mis_cursos_ids(request)
    cursos = Curso.objects.filter(id__in=cursos_ids)

    total_cursos = cursos.count()
    total_estudiantes = _mis_estudiantes_ids(request).count()
    total_lecciones = Leccion.objects.filter(curso_id__in=cursos_ids).count()
    lecciones_completadas = ProgresoEstudiante.objects.filter(
        leccion__curso_id__in=cursos_ids, completada=True
    ).count()
    total_certificados = Certificado.objects.filter(
        curso_id__in=cursos_ids, estado='emitido'
    ).count()
    entregas_pendientes = Entrega.objects.filter(
        tarea__curso_id__in=cursos_ids,
        calificacion__isnull=True
    ).count()
    total_evaluaciones = Evaluacion.objects.filter(curso_id__in=cursos_ids).count()

    actividad = Inscripcion.objects.filter(
        curso_id__in=cursos_ids, activa=True
    ).select_related('estudiante', 'curso').order_by('-fecha_inscripcion')[:12]

    cursos_info = []
    for c in cursos.order_by('-id')[:6]:
        inscritos = c.inscritos.filter(activa=True).count()
        lecciones = c.lecciones.count()
        completadas = ProgresoEstudiante.objects.filter(
            leccion__curso=c, completada=True
        ).count()
        pct = int(completadas * 100 / (inscritos * lecciones)) if (inscritos and lecciones) else 0
        cursos_info.append({
            'curso': c,
            'inscritos': inscritos,
            'lecciones': lecciones,
            'completadas': completadas,
            'pct': min(pct, 100),
        })

    return render(request, 'users/panel/home.html', {
        'seccion': 'home',
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_lecciones': total_lecciones,
        'lecciones_completadas': lecciones_completadas,
        'total_certificados': total_certificados,
        'entregas_pendientes': entregas_pendientes,
        'total_evaluaciones': total_evaluaciones,
        'actividad': actividad,
        'cursos_info': cursos_info,
    })


# ==================== CURSOS ====================
@login_required
@profesor_required
def panel_cursos(request):
    cursos = _mis_cursos(request).annotate(
        n_inscritos=Count('inscritos', filter=Q(inscritos__activa=True), distinct=True),
        n_lecciones=Count('lecciones', distinct=True),
        n_evaluaciones=Count('evaluaciones', distinct=True),
        n_tareas=Count('tareas', distinct=True),
    ).order_by('-id')
    return render(request, 'users/panel/cursos.html', {
        'seccion': 'cursos',
        'cursos': cursos,
    })


# ==================== ESTUDIANTES ====================
@login_required
@profesor_required
def panel_estudiantes(request):
    cursos_ids = _mis_cursos_ids(request)
    q = request.GET.get('q', '').strip()
    curso_id = request.GET.get('curso', '').strip()

    inscripciones = Inscripcion.objects.filter(
        curso_id__in=cursos_ids, activa=True
    ).select_related('estudiante', 'curso')

    if curso_id:
        inscripciones = inscripciones.filter(curso_id=curso_id)
    if q:
        inscripciones = inscripciones.filter(
            Q(estudiante__username__icontains=q) |
            Q(estudiante__first_name__icontains=q) |
            Q(estudiante__last_name__icontains=q) |
            Q(estudiante__email__icontains=q)
        )

    estudiantes_dict = {}
    for ins in inscripciones:
        eid = ins.estudiante_id
        if eid not in estudiantes_dict:
            estudiantes_dict[eid] = {
                'estudiante': ins.estudiante,
                'perfil': getattr(ins.estudiante, 'perfil', None),
                'cursos': [],
            }
        estudiantes_dict[eid]['cursos'].append(ins.curso)

    estudiantes = list(estudiantes_dict.values())
    estudiantes.sort(key=lambda x: x['estudiante'].username)

    return render(request, 'users/panel/estudiantes.html', {
        'seccion': 'estudiantes',
        'estudiantes': estudiantes,
        'total': len(estudiantes),
        'q': q,
        'curso_id': curso_id,
        'cursos': _mis_cursos(request),
    })


@login_required
@profesor_required
def panel_estudiante_detalle(request, estudiante_id):
    estudiante = get_object_or_404(User, id=estudiante_id)
    cursos_ids = _mis_cursos_ids(request)

    inscripciones = Inscripcion.objects.filter(
        estudiante=estudiante, curso_id__in=cursos_ids, activa=True
    ).select_related('curso')

    if not inscripciones.exists():
        messages.error(request, "Este estudiante no esta en tus cursos.")
        return redirect('users:panel_estudiantes')

    cursos_info = []
    for ins in inscripciones:
        curso = ins.curso
        total = curso.lecciones.count()
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=estudiante, leccion__curso=curso, completada=True
        ).count()
        pct = int(completadas * 100 / total) if total else 0

        entregas = Entrega.objects.filter(
            estudiante=estudiante, tarea__curso=curso
        ).select_related('tarea').order_by('-fecha_entrega')

        intentos = IntentoEvaluacion.objects.filter(
            estudiante=estudiante, evaluacion__curso=curso, completado=True
        ).select_related('evaluacion').order_by('-fecha_inicio')

        cert = Certificado.objects.filter(
            estudiante=estudiante, curso=curso, estado='emitido'
        ).first()

        cursos_info.append({
            'curso': curso,
            'total': total,
            'completadas': completadas,
            'pct': pct,
            'entregas': entregas,
            'intentos': intentos,
            'certificado': cert,
        })

    actividad = ProgresoEstudiante.objects.filter(
        estudiante=estudiante, leccion__curso_id__in=cursos_ids, completada=True
    ).select_related('leccion', 'leccion__curso').order_by('-fecha_completado')[:25]

    return render(request, 'users/panel/estudiante_detalle.html', {
        'seccion': 'estudiantes',
        'estudiante': estudiante,
        'perfil': getattr(estudiante, 'perfil', None),
        'cursos_info': cursos_info,
        'actividad': actividad,
    })


# ==================== EVALUACIONES ====================
@login_required
@profesor_required
def panel_evaluaciones(request):
    cursos_ids = _mis_cursos_ids(request)
    evs = Evaluacion.objects.filter(curso_id__in=cursos_ids).select_related('curso').order_by('-creada')

    evs_info = []
    for ev in evs:
        total_intentos = ev.intentos.filter(completado=True).count()
        aprobados = ev.intentos.filter(completado=True, aprobado=True).count()
        tasa = int(aprobados * 100 / total_intentos) if total_intentos else 0
        promedio = ev.intentos.filter(completado=True).aggregate(a=Avg('puntaje'))['a']
        evs_info.append({
            'ev': ev,
            'total_preguntas': ev.preguntas.count(),
            'total_intentos': total_intentos,
            'aprobados': aprobados,
            'tasa': tasa,
            'promedio': round(promedio, 1) if promedio else 0,
        })

    return render(request, 'users/panel/evaluaciones.html', {
        'seccion': 'evaluaciones',
        'evs_info': evs_info,
        'total': len(evs_info),
    })


# ==================== ENTREGAS ====================
@login_required
@profesor_required
def panel_entregas(request):
    cursos_ids = _mis_cursos_ids(request)
    estado = request.GET.get('estado', 'pendientes').strip()
    curso_id = request.GET.get('curso', '').strip()

    qs = Entrega.objects.filter(
        tarea__curso_id__in=cursos_ids
    ).select_related('estudiante', 'tarea', 'tarea__curso')

    if estado == 'pendientes':
        qs = qs.filter(calificacion__isnull=True)
    elif estado == 'calificadas':
        qs = qs.filter(calificacion__isnull=False)
    if curso_id:
        qs = qs.filter(tarea__curso_id=curso_id)

    qs = qs.order_by('-fecha_entrega')

    return render(request, 'users/panel/entregas.html', {
        'seccion': 'entregas',
        'entregas': qs,
        'total': qs.count(),
        'estado': estado,
        'curso_id': curso_id,
        'cursos': _mis_cursos(request),
    })


# ==================== CERTIFICADOS ====================
@login_required
@profesor_required
def panel_certificados(request):
    cursos_ids = _mis_cursos_ids(request)
    curso_id = request.GET.get('curso', '').strip()

    qs = Certificado.objects.filter(
        curso_id__in=cursos_ids
    ).select_related('estudiante', 'curso').order_by('-fecha_emision')

    if curso_id:
        qs = qs.filter(curso_id=curso_id)

    return render(request, 'users/panel/certificados.html', {
        'seccion': 'certificados',
        'certificados': qs,
        'total': qs.count(),
        'curso_id': curso_id,
        'cursos': _mis_cursos(request),
    })


@login_required
@profesor_required
def panel_certificado_emitir(request):
    cursos_ids = _mis_cursos_ids(request)

    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        curso_id = request.POST.get('curso_id')

        try:
            estudiante = User.objects.get(id=estudiante_id)
            curso = Curso.objects.get(id=curso_id, id__in=cursos_ids)
        except (User.DoesNotExist, Curso.DoesNotExist):
            messages.error(request, "Estudiante o curso invalido.")
            return redirect('users:panel_certificados')

        # Verificar que el estudiante este inscrito
        if not Inscripcion.objects.filter(estudiante=estudiante, curso=curso, activa=True).exists():
            messages.error(request, "El estudiante no esta inscrito en ese curso.")
            return redirect('users:panel_certificados')

        cert, created = Certificado.objects.get_or_create(
            estudiante=estudiante, curso=curso,
            defaults={
                'puntos_obtenidos': curso.lecciones.count() * 10,
                'calificacion': 'Aprobado',
                'estado': 'emitido',
            }
        )
        if created:
            messages.success(request, "Certificado emitido: " + cert.codigo)
        else:
            messages.info(request, "Ya existia un certificado para ese par.")
        return redirect('users:panel_certificados')

    # GET: mostrar formulario
    estudiantes = User.objects.filter(
        id__in=_mis_estudiantes_ids(request)
    ).order_by('username')

    return render(request, 'users/panel/certificado_emitir.html', {
        'seccion': 'certificados',
        'estudiantes': estudiantes,
        'cursos': _mis_cursos(request),
    })


@login_required
@profesor_required
def panel_certificado_revocar(request, cert_id):
    cursos_ids = _mis_cursos_ids(request)
    cert = get_object_or_404(Certificado, id=cert_id, curso_id__in=cursos_ids)

    if request.method == 'POST':
        cert.estado = 'revocado'
        cert.save()
        messages.warning(request, "Certificado revocado: " + cert.codigo)
        return redirect('users:panel_certificados')

    return render(request, 'users/panel/certificado_revocar.html', {
        'seccion': 'certificados',
        'cert': cert,
    })


# ==================== RANKING ====================
@login_required
@profesor_required
def panel_curso_ranking(request, curso_id):
    """Ranking de estudiantes de un curso (vista del profesor)."""
    curso = get_object_or_404(Curso, id=curso_id)
    if not request.user.is_superuser and curso.profesor != request.user:
        messages.error(request, "Sin permiso.")
        return redirect('users:panel_home')

    from .ranking_utils import calcular_ranking
    ranking = calcular_ranking(curso, request.user)

    return render(request, 'users/panel/ranking.html', {
        'seccion': 'cursos',
        'curso': curso,
        'ranking': ranking,
        'total': len(ranking),
    })


# ==================== ESTADISTICAS ====================
@login_required
@profesor_required
def panel_estadisticas(request):
    """Panel de estadisticas con graficos Chart.js."""
    import json
    from datetime import timedelta
    from django.db.models import Count, Avg
    from django.utils import timezone

    cursos_ids = _mis_cursos_ids(request)
    cursos = Curso.objects.filter(id__in=cursos_ids)

    # Totales generales
    total_cursos = cursos.count()
    total_estudiantes = _mis_estudiantes_ids(request).count()
    total_lecciones = Leccion.objects.filter(curso_id__in=cursos_ids).count()
    total_completadas = ProgresoEstudiante.objects.filter(
        leccion__curso_id__in=cursos_ids, completada=True
    ).count()
    total_evaluaciones = Evaluacion.objects.filter(curso_id__in=cursos_ids).count()

    intentos_todos = IntentoEvaluacion.objects.filter(
        evaluacion__curso_id__in=cursos_ids, completado=True
    )
    total_intentos = intentos_todos.count()
    aprobados = intentos_todos.filter(aprobado=True).count()
    tasa_aprobacion = int(aprobados * 100 / total_intentos) if total_intentos else 0

    # ============================================================
    # 1. Top cursos con mas inscritos
    # ============================================================
    cursos_inscritos = []
    for c in cursos:
        n = c.inscritos.filter(activa=True).count()
        cursos_inscritos.append({'titulo': c.titulo[:30], 'inscritos': n})
    cursos_inscritos.sort(key=lambda x: -x['inscritos'])
    cursos_inscritos = cursos_inscritos[:10]

    # ============================================================
    # 2. Progreso promedio por curso
    # ============================================================
    cursos_progreso = []
    for c in cursos:
        n_lec = c.lecciones.count()
        n_ins = c.inscritos.filter(activa=True).count()
        total_posible = n_lec * n_ins
        completadas = ProgresoEstudiante.objects.filter(
            leccion__curso=c, completada=True
        ).count()
        pct = int(completadas * 100 / total_posible) if total_posible else 0
        cursos_progreso.append({
            'titulo': c.titulo[:30],
            'pct': min(pct, 100),
        })
    cursos_progreso.sort(key=lambda x: -x['pct'])
    cursos_progreso = cursos_progreso[:10]

    # ============================================================
    # 3. Actividad ultimos 30 dias
    # ============================================================
    hoy = timezone.now().date()
    hace_30 = hoy - timedelta(days=29)

    actividad_map = {}
    for i in range(30):
        d = hace_30 + timedelta(days=i)
        actividad_map[d.isoformat()] = 0

    qs_act = ProgresoEstudiante.objects.filter(
        leccion__curso_id__in=cursos_ids,
        completada=True,
        fecha_completado__date__gte=hace_30,
    ).values('fecha_completado__date').annotate(n=Count('id'))

    for r in qs_act:
        f = r['fecha_completado__date']
        if f:
            actividad_map[f.isoformat()] = r['n']

    actividad_labels = list(actividad_map.keys())
    actividad_valores = list(actividad_map.values())

    # ============================================================
    # 4. Distribucion por nivel
    # ============================================================
    niveles_map = {}
    for c in cursos:
        n = c.inscritos.filter(activa=True).count()
        nivel = c.nivel or 'Sin nivel'
        niveles_map[nivel] = niveles_map.get(nivel, 0) + n
    # Ordenar por nivel
    orden_niveles = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Sin nivel']
    niveles_labels = [n for n in orden_niveles if n in niveles_map]
    niveles_valores = [niveles_map[n] for n in niveles_labels]

    # ============================================================
    # 5. Top 10 estudiantes por puntos
    # ============================================================
    estudiantes_ids = _mis_estudiantes_ids(request)
    top_perfiles = Perfil.objects.filter(
        usuario_id__in=estudiantes_ids
    ).select_related('usuario').order_by('-puntos')[:10]

    top_labels = [p.usuario.username[:15] for p in top_perfiles]
    top_valores = [p.puntos for p in top_perfiles]

    # ============================================================
    # 6. Evaluaciones: aprobados vs reprobados
    # ============================================================
    reprobados = total_intentos - aprobados

    context = {
        'seccion': 'estadisticas',
        'total_cursos': total_cursos,
        'total_estudiantes': total_estudiantes,
        'total_lecciones': total_lecciones,
        'total_completadas': total_completadas,
        'total_evaluaciones': total_evaluaciones,
        'total_intentos': total_intentos,
        'tasa_aprobacion': tasa_aprobacion,
        # JSON para Chart.js
        'cursos_inscritos_json': json.dumps(cursos_inscritos),
        'cursos_progreso_json': json.dumps(cursos_progreso),
        'actividad_labels_json': json.dumps(actividad_labels),
        'actividad_valores_json': json.dumps(actividad_valores),
        'niveles_labels_json': json.dumps(niveles_labels),
        'niveles_valores_json': json.dumps(niveles_valores),
        'top_labels_json': json.dumps(top_labels),
        'top_valores_json': json.dumps(top_valores),
        'eval_aprobados': aprobados,
        'eval_reprobados': reprobados,
    }

    return render(request, 'users/panel/estadisticas.html', context)
