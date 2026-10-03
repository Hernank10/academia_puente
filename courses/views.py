# courses/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from .models import Curso, Leccion, RecursoInteractivo


# ═══════════════════════════════════════════════════════════
# HOME / CURSOS
# ═══════════════════════════════════════════════════════════

def _normalizar(s):
    """Normaliza para comparar respuestas cortas."""
    import unicodedata
    if not s:
        return ""
    s = s.lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def _calificar_pregunta(pregunta, datos):
    """Devuelve (es_correcta, puntaje_obtenido, detalle)."""
    tipo = getattr(pregunta, "tipo", "unica")
    puntaje = pregunta.puntaje or 10

    if tipo == "unica":
        opcion_id = datos.get("opcion_" + str(pregunta.id))
        if not opcion_id:
            return (False, 0, "Sin responder")
        try:
            op = OpcionRespuesta.objects.get(id=opcion_id)
            correcto = op.es_correcta
            return (correcto, puntaje if correcto else 0, op.texto)
        except OpcionRespuesta.DoesNotExist:
            return (False, 0, "Opcion invalida")

    if tipo == "multiple":
        ids = datos.getlist("opciones_" + str(pregunta.id))
        if not ids:
            return (False, 0, "Sin responder")
        ids = set(int(i) for i in ids if i.isdigit())
        correctas = set(pregunta.opciones.filter(es_correcta=True).values_list("id", flat=True))
        acierto = (ids == correctas)
        return (acierto, puntaje if acierto else 0,
                "Marcadas: {}".format(", ".join(str(i) for i in sorted(ids))))

    if tipo == "vf":
        resp = datos.get("vf_" + str(pregunta.id))
        if not resp:
            return (False, 0, "Sin responder")
        primera = pregunta.opciones.order_by("orden").first()
        correcta_txt = "V" if (primera and primera.es_correcta) else "F"
        acierto = (resp == correcta_txt)
        return (acierto, puntaje if acierto else 0, resp)

    if tipo == "corta":
        resp = datos.get("corta_" + str(pregunta.id), "")
        if not resp.strip():
            return (False, 0, "Sin responder")
        norm = _normalizar(resp)
        validas = [_normalizar(x) for x in (pregunta.respuesta_corta or "").split("|")]
        validas = [v for v in validas if v]
        acierto = norm in validas
        return (acierto, puntaje if acierto else 0, resp)

    if tipo == "emparejar":
        pares = pregunta.pares_json or []
        if not pares:
            return (False, 0, "Sin pares definidos")
        aciertos = 0
        detalle = []
        for i, par in enumerate(pares):
            r = datos.get("par_{}_{}".format(pregunta.id, i), "")
            esperado = par.get("der", "")
            ok = (_normalizar(r) == _normalizar(esperado))
            if ok:
                aciertos += 1
            detalle.append("{}:{}".format(par.get("izq", ""), r or "—"))
        correcto = (aciertos == len(pares))
        pts = int(puntaje * aciertos / len(pares)) if len(pares) else 0
        return (correcto, pts, " | ".join(detalle))

    return (False, 0, "Tipo desconocido")


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
    """Visor tipo presentacion con navegacion anterior/siguiente."""
    recurso = get_object_or_404(RecursoInteractivo, slug=slug, activo=True)

    # Lista completa ordenada para navegacion
    todos = list(RecursoInteractivo.objects.filter(activo=True).order_by('tipo', 'orden', 'titulo'))
    total = len(todos)

    # Posicion actual
    try:
        posicion = todos.index(recurso) + 1
    except ValueError:
        posicion = 0

    # Anterior y siguiente (circular)
    recurso_anterior = None
    recurso_siguiente = None
    if total > 1 and posicion > 0:
        idx = posicion - 1
        recurso_anterior = todos[(idx - 1) % total]
        recurso_siguiente = todos[(idx + 1) % total]

    return render(request, 'courses/recurso_detalle.html', {
        'recurso': recurso,
        'recurso_anterior': recurso_anterior,
        'recurso_siguiente': recurso_siguiente,
        'posicion': posicion,
        'total_recursos': total,
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
