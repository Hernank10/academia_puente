# -*- coding: utf-8 -*-
from rest_framework import permissions


class IsProfesor(permissions.BasePermission):
    """Solo profesores o superusers."""
    message = "Solo profesores pueden acceder."

    def has_permission(self, request, view):
        u = request.user
        if not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        try:
            return u.perfil.rol_principal == "profesor" or u.is_staff
        except Exception:
            return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Solo el dueño puede modificar."""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Buscar campo 'estudiante' o 'usuario'
        for campo in ("estudiante", "usuario"):
            if hasattr(obj, campo):
                return getattr(obj, campo) == request.user
        return False


class IsProfesorDelCurso(permissions.BasePermission):
    """El profesor solo puede tocar sus propios cursos."""
    message = "No tienes permiso sobre este curso."

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        # obj puede ser Curso o tener .curso
        curso = obj if obj.__class__.__name__ == "Curso" else getattr(obj, "curso", None)
        if curso is None:
            return True
        return curso.profesor_id == request.user.id
