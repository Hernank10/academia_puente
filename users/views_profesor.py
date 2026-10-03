# -*- coding: utf-8 -*-
"""views_profesor.py - CRUD completo del panel del profesor."""
from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from courses.models import (
    Curso, Leccion, Tarea, Entrega,
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
)
from .models import Perfil
from .forms_profesor import (
    CursoForm, LeccionForm, TareaForm, EvaluacionForm,
    PreguntaForm, OpcionForm, CalificarEntregaForm,
)


def profesor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("users:login")
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            perfil = request.user.perfil
            if perfil.rol_principal == "profesor" or request.user.is_staff:
                return view_func(request, *args, **kwargs)
        except Perfil.DoesNotExist:
            pass
        messages.error(request, "Solo profesores pueden acceder.")
        return redirect("users:dashboard")
    return wrapper


def _check_curso(request, curso):
    if request.user.is_superuser:
        return True
    return curso.profesor_id == request.user.id


def _url_panel(curso, tab):
    return reverse("users:profesor_curso_detalle", args=[curso.id]) + "?tab=" + tab


# ==================== CURSO ====================
@login_required
@profesor_required
def curso_crear(request):
    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.profesor = request.user
            curso.save()
            messages.success(request, "Curso '" + curso.titulo + "' creado.")
            return redirect("users:dashboard_profesor")
    else:
        form = CursoForm()
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nuevo curso",
        "form": form,
        "accion": "Crear",
        "url_cancelar": reverse("users:dashboard_profesor"),
    })


@login_required
@profesor_required
def curso_editar(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso actualizado.")
            return redirect("users:dashboard_profesor")
    else:
        form = CursoForm(instance=curso)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar curso: " + curso.titulo,
        "form": form,
        "accion": "Guardar",
        "url_cancelar": reverse("users:dashboard_profesor"),
    })


# ==================== LECCION ====================
@login_required
@profesor_required
def leccion_crear(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = LeccionForm(request.POST, request.FILES)
        if form.is_valid():
            lec = form.save(commit=False)
            lec.curso = curso
            lec.save()
            messages.success(request, "Leccion creada.")
            return redirect(_url_panel(curso, "lecciones"))
    else:
        form = LeccionForm(initial={"orden": curso.lecciones.count() + 1})
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nueva leccion en " + curso.titulo,
        "form": form,
        "accion": "Crear",
        "url_cancelar": _url_panel(curso, "lecciones"),
    })


@login_required
@profesor_required
def leccion_editar(request, leccion_id):
    lec = get_object_or_404(Leccion, id=leccion_id)
    if not _check_curso(request, lec.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = LeccionForm(request.POST, request.FILES, instance=lec)
        if form.is_valid():
            form.save()
            messages.success(request, "Leccion actualizada.")
            return redirect(_url_panel(lec.curso, "lecciones"))
    else:
        form = LeccionForm(instance=lec)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar leccion",
        "form": form,
        "accion": "Guardar",
        "url_cancelar": _url_panel(lec.curso, "lecciones"),
    })


@login_required
@profesor_required
def leccion_borrar(request, leccion_id):
    lec = get_object_or_404(Leccion, id=leccion_id)
    curso = lec.curso
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        titulo = lec.titulo
        lec.delete()
        messages.success(request, "Leccion '" + titulo + "' borrada.")
        return redirect(_url_panel(curso, "lecciones"))
    return render(request, "profesor/confirmar_borrar.html", {
        "titulo": "Borrar leccion",
        "mensaje": "Seguro que quieres borrar '" + lec.titulo + "'?",
        "url_confirmar": request.path,
        "url_cancelar": _url_panel(curso, "lecciones"),
    })


# ==================== TAREA ====================
@login_required
@profesor_required
def tarea_crear(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = TareaForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.curso = curso
            t.save()
            messages.success(request, "Tarea creada.")
            return redirect(_url_panel(curso, "tareas"))
    else:
        form = TareaForm()
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nueva tarea en " + curso.titulo,
        "form": form,
        "accion": "Crear",
        "url_cancelar": _url_panel(curso, "tareas"),
    })


@login_required
@profesor_required
def tarea_editar(request, tarea_id):
    t = get_object_or_404(Tarea, id=tarea_id)
    if not _check_curso(request, t.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = TareaForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Tarea actualizada.")
            return redirect(_url_panel(t.curso, "tareas"))
    else:
        form = TareaForm(instance=t)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar tarea",
        "form": form,
        "accion": "Guardar",
        "url_cancelar": _url_panel(t.curso, "tareas"),
    })


@login_required
@profesor_required
def tarea_borrar(request, tarea_id):
    t = get_object_or_404(Tarea, id=tarea_id)
    curso = t.curso
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        titulo = t.titulo
        t.delete()
        messages.success(request, "Tarea '" + titulo + "' borrada.")
        return redirect(_url_panel(curso, "tareas"))
    return render(request, "profesor/confirmar_borrar.html", {
        "titulo": "Borrar tarea",
        "mensaje": "Seguro que quieres borrar '" + t.titulo + "'?",
        "url_confirmar": request.path,
        "url_cancelar": _url_panel(curso, "tareas"),
    })


# ==================== CALIFICAR ENTREGA ====================
@login_required
@profesor_required
def entrega_calificar(request, entrega_id):
    e = get_object_or_404(Entrega, id=entrega_id)
    if not _check_curso(request, e.tarea.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = CalificarEntregaForm(request.POST, instance=e)
        if form.is_valid():
            obj = form.save(commit=False)
            if obj.calificacion is not None and obj.estado == "entregada":
                obj.estado = "calificada"
            obj.fecha_calificacion = timezone.now()
            obj.save()
            messages.success(request, "Entrega calificada.")
            return redirect(_url_panel(e.tarea.curso, "tareas"))
    else:
        form = CalificarEntregaForm(instance=e)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Calificar entrega: " + e.estudiante.username + " / " + e.tarea.titulo,
        "form": form,
        "accion": "Guardar calificacion",
        "url_cancelar": _url_panel(e.tarea.curso, "tareas"),
        "extra_info": "Contenido: " + (e.contenido or "(sin contenido)")[:500],
    })


# ==================== EVALUACION ====================
@login_required
@profesor_required
def evaluacion_crear(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = EvaluacionForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.curso = curso
            ev.save()
            messages.success(request, "Evaluacion creada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[curso.id, ev.id]))
    else:
        form = EvaluacionForm()
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nueva evaluacion en " + curso.titulo,
        "form": form,
        "accion": "Crear",
        "url_cancelar": _url_panel(curso, "evaluaciones"),
    })


@login_required
@profesor_required
def evaluacion_editar(request, evaluacion_id):
    ev = get_object_or_404(Evaluacion, id=evaluacion_id)
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = EvaluacionForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            messages.success(request, "Evaluacion actualizada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[ev.curso.id, ev.id]))
    else:
        form = EvaluacionForm(instance=ev)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar evaluacion: " + ev.titulo,
        "form": form,
        "accion": "Guardar",
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


@login_required
@profesor_required
def evaluacion_borrar(request, evaluacion_id):
    ev = get_object_or_404(Evaluacion, id=evaluacion_id)
    curso = ev.curso
    if not _check_curso(request, curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        ev.delete()
        messages.success(request, "Evaluacion borrada.")
        return redirect(_url_panel(curso, "evaluaciones"))
    return render(request, "profesor/confirmar_borrar.html", {
        "titulo": "Borrar evaluacion",
        "mensaje": "Seguro que quieres borrar '" + ev.titulo + "'?",
        "url_confirmar": request.path,
        "url_cancelar": _url_panel(curso, "evaluaciones"),
    })


# ==================== PREGUNTA ====================
@login_required
@profesor_required
def pregunta_crear(request, evaluacion_id):
    ev = get_object_or_404(Evaluacion, id=evaluacion_id)
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = PreguntaForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.evaluacion = ev
            p.save()
            messages.success(request, "Pregunta creada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[ev.curso.id, ev.id]))
    else:
        form = PreguntaForm(initial={"orden": ev.preguntas.count() + 1})
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nueva pregunta para: " + ev.titulo,
        "form": form,
        "accion": "Crear",
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


@login_required
@profesor_required
def pregunta_editar(request, pregunta_id):
    p = get_object_or_404(PreguntaEvaluacion, id=pregunta_id)
    ev = p.evaluacion
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = PreguntaForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            messages.success(request, "Pregunta actualizada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[ev.curso.id, ev.id]))
    else:
        form = PreguntaForm(instance=p)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar pregunta",
        "form": form,
        "accion": "Guardar",
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


@login_required
@profesor_required
def pregunta_borrar(request, pregunta_id):
    p = get_object_or_404(PreguntaEvaluacion, id=pregunta_id)
    ev = p.evaluacion
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        p.delete()
        messages.success(request, "Pregunta borrada.")
        return redirect(reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]))
    return render(request, "profesor/confirmar_borrar.html", {
        "titulo": "Borrar pregunta",
        "mensaje": "Seguro que quieres borrar esta pregunta?",
        "url_confirmar": request.path,
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


# ==================== OPCION ====================
@login_required
@profesor_required
def opcion_crear(request, pregunta_id):
    p = get_object_or_404(PreguntaEvaluacion, id=pregunta_id)
    ev = p.evaluacion
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = OpcionForm(request.POST)
        if form.is_valid():
            o = form.save(commit=False)
            o.pregunta = p
            o.save()
            messages.success(request, "Opcion creada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[ev.curso.id, ev.id]))
    else:
        form = OpcionForm(initial={"orden": p.opciones.count() + 1})
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Nueva opcion para: " + p.texto[:80],
        "form": form,
        "accion": "Crear",
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


@login_required
@profesor_required
def opcion_editar(request, opcion_id):
    o = get_object_or_404(OpcionRespuesta, id=opcion_id)
    ev = o.pregunta.evaluacion
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        form = OpcionForm(request.POST, instance=o)
        if form.is_valid():
            form.save()
            messages.success(request, "Opcion actualizada.")
            return redirect(reverse("users:profesor_evaluacion_detalle",
                                    args=[ev.curso.id, ev.id]))
    else:
        form = OpcionForm(instance=o)
    return render(request, "profesor/form_generico.html", {
        "titulo_form": "Editar opcion",
        "form": form,
        "accion": "Guardar",
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })


@login_required
@profesor_required
def opcion_borrar(request, opcion_id):
    o = get_object_or_404(OpcionRespuesta, id=opcion_id)
    ev = o.pregunta.evaluacion
    if not _check_curso(request, ev.curso):
        messages.error(request, "Sin permiso.")
        return redirect("users:dashboard_profesor")
    if request.method == "POST":
        o.delete()
        messages.success(request, "Opcion borrada.")
        return redirect(reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]))
    return render(request, "profesor/confirmar_borrar.html", {
        "titulo": "Borrar opcion",
        "mensaje": "Seguro que quieres borrar esta opcion?",
        "url_confirmar": request.path,
        "url_cancelar": reverse("users:profesor_evaluacion_detalle",
                                args=[ev.curso.id, ev.id]),
    })
