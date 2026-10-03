# -*- coding: utf-8 -*-
"""views_notificaciones.py - Listar, leer y borrar notificaciones."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notificacion


@login_required
def notificaciones_lista(request):
    qs = Notificacion.objects.filter(usuario=request.user).order_by('-creada')
    solo_no_leidas = request.GET.get('no_leidas') == '1'
    if solo_no_leidas:
        qs = qs.filter(leida=False)
    total_no_leidas = Notificacion.objects.filter(
        usuario=request.user, leida=False
    ).count()
    return render(request, 'users/notificaciones.html', {
        'notificaciones': qs,
        'total_no_leidas': total_no_leidas,
        'solo_no_leidas': solo_no_leidas,
        'seccion': 'notificaciones',
    })


@login_required
def notificacion_leer(request, notif_id):
    n = get_object_or_404(Notificacion, id=notif_id, usuario=request.user)
    n.leida = True
    n.save(update_fields=['leida'])
    if n.url:
        return redirect(n.url)
    return redirect('users:notificaciones_lista')


@login_required
def notificaciones_marcar_todas(request):
    Notificacion.objects.filter(
        usuario=request.user, leida=False
    ).update(leida=True)
    messages.success(request, "Todas marcadas como leidas.")
    return redirect('users:notificaciones_lista')


@login_required
def notificacion_borrar(request, notif_id):
    n = get_object_or_404(Notificacion, id=notif_id, usuario=request.user)
    if request.method == 'POST':
        n.delete()
        messages.success(request, "Notificacion borrada.")
        return redirect('users:notificaciones_lista')
    return render(request, 'profesor/confirmar_borrar.html', {
        'titulo': 'Borrar notificacion',
        'mensaje': n.titulo,
        'url_confirmar': request.path,
        'url_cancelar': '/es/cuenta/notificaciones/',
    })
