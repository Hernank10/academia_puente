# -*- coding: utf-8 -*-
"""URLs de la API v1."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("materias", views.MateriaViewSet, basename="materia")
router.register("cursos", views.CursoViewSet, basename="curso")
router.register("mis-cursos", views.MiCursoViewSet, basename="mis-curso")
router.register("lecciones", views.LeccionViewSet, basename="leccion")
router.register("mis-certificados", views.CertificadoViewSet, basename="mi-cert")
router.register("notificaciones", views.NotificacionViewSet, basename="notif")
router.register("logros", views.LogroViewSet, basename="logro")
router.register("mis-logros", views.MiLogroViewSet, basename="mi-logro")
router.register("recursos", views.RecursoViewSet, basename="recurso")
router.register("evaluaciones", views.EvaluacionViewSet, basename="evaluacion")
router.register("mis-intentos", views.IntentoViewSet, basename="mi-intento")
router.register("tareas", views.TareaViewSet, basename="tarea")

# Profesor
router.register("profesor/cursos", views.ProfesorCursoViewSet, basename="p-curso")
router.register("profesor/lecciones", views.ProfesorLeccionViewSet, basename="p-leccion")
router.register("profesor/evaluaciones", views.ProfesorEvaluacionViewSet, basename="p-eval")
router.register("profesor/tareas", views.ProfesorTareaViewSet, basename="p-tarea")
router.register("profesor/entregas", views.ProfesorEntregaViewSet, basename="p-entrega")

urlpatterns = [
    # Auth
    path("auth/login/", views.api_login, name="api-login"),
    path("auth/logout/", views.api_logout, name="api-logout"),
    path("auth/register/", views.api_register, name="api-register"),
    path("me/", views.api_me, name="api-me"),

    # Ranking
    path("ranking/curso/<int:curso_id>/", views.api_ranking_curso, name="api-ranking"),

    # Router
    path("", include(router.urls)),
]
