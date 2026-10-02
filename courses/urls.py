from django.urls import path
from . import views
from users import views as users_views

app_name = 'courses'

urlpatterns = [
    # Home
    path('', views.index, name='index'),

    # Cursos
    path('cursos/<int:curso_id>/', views.curso_detalle, name='curso_detalle'),
    path('cursos/<int:curso_id>/leccion/<int:leccion_id>/completar/',
         views.marcar_leccion_completada, name='marcar_leccion_completada'),

    # Recursos
    path('recursos/', views.recursos_lista, name='recursos_lista'),
    path('recursos/<slug:slug>/', views.recurso_detalle, name='recurso_detalle'),

    # Evaluaciones
    path('evaluacion/<int:evaluacion_id>/', views.rendir_evaluacion, name='rendir_evaluacion'),
    path('evaluacion/resultado/<int:intento_id>/',
         views.resultado_evaluacion, name='resultado_evaluacion'),

    # Certificados (públicos, verificables)
    path('certificado/<str:codigo>/',
         users_views.certificado_detalle, name='certificado_detalle'),
    path('certificados/verificar/',
         users_views.certificado_verificar, name='certificado_verificar'),
]
