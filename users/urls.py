from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-profesor/', views.dashboard_profesor, name='dashboard_profesor'),

    # Acciones
    path('inscribirse/<int:curso_id>/', views.inscribirse, name='inscribirse'),

    # Panel del profesor
    path('profesor/curso/<int:curso_id>/',
         views.profesor_curso_detalle, name='profesor_curso_detalle'),
    path('profesor/curso/<int:curso_id>/estudiante/<int:estudiante_id>/',
         views.profesor_estudiante_detalle, name='profesor_estudiante_detalle'),
    path('profesor/curso/<int:curso_id>/entregas/',
         views.profesor_entregas, name='profesor_entregas'),
    path('profesor/entrega/<int:entrega_id>/calificar/',
         views.profesor_calificar, name='profesor_calificar'),

    # Certificados (públicos)
    path('certificado/<str:codigo>/',
         views.certificado_detalle, name='certificado_detalle'),
    path('certificados/verificar/',
         views.certificado_verificar, name='certificado_verificar'),
]
