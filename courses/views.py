# courses/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .models import Curso, Leccion, RecursoInteractivo


# ═══════════════════════════════════════════════════════════
# HOME / CURSOS
# ═══════════════════════════════════════════════════════════

def index(request):
    """Vista principal: cursos agrupados por materia + recursos."""
    # Cursos con conteo de lecciones
    cursos = Curso.objects.annotate(
        n_lecciones=Count('lecciones')
    ).select_related('materia').order_by('materia__nombre', 'nivel', 'titulo')

    # Agrupar por materia
    materias = {}
    for c in cursos:
        nombre_mat = c.materia.nombre if c.materia else "Sin materia"
        if nombre_mat not in materias:
            materias[nombre_mat] = []
        materias[nombre_mat].append(c)

    # Recursos
    recursos_count = RecursoInteractivo.objects.filter(activo=True).count()
    tipos_count = {}
    for row in RecursoInteractivo.objects.filter(activo=True).values('tipo').annotate(n=Count('id')):
        tipos_count[row['tipo']] = row['n']
    recursos_destacados = RecursoInteractivo.objects.filter(activo=True)[:12]

    return render(request, 'courses/index.html', {
        'materias': materias,
        'total_cursos': cursos.count(),
        'recursos_count': recursos_count,
        'tipos_count': tipos_count,
        'recursos_destacados': recursos_destacados,
        'tipos': RecursoInteractivo.TIPOS,
    })


# ═══════════════════════════════════════════════════════════
# RECURSOS INTERACTIVOS
# ═══════════════════════════════════════════════════════════

@login_required
def recursos_lista(request):
    """Catálogo de recursos interactivos con filtro por tipo."""
    tipo = request.GET.get('tipo', '').strip()

    qs = RecursoInteractivo.objects.filter(activo=True)
    if tipo:
        qs = qs.filter(tipo=tipo)

    # Conteo por tipo para los filtros
    conteos = {}
    for row in RecursoInteractivo.objects.filter(activo=True).values('tipo').annotate(n=Count('id')):
        conteos[row['tipo']] = row['n']

    return render(request, 'courses/recursos_lista.html', {
        'recursos': qs,
        'tipos': RecursoInteractivo.TIPOS,
        'tipo_actual': tipo,
        'conteos': conteos,
        'total': RecursoInteractivo.objects.filter(activo=True).count(),
    })


@login_required
def recurso_detalle(request, slug):
    """Detalle de un recurso con iframe embebido."""
    recurso = get_object_or_404(RecursoInteractivo, slug=slug, activo=True)
    return render(request, 'courses/recurso_detalle.html', {
        'recurso': recurso,
    })


# ═══════════════════════════════════════════════════════════
# CURSO: DETALLE Y EVALUACIONES
# ═══════════════════════════════════════════════════════════

from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg
from .models import (
    Curso, Leccion, Inscripcion, ProgresoEstudiante,
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
    IntentoEvaluacion, RespuestaIntento,
)
from users.models import Perfil


@login_required
def curso_detalle(request, curso_id):
    """Página del curso: lecciones, evaluaciones y progreso del estudiante."""
    curso = get_object_or_404(Curso, id=curso_id)
    user = request.user

    # ¿Está inscrito?
    inscripcion, creada = Inscripcion.objects.get_or_create(
        estudiante=user, curso=curso,
        defaults={'activa': True}
    )

    # Lecciones con progreso
    lecciones = curso.lecciones.all().order_by('orden')
    progreso_dict = {
        p.leccion_id: p
        for p in ProgresoEstudiante.objects.filter(
            estudiante=user, leccion__curso=curso
        )
    }

    lecciones_info = []
    for lec in lecciones:
        p = progreso_dict.get(lec.id)
        lecciones_info.append({
            'leccion': lec,
            'completada': p.completada if p else False,
            'fecha': p.fecha_completado if p else None,
        })

    total_lecciones = len(lecciones_info)
    completadas = sum(1 for x in lecciones_info if x['completada'])
    progreso_pct = int(completadas * 100 / total_lecciones) if total_lecciones else 0

    # Evaluaciones del curso
    evaluaciones = curso.evaluaciones.filter(estado='publicada')

    # Progreso en evaluaciones
    evaluaciones_info = []
    for ev in evaluaciones:
        mejor_intento = IntentoEvaluacion.objects.filter(
            evaluacion=ev, estudiante=user, completado=True
        ).order_by('-puntaje').first()

        intentos_hechos = IntentoEvaluacion.objects.filter(
            evaluacion=ev, estudiante=user, completado=True
        ).count()

        evaluaciones_info.append({
            'evaluacion': ev,
            'mejor_intento': mejor_intento,
            'intentos_hechos': intentos_hechos,
            'intentos_restantes': max(0, ev.intentos_maximos - intentos_hechos),
        })

    return render(request, 'courses/curso_detalle.html', {
        'curso': curso,
        'inscripcion': inscripcion,
        'lecciones_info': lecciones_info,
        'evaluaciones_info': evaluaciones_info,
        'total_lecciones': total_lecciones,
        'completadas': completadas,
        'progreso_pct': progreso_pct,
    })


@login_required
def marcar_leccion_completada(request, curso_id, leccion_id):
    """Marca una lección como completada."""
    curso = get_object_or_404(Curso, id=curso_id)
    leccion = get_object_or_404(Leccion, id=leccion_id, curso=curso)

    progreso, created = ProgresoEstudiante.objects.get_or_create(
        estudiante=request.user, leccion=leccion,
        defaults={'completada': True}
    )
    if not created and not progreso.completada:
        progreso.completada = True
        progreso.save()

    # Sumar puntos
    if created:
        perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
        perfil.puntos += 5
        perfil.save()

    return redirect('courses:curso_detalle', curso_id=curso.id)


# ═══════════════════════════════════════════════════════════
# EVALUACIONES
# ═══════════════════════════════════════════════════════════

@login_required
def rendir_evaluacion(request, evaluacion_id):
    """El estudiante contesta una evaluación."""
    evaluacion = get_object_or_404(Evaluacion, id=evaluacion_id, estado='publicada')

    # Verificar intentos
    intentos_hechos = IntentoEvaluacion.objects.filter(
        evaluacion=evaluacion, estudiante=request.user, completado=True
    ).count()

    if intentos_hechos >= evaluacion.intentos_maximos:
        messages.warning(request, "Ya has agotado todos los intentos para esta evaluación.")
        return redirect('courses:curso_detalle', curso_id=evaluacion.curso.id)

    # Crear intento nuevo
    if request.method == 'GET':
        intento = IntentoEvaluacion.objects.create(
            evaluacion=evaluacion,
            estudiante=request.user,
        )
        preguntas = evaluacion.preguntas.all().order_by('orden')
        if evaluacion.aleatorizar_preguntas:
            preguntas = preguntas.order_by('?')

        return render(request, 'courses/rendir_evaluacion.html', {
            'evaluacion': evaluacion,
            'intento': intento,
            'preguntas': preguntas,
        })

    # POST: procesar respuestas
    intento_id = request.POST.get('intento_id')
    intento = get_object_or_404(IntentoEvaluacion, id=intento_id, estudiante=request.user)

    puntaje_total = 0
    correctas = 0
    total = 0

    for pregunta in evaluacion.preguntas.all():
        opcion_id = request.POST.get(f'pregunta_{pregunta.id}')
        if not opcion_id:
            continue

        try:
            opcion = OpcionRespuesta.objects.get(id=opcion_id, pregunta=pregunta)
        except OpcionRespuesta.DoesNotExist:
            continue

        RespuestaIntento.objects.create(
            intento=intento,
            pregunta=pregunta,
            opcion_elegida=opcion,
            es_correcta=opcion.es_correcta,
        )

        total += 1
        if opcion.es_correcta:
            puntaje_total += pregunta.puntaje
            correctas += 1

    intento.puntaje = puntaje_total
    intento.aprobado = puntaje_total >= evaluacion.puntaje_aprobacion
    intento.completado = True
    intento.fecha_fin = timezone.now()
    intento.save()

    # Sumar puntos al perfil
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    perfil.puntos += puntaje_total
    perfil.save()

    messages.success(
        request,
        f"¡Evaluación completada! {correctas}/{total} correctas · {puntaje_total} puntos"
    )
    return redirect('courses:resultado_evaluacion', intento_id=intento.id)


@login_required
def resultado_evaluacion(request, intento_id):
    """Muestra el resultado de una evaluación."""
    intento = get_object_or_404(
        IntentoEvaluacion, id=intento_id, estudiante=request.user
    )
    respuestas = intento.respuestas.select_related('pregunta', 'opcion_elegida').all()

    return render(request, 'courses/resultado_evaluacion.html', {
        'intento': intento,
        'evaluacion': intento.evaluacion,
        'respuestas': respuestas,
    })
