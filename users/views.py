# users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Sum

from courses.models import (
    Curso, Inscripcion, ProgresoEstudiante,
    Certificado, emitir_certificado,
    Tarea, Entrega,
)
from .models import (
    Perfil, Logro, LogroUsuario,
    calcular_rango, verificar_logros
)
from .decorators import profesor_required, estudiante_required


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def redirigir_por_rol(user):
    """Redirige al dashboard correcto según el rol del usuario."""
    perfil = getattr(user, 'perfil', None)
    if perfil and perfil.rol_principal == 'profesor':
        return redirect('users:dashboard_profesor')
    return redirect('users:dashboard')


# ═══════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════

def registro(request):
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        rol = request.POST.get('rol', 'estudiante')

        errores = []
        if not username or len(username) < 3:
            errores.append({
                "campo": "username",
                "msg": "El usuario debe tener al menos 3 caracteres."
            })
        if User.objects.filter(username=username).exists():
            errores.append({
                "campo": "username",
                "msg": f"El usuario «{username}» ya está en uso. Prueba con otro."
            })
        if email and User.objects.filter(email=email).exists():

            existente = User.objects.filter(email=email).first()

            errores.append(

                f"El email «{email}» ya está registrado como «{existente.username}». "

                f"Si eres tú, inicia sesión en /cuenta/login/. "

                f"Si no, usa otro email."

            )
        if len(password1) < 6:
            errores.append({
                "campo": "password1",
                "msg": "La contraseña debe tener al menos 6 caracteres."
            })
        if password1 != password2:
            errores.append({
                "campo": "password2",
                "msg": "Las contraseñas no coinciden."
            })
        if rol not in ('estudiante', 'profesor'):
            rol = 'estudiante'

        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'users/registro.html', {
                'username': username, 'email': email, 'rol': rol,
            })

        user = User.objects.create_user(username=username, email=email, password=password1)

        # Asignar el rol
        perfil, _ = Perfil.objects.get_or_create(usuario=user)
        perfil.rol_principal = rol
        if rol == 'profesor':
            perfil.puede_publicar_cursos = True
        perfil.save()

        login(request, user)
        messages.success(request, f"¡Bienvenido, {username}!")
        return redirigir_por_rol(user)

    return render(request, 'users/registro.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"¡Hola de nuevo, {user.username}!")
            next_url = request.GET.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirigir_por_rol(user)
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect('courses:index')


# ═══════════════════════════════════════════════════════════
# PERFIL (común a ambos roles)
# ═══════════════════════════════════════════════════════════

@login_required
def perfil(request):
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()

        perfil_obj.biografia = request.POST.get('biografia', '').strip()
        perfil_obj.idioma_nativo = request.POST.get('idioma_nativo', 'es')
        perfil_obj.variante_interes = request.POST.get('variante_interes', 'lat')
        perfil_obj.zona_horaria = request.POST.get('zona_horaria', 'UTC')
        perfil_obj.areas_especialidad = request.POST.get('areas_especialidad', '').strip()
        perfil_obj.estado_academico = request.POST.get('estado_academico', 'grado')
        perfil_obj.save()

        messages.success(request, "Perfil actualizado.")
        return redirect('users:perfil')

    return render(request, 'users/perfil.html', {'perfil': perfil_obj})


# ═══════════════════════════════════════════════════════════
# DASHBOARD ESTUDIANTE
# ═══════════════════════════════════════════════════════════

@login_required
def dashboard(request):
    """Dashboard del estudiante (gamificación + certificados)."""
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=request.user)

    # Si es profesor, redirigir a su dashboard
    if perfil_obj.rol_principal == 'profesor':
        return redirect('users:dashboard_profesor')

    # Verificar y otorgar logros
    nuevos = verificar_logros(request.user)
    for codigo in nuevos:
        try:
            logro = Logro.objects.get(codigo=codigo)
            messages.success(request, f"{logro.icono} ¡Nuevo logro: {logro.nombre}!")
        except Logro.DoesNotExist:
            pass

    # Inscripciones + emisión automática de certificados
    inscripciones = Inscripcion.objects.filter(
        estudiante=request.user, activa=True
    ).select_related('curso')

    for ins in inscripciones:
        cert, creado = emitir_certificado(request.user, ins.curso)
        if creado:
            messages.success(request, f"🎓 ¡Certificado emitido para {ins.curso.titulo}!")

    # Rango
    rango_nombre, rango_icono, siguiente_umbral = calcular_rango(perfil_obj.puntos)
    pct_siguiente = 0
    puntos_faltan = 0
    if siguiente_umbral:
        pct_siguiente = min(100, int(perfil_obj.puntos * 100 / siguiente_umbral))
        puntos_faltan = max(0, siguiente_umbral - perfil_obj.puntos)
    else:
        pct_siguiente = 100

    total_lecciones_completadas = ProgresoEstudiante.objects.filter(
        estudiante=request.user, completada=True
    ).count()

    cursos_inscritos_ids = [i.curso_id for i in inscripciones]
    cursos_disponibles = Curso.objects.exclude(id__in=cursos_inscritos_ids)[:6]

    logros_usuario = LogroUsuario.objects.filter(
        usuario=request.user
    ).select_related('logro').order_by('-fecha_desbloqueo')

    logros_ganados_ids = [lu.logro_id for lu in logros_usuario]
    logros_pendientes = Logro.objects.filter(
        activo=True
    ).exclude(id__in=logros_ganados_ids)[:6]

    certificados = Certificado.objects.filter(
        estudiante=request.user, estado='emitido'
    ).select_related('curso').order_by('-fecha_emision')

    return render(request, 'users/dashboard.html', {
        'perfil': perfil_obj,
        'inscripciones': inscripciones,
        'cursos_disponibles': cursos_disponibles,
        'total_inscripciones': inscripciones.count(),
        'total_lecciones_completadas': total_lecciones_completadas,
        'total_puntos': perfil_obj.puntos,
        'rango_nombre': rango_nombre,
        'rango_icono': rango_icono,
        'siguiente_umbral': siguiente_umbral,
        'pct_siguiente': pct_siguiente,
        'puntos_faltan': puntos_faltan,
        'logros_usuario': logros_usuario,
        'logros_pendientes': logros_pendientes,
        'total_logros': logros_usuario.count(),
        'logros_disponibles': Logro.objects.filter(activo=True).count(),
        'certificados': certificados,
        'total_certificados': certificados.count(),
    })


@login_required
def inscribirse(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscripcion, creada = Inscripcion.objects.get_or_create(
        estudiante=request.user, curso=curso, defaults={'activa': True}
    )
    if creada:
        messages.success(request, f"Te has inscrito en: {curso.titulo}")
        verificar_logros(request.user)
    else:
        messages.info(request, f"Ya estabas inscrito en: {curso.titulo}")
    return redirect('users:dashboard')


# ═══════════════════════════════════════════════════════════
# DASHBOARD PROFESOR
# ═══════════════════════════════════════════════════════════

@login_required
@profesor_required
def dashboard_profesor(request):
    """Dashboard del profesor con estadísticas completas."""
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=request.user)

    # Cursos del profesor con contadores
    cursos = Curso.objects.filter(profesor=request.user).annotate(
        total_lecciones=Count('lecciones', distinct=True),
        total_inscritos=Count('inscritos', distinct=True),
    )

    cursos_ids = [c.id for c in cursos]

    # Estadísticas globales
    estudiantes_unicos = Inscripcion.objects.filter(
        curso_id__in=cursos_ids, activa=True
    ).values('estudiante').distinct().count()

    lecciones_completadas = ProgresoEstudiante.objects.filter(
        leccion__curso_id__in=cursos_ids, completada=True
    ).count()

    certificados_emitidos = Certificado.objects.filter(
        curso_id__in=cursos_ids, estado='emitido'
    ).count()

    # Entregas pendientes de calificar
    entregas_pendientes = Entrega.objects.filter(
        tarea__curso_id__in=cursos_ids,
        estado='entregada',
        calificacion__isnull=True
    ).count()

    # Total de tareas
    total_tareas = Tarea.objects.filter(curso_id__in=cursos_ids).count()

    # Tareas recientes
    tareas_recientes = Tarea.objects.filter(
        curso_id__in=cursos_ids
    ).select_related('curso').order_by('-creada')[:5]

    # Últimos estudiantes inscritos
    ultimos_inscritos = Inscripcion.objects.filter(
        curso_id__in=cursos_ids, activa=True
    ).select_related('estudiante', 'curso').order_by('-fecha_inscripcion')[:8]

    # Top estudiantes por puntos (solo de sus cursos)
    estudiantes_ids = Inscripcion.objects.filter(
        curso_id__in=cursos_ids, activa=True
    ).values_list('estudiante_id', flat=True).distinct()

    top_estudiantes = Perfil.objects.filter(
        usuario_id__in=estudiantes_ids
    ).select_related('usuario').order_by('-puntos')[:5]

    return render(request, 'users/dashboard_profesor.html', {
        'perfil': perfil_obj,
        'cursos': cursos,
        'total_cursos': cursos.count(),
        'total_estudiantes': estudiantes_unicos,
        'total_lecciones_completadas': lecciones_completadas,
        'total_certificados': certificados_emitidos,
        'entregas_pendientes': entregas_pendientes,
        'total_tareas': total_tareas,
        'tareas_recientes': tareas_recientes,
        'ultimos_inscritos': ultimos_inscritos,
        'top_estudiantes': top_estudiantes,
    })

# ═══════════════════════════════════════════════════════════
# CERTIFICADOS (públicos)
# ═══════════════════════════════════════════════════════════

def certificado_detalle(request, codigo):
    cert = get_object_or_404(Certificado, codigo=codigo, estado='emitido')
    return render(request, 'users/certificado_detalle.html', {'cert': cert})


def certificado_verificar(request):
    codigo = request.GET.get('codigo', '').strip()
    cert = None
    error = None

    if codigo:
        try:
            cert = Certificado.objects.get(codigo=codigo, estado='emitido')
        except Certificado.DoesNotExist:
            error = f"No se encontró ningún certificado con el código «{codigo}»."

    return render(request, 'users/certificado_verificar.html', {
        'codigo': codigo, 'cert': cert, 'error': error,
    })


# ═══════════════════════════════════════════════════════════
# PANEL DEL PROFESOR - VISTAS DETALLADAS
# ═══════════════════════════════════════════════════════════

from django.utils import timezone
from django.db.models import Avg, Max


@login_required
@profesor_required
def profesor_curso_detalle(request, curso_id):
    """Detalle de un curso: estudiantes, progreso, tareas y entregas."""
    curso = get_object_or_404(Curso, id=curso_id, profesor=request.user)

    # Lista de estudiantes inscritos con su progreso
    inscripciones = Inscripcion.objects.filter(
        curso=curso, activa=True
    ).select_related('estudiante')

    total_lecciones = curso.lecciones.count()

    estudiantes_info = []
    for ins in inscripciones:
        estudiante = ins.estudiante
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=estudiante, leccion__curso=curso, completada=True
        ).count()
        progreso_pct = int(completadas * 100 / total_lecciones) if total_lecciones else 0

        # Entregas del estudiante en este curso
        entregas = Entrega.objects.filter(
            estudiante=estudiante,
            tarea__curso=curso
        )
        entregas_pendientes = entregas.filter(estado='entregada', calificacion__isnull=True).count()
        entregas_calificadas = entregas.filter(estado='calificada').count()

        # Promedio de calificaciones
        promedio = entregas.filter(calificacion__isnull=False).aggregate(
            avg=Avg('calificacion')
        )['avg'] or 0

        estudiantes_info.append({
            'estudiante': estudiante,
            'perfil': getattr(estudiante, 'perfil', None),
            'completadas': completadas,
            'total': total_lecciones,
            'progreso_pct': progreso_pct,
            'entregas_pendientes': entregas_pendientes,
            'entregas_calificadas': entregas_calificadas,
            'promedio': round(promedio, 1),
        })

    # Ordenar por progreso descendente
    estudiantes_info.sort(key=lambda x: x['progreso_pct'], reverse=True)

    # Tareas del curso
    tareas = curso.tareas.all()

    return render(request, 'users/profesor_curso_detalle.html', {
        'curso': curso,
        'estudiantes_info': estudiantes_info,
        'total_estudiantes': len(estudiantes_info),
        'total_lecciones': total_lecciones,
        'tareas': tareas,
    })


@login_required
@profesor_required
def profesor_estudiante_detalle(request, curso_id, estudiante_id):
    """Detalle del progreso de un estudiante en un curso."""
    curso = get_object_or_404(Curso, id=curso_id, profesor=request.user)
    estudiante = get_object_or_404(User, id=estudiante_id)

    # Verificar que está inscrito
    inscripcion = get_object_or_404(Inscripcion, curso=curso, estudiante=estudiante)

    # Progreso por lección
    lecciones = curso.lecciones.all().order_by('orden')
    progreso_dict = {
        p.leccion_id: p
        for p in ProgresoEstudiante.objects.filter(
            estudiante=estudiante, leccion__curso=curso
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

    completadas = sum(1 for x in lecciones_info if x['completada'])
    total = len(lecciones_info)
    progreso_pct = int(completadas * 100 / total) if total else 0

    # Entregas del estudiante
    entregas = Entrega.objects.filter(
        estudiante=estudiante, tarea__curso=curso
    ).select_related('tarea')

    return render(request, 'users/profesor_estudiante_detalle.html', {
        'curso': curso,
        'estudiante': estudiante,
        'perfil': getattr(estudiante, 'perfil', None),
        'lecciones_info': lecciones_info,
        'completadas': completadas,
        'total': total,
        'progreso_pct': progreso_pct,
        'entregas': entregas,
        'inscripcion': inscripcion,
    })


@login_required
@profesor_required
def profesor_entregas(request, curso_id):
    """Lista de todas las entregas de un curso."""
    curso = get_object_or_404(Curso, id=curso_id, profesor=request.user)

    entregas = Entrega.objects.filter(
        tarea__curso=curso
    ).select_related('estudiante', 'tarea').order_by('-fecha_entrega')

    # Filtros
    estado = request.GET.get('estado', '')
    if estado:
        entregas = entregas.filter(estado=estado)

    return render(request, 'users/profesor_entregas.html', {
        'curso': curso,
        'entregas': entregas,
        'estado_actual': estado,
        'total_pendientes': Entrega.objects.filter(
            tarea__curso=curso, estado='entregada', calificacion__isnull=True
        ).count(),
    })


@login_required
@profesor_required
def profesor_calificar(request, entrega_id):
    """Formulario para calificar una entrega."""
    entrega = get_object_or_404(
        Entrega, id=entrega_id,
        tarea__curso__profesor=request.user
    )

    if request.method == 'POST':
        calificacion = request.POST.get('calificacion', '')
        retro = request.POST.get('retroalimentacion', '').strip()
        estado = request.POST.get('estado', 'calificada')

        try:
            entrega.calificacion = int(calificacion) if calificacion else None
        except ValueError:
            entrega.calificacion = None

        entrega.retroalimentacion = retro
        entrega.estado = estado
        if estado == 'calificada':
            entrega.fecha_calificacion = timezone.now()
        entrega.save()

        # Sumar puntos al estudiante
        if entrega.calificacion and estado == 'calificada':
            perfil, _ = Perfil.objects.get_or_create(usuario=entrega.estudiante)
            perfil.puntos += entrega.calificacion
            perfil.save()

        messages.success(request, "Entrega calificada.")
        return redirect('users:profesor_entregas', curso_id=entrega.tarea.curso.id)

    return render(request, 'users/profesor_calificar.html', {
        'entrega': entrega,
    })
