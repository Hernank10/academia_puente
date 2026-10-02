# users/decorators.py
"""
Decoradores para controlar acceso según el rol del usuario.
Roles disponibles: 'estudiante', 'profesor'.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def profesor_required(view_func):
    """
    Solo permite acceso a usuarios autenticados con rol_principal='profesor'.
    Si es estudiante, lo redirige a su dashboard con un mensaje.
    Si no está autenticado, lo manda al login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder.")
            return redirect('users:login')

        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol_principal != 'profesor':
            messages.error(request, "⛔ Esta sección es solo para profesores.")
            return redirect('users:dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


def estudiante_required(view_func):
    """
    Solo permite acceso a usuarios autenticados con rol_principal='estudiante'.
    Si es profesor, lo redirige a su dashboard.
    Si no está autenticado, lo manda al login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder.")
            return redirect('users:login')

        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol_principal != 'estudiante':
            messages.error(request, "⛔ Esta sección es solo para estudiantes.")
            return redirect('users:dashboard_profesor')

        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """
    Solo permite acceso a usuarios staff (is_staff=True).
    Útil para vistas de administración personalizadas.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder.")
            return redirect('users:login')

        if not request.user.is_staff:
            messages.error(request, "⛔ Esta sección es solo para administradores.")
            return redirect('users:dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════
# Helper: redirigir según rol
# ═══════════════════════════════════════════════════════════

def redirigir_por_rol(user):
    """
    Devuelve la URL del dashboard correcto según el rol del usuario.
    Uso: return redirigir_por_rol(request.user)
    """
    perfil = getattr(user, 'perfil', None)
    if perfil and perfil.rol_principal == 'profesor':
        return redirect('users:dashboard_profesor')
    return redirect('users:dashboard')
