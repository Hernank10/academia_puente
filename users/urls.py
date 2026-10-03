from django.urls import path
from . import views
from . import views_profesor
from . import views_panel
from . import views_notificaciones
from . import views_alumno

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
    path('profesor/curso/<int:curso_id>/evaluacion/<int:evaluacion_id>/',
         views.profesor_evaluacion_detalle, name='profesor_evaluacion_detalle'),
    path('profesor/curso/<int:curso_id>/entregas/',
         views.profesor_entregas, name='profesor_entregas'),
    path('profesor/entrega/<int:entrega_id>/calificar/',
         views.profesor_calificar, name='profesor_calificar'),

    # Certificados (públicos)
    path('certificado/<str:codigo>/',
         views.certificado_detalle, name='certificado_detalle'),
    path('certificados/verificar/',
         views.certificado_verificar, name='certificado_verificar'),

    # ============================================================
    # CRUD PANEL PROFESOR
    # ============================================================
    path('profesor/curso/nuevo/',
         views_profesor.curso_crear, name='profesor_curso_crear'),
    path('profesor/curso/<int:curso_id>/editar/',
         views_profesor.curso_editar, name='profesor_curso_editar'),

    path('profesor/curso/<int:curso_id>/leccion/nueva/',
         views_profesor.leccion_crear, name='profesor_leccion_crear'),
    path('profesor/leccion/<int:leccion_id>/editar/',
         views_profesor.leccion_editar, name='profesor_leccion_editar'),
    path('profesor/leccion/<int:leccion_id>/borrar/',
         views_profesor.leccion_borrar, name='profesor_leccion_borrar'),

    path('profesor/curso/<int:curso_id>/tarea/nueva/',
         views_profesor.tarea_crear, name='profesor_tarea_crear'),
    path('profesor/tarea/<int:tarea_id>/editar/',
         views_profesor.tarea_editar, name='profesor_tarea_editar'),
    path('profesor/tarea/<int:tarea_id>/borrar/',
         views_profesor.tarea_borrar, name='profesor_tarea_borrar'),
    path('profesor/entrega/<int:entrega_id>/calificar/',
         views_profesor.entrega_calificar, name='profesor_entrega_calificar'),

    path('profesor/curso/<int:curso_id>/evaluacion/nueva/',
         views_profesor.evaluacion_crear, name='profesor_evaluacion_crear'),
    path('profesor/evaluacion/<int:evaluacion_id>/editar/',
         views_profesor.evaluacion_editar, name='profesor_evaluacion_editar'),
    path('profesor/evaluacion/<int:evaluacion_id>/borrar/',
         views_profesor.evaluacion_borrar, name='profesor_evaluacion_borrar'),

    path('profesor/evaluacion/<int:evaluacion_id>/pregunta/nueva/',
         views_profesor.pregunta_crear, name='profesor_pregunta_crear'),
    path('profesor/pregunta/<int:pregunta_id>/editar/',
         views_profesor.pregunta_editar, name='profesor_pregunta_editar'),
    path('profesor/pregunta/<int:pregunta_id>/borrar/',
         views_profesor.pregunta_borrar, name='profesor_pregunta_borrar'),

    path('profesor/pregunta/<int:pregunta_id>/opcion/nueva/',
         views_profesor.opcion_crear, name='profesor_opcion_crear'),
    path('profesor/opcion/<int:opcion_id>/editar/',
         views_profesor.opcion_editar, name='profesor_opcion_editar'),
    path('profesor/opcion/<int:opcion_id>/borrar/',
         views_profesor.opcion_borrar, name='profesor_opcion_borrar'),


    # ============================================================
    # PANEL ADMIN DEL PROFESOR (sitio web, no django admin)
    # ============================================================
    path('panel/', views_panel.panel_home, name='panel_home'),
    path('panel/cursos/', views_panel.panel_cursos, name='panel_cursos'),
    path('panel/estudiantes/', views_panel.panel_estudiantes, name='panel_estudiantes'),
    path('panel/estudiante/<int:estudiante_id>/',
         views_panel.panel_estudiante_detalle, name='panel_estudiante_detalle'),
    path('panel/evaluaciones/', views_panel.panel_evaluaciones, name='panel_evaluaciones'),
    path('panel/entregas/', views_panel.panel_entregas, name='panel_entregas'),
    path('panel/certificados/', views_panel.panel_certificados, name='panel_certificados'),
    path('panel/certificados/emitir/',
         views_panel.panel_certificado_emitir, name='panel_certificado_emitir'),
    path('panel/certificados/<int:cert_id>/revocar/',
         views_panel.panel_certificado_revocar, name='panel_certificado_revocar'),


    # ============================================================
    # PANEL DEL ALUMNO
    # ============================================================
    path('mi-panel/', views_alumno.alumno_home, name='alumno_home'),
    path('mi-panel/cursos/', views_alumno.alumno_cursos, name='alumno_cursos'),
    path('mi-panel/certificados/', views_alumno.alumno_certificados, name='alumno_certificados'),
    path('mi-panel/logros/', views_alumno.alumno_logros, name='alumno_logros'),

    # Certificado publico mejorado
    path('certificado-publico/<str:codigo>/',
         views_alumno.certificado_publico, name='certificado_publico'),


    # ============================================================
    # NOTIFICACIONES
    # ============================================================
    path('notificaciones/', views_notificaciones.notificaciones_lista,
         name='notificaciones_lista'),
    path('notificaciones/<int:notif_id>/leer/',
         views_notificaciones.notificacion_leer, name='notificacion_leer'),
    path('notificaciones/marcar-todas/',
         views_notificaciones.notificaciones_marcar_todas,
         name='notificaciones_marcar_todas'),
    path('notificaciones/<int:notif_id>/borrar/',
         views_notificaciones.notificacion_borrar, name='notificacion_borrar'),

    # ============================================================
    # RANKING
    # ============================================================
    path('panel/curso/<int:curso_id>/ranking/',
         views_panel.panel_curso_ranking, name='panel_curso_ranking'),
    path('mi-panel/curso/<int:curso_id>/ranking/',
         views_alumno.alumno_curso_ranking, name='alumno_curso_ranking'),

]
