# -*- coding: utf-8 -*-
"""Helper para crear notificaciones."""
from .models import Notificacion


def crear_notificacion(usuario, tipo, titulo, mensaje="", url=""):
    """Crea una notificacion. Ignora si usuario es None."""
    if not usuario:
        return None
    return Notificacion.objects.create(
        usuario=usuario, tipo=tipo, titulo=titulo,
        mensaje=mensaje, url=url
    )


def notificar(usuario, tipo, titulo, mensaje="", url=""):
    """Alias corto."""
    return crear_notificacion(usuario, tipo, titulo, mensaje, url)
