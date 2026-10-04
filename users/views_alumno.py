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


# ==================== ESTADISTICAS (alumno) ====================
@login_required
def alumno_estadisticas(request):
    """Panel de estadisticas personales con graficos Chart.js."""
    import json
    from datetime import timedelta
    from django.db.models import Count, Avg
    from django.utils import timezone
    from courses.models import IntentoEvaluacion

    perfil = _perfil(request.user)

    # Cursos inscritos
    inscripciones = Inscripcion.objects.filter(
        estudiante=request.user, activa=True
    ).select_related('curso')

    # ============================================================
    # 1. Progreso por curso
    # ============================================================
    progreso_cursos = []
    total_lecciones = 0
    total_completadas = 0
    for ins in inscripciones:
        curso = ins.curso
        n_lec = curso.lecciones.count()
        comp = ProgresoEstudiante.objects.filter(
            estudiante=request.user, leccion__curso=curso, completada=True
        ).count()
        pct = int(comp * 100 / n_lec) if n_lec else 0

        progreso_cursos.append({
            'titulo': curso.titulo[:30],
            'pct': pct,
            'completadas': comp,
            'total': n_lec,
        })

        total_lecciones += n_lec
        total_completadas += comp

    # Ordenar por pct descendente
    progreso_cursos.sort(key=lambda x: -x['pct'])

    # ============================================================
    # 2. Actividad ultimos 30 dias
    # ============================================================
    hoy = timezone.now().date()
    hace_30 = hoy - timedelta(days=29)

    actividad_map = {}
    for i in range(30):
        d = hace_30 + timedelta(days=i)
        actividad_map[d.isoformat()] = 0

    qs_act = ProgresoEstudiante.objects.filter(
        estudiante=request.user,
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
    # 3. Lecciones: completadas vs pendientes (global)
    # ============================================================
    pendientes = max(0, total_lecciones - total_completadas)

    # ============================================================
    # 4. Evolucion de puntos por mes (ultimos 6 meses)
    # ============================================================
    puntos_labels = []
    puntos_valores = []

    for i in range(5, -1, -1):
        # Primer dia del mes hace i meses
        if hoy.month - i <= 0:
            año = hoy.year - 1
            mes = hoy.month - i + 12
        else:
            año = hoy.year
            mes = hoy.month - i

        # Puntos acumulados hasta el final de ese mes
        fecha_fin = None
        try:
            if mes == 12:
                fecha_fin = timezone.datetime(año + 1, 1, 1).date()
            else:
                fecha_fin = timezone.datetime(año, mes + 1, 1).date()
        except Exception:
            fecha_fin = hoy + timedelta(days=1)

        puntos_acumulados = ProgresoEstudiante.objects.filter(
            estudiante=request.user,
            completada=True,
            fecha_completado__date__lt=fecha_fin,
        ).count() * 5

        # Bonus por certificados
        certs = Certificado.objects.filter(
            estudiante=request.user,
            estado='emitido',
            fecha_emision__date__lt=fecha_fin,
        ).count()
        puntos_acumulados += certs * 20

        puntos_labels.append("{}/{}".format(mes, str(año)[-2:]))
        puntos_valores.append(puntos_acumulados)

    # ============================================================
    # 5. Ultimos 10 intentos de evaluaciones
    # ============================================================
    intentos = IntentoEvaluacion.objects.filter(
        estudiante=request.user, completado=True
    ).select_related('evaluacion').order_by('-fecha_inicio')[:10]

    intentos_ordenados = list(reversed(intentos))
    eval_labels = [i.evaluacion.titulo[:20] for i in intentos_ordenados]
    eval_puntajes = [i.puntaje for i in intentos_ordenados]
    eval_maximos = [i.evaluacion.puntaje_maximo for i in intentos_ordenados]
    eval_aprobados = [i.aprobado for i in intentos_ordenados]

    # Convertir a porcentaje
    eval_pcts = []
    for i, p in enumerate(intentos_ordenados):
        mx = eval_maximos[i] if eval_maximos[i] else 100
        eval_pcts.append(int(p * 100 / mx))

    # ============================================================
    # 6. Progreso hacia el siguiente rango
    # ============================================================
    puntos = perfil.puntos
    if puntos < 100:
        rango_actual = "Aprendiz de Idiomas"
        sig_umbral = 100
    elif puntos < 500:
        rango_actual = "Interprete Cultural"
        sig_umbral = 500
    else:
        rango_actual = "Sabio Licenciado"
        sig_umbral = None

    if sig_umbral:
        pct_sig = min(100, int(puntos * 100 / sig_umbral))
    else:
        pct_sig = 100

    # ============================================================
    # Context
    # ============================================================
    context = {
        'seccion': 'estadisticas',
        'perfil': perfil,
        'total_lecciones': total_lecciones,
        'total_completadas': total_completadas,
        'lecciones_pendientes': pendientes,
        'total_cursos': inscripciones.count(),
        'total_intentos': len(intentos_ordenados),
        'puntos': puntos,
        'rango_actual': rango_actual,
        'sig_umbral': sig_umbral,
        'pct_sig': pct_sig,
        # JSON para Chart.js
        'progreso_cursos_json': json.dumps(progreso_cursos),
        'actividad_labels_json': json.dumps(actividad_labels),
        'actividad_valores_json': json.dumps(actividad_valores),
        'puntos_labels_json': json.dumps(puntos_labels),
        'puntos_valores_json': json.dumps(puntos_valores),
        'eval_labels_json': json.dumps(eval_labels),
        'eval_pcts_json': json.dumps(eval_pcts),
        'eval_aprobados_json': json.dumps(eval_aprobados),
        'eval_puntajes_json': json.dumps(eval_puntajes),
        'eval_maximos_json': json.dumps(eval_maximos),
    }

    return render(request, 'users/alumno/estadisticas.html', context)
