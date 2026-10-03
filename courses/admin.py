# Parcheado: es_staff_o_super puede ver el admin
# -*- coding: utf-8 -*-
"""admin.py - Admin personalizado: profesor solo ve SUS cursos."""
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin, GroupAdmin as BaseGroupAdmin

from .models import (
    Materia, Curso, Leccion, ProgresoEstudiante,
    RecursoInteractivo, Inscripcion, Certificado,
    Tarea, Entrega, Evaluacion, PreguntaEvaluacion,
    OpcionRespuesta, IntentoEvaluacion, RespuestaIntento,
)


# ============================================================
# MIXIN: filtrar queryset para que el profesor solo vea lo suyo
# ============================================================
class ProfesorFilterMixin:
    """Filtra el queryset para que un profesor solo vea sus cursos."""

    # Atributo opcional: ruta al campo que apunta al profesor
    # Si el modelo tiene 'profesor' directo o 'curso__profesor'
    filtro_profesor = 'curso__profesor'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Profesor: solo sus cursos
        try:
            return qs.filter(**{self.filtro_profesor: request.user})
        except Exception:
            return qs.none()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # Verificar que el objeto pertenece al profesor
        return self._es_del_profesor(obj, request.user)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_module_permission(self, request):
        # is_staff y superuser pueden ver el modulo
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def _es_del_profesor(self, obj, user):
        """Comprueba si el objeto pertenece a un curso del profesor."""
        try:
            if hasattr(obj, 'curso'):
                return obj.curso.profesor == user
            if hasattr(obj, 'profesor'):
                return obj.profesor == user
            if hasattr(obj, 'evaluacion'):
                return obj.evaluacion.curso.profesor == user
            if hasattr(obj, 'tarea'):
                return obj.tarea.curso.profesor == user
            if hasattr(obj, 'intento'):
                return obj.intento.evaluacion.curso.profesor == user
        except Exception:
            pass
        return False


# ============================================================
# OCULTAR User y Group A LOS NO SUPERUSUARIOS
# ============================================================
try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class SoloSuperUserUserAdmin(BaseUserAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Group)
class SoloSuperUserGroupAdmin(BaseGroupAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ============================================================
# MATERIA
# ============================================================
@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

    def has_module_permission(self, request):
        # Las materias las ve el superuser, los profesores no las editan
        return request.user.is_superuser or request.user.is_staff


# ============================================================
# CURSO
# ============================================================
@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'materia', 'nivel', 'idioma', 'profesor', 'total_lecciones_admin', 'total_inscritos_admin')
    list_filter = ('nivel', 'idioma', 'materia')
    search_fields = ('titulo',)
    autocomplete_fields = ('profesor',)

    def has_module_permission(self, request):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(profesor=request.user)

    def save_model(self, request, obj, form, change):
        # Si un profesor crea un curso, se le asigna automaticamente
        if not request.user.is_superuser and not change:
            obj.profesor = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        return obj.profesor == request.user

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Profesor solo puede asignarse a si mismo
        if db_field.name == 'profesor' and not request.user.is_superuser:
            kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
            kwargs['initial'] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def total_lecciones_admin(self, obj):
        return obj.lecciones.count()
    total_lecciones_admin.short_description = 'Lecciones'

    def total_inscritos_admin(self, obj):
        return obj.inscripciones.filter(activa=True).count()
    total_inscritos_admin.short_description = 'Inscritos'


# ============================================================
# LECCION
# ============================================================
@admin.register(Leccion)
class LeccionAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'pais_origen', 'orden', 'fecha_publicacion')
    list_filter = ('pais_origen', 'curso')
    search_fields = ('titulo', 'explicacion')
    list_select_related = ('curso',)
    filtro_profesor = 'curso__profesor'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Profesor solo ve sus cursos en el desplegable
        if db_field.name == 'curso' and not request.user.is_superuser:
            kwargs['queryset'] = Curso.objects.filter(profesor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ============================================================
# RECURSO INTERACTIVO
# ============================================================
@admin.register(RecursoInteractivo)
class RecursoInteractivoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo', 'orden')
    list_filter = ('tipo',)
    search_fields = ('titulo', 'descripcion')

    def has_module_permission(self, request):
        # RecursoInteractivo es global, solo lo ve el superuser
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ============================================================
# INSCRIPCION
# ============================================================
@admin.register(Inscripcion)
class InscripcionAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('estudiante', 'curso', 'activa', 'fecha_inscripcion')
    list_filter = ('activa', 'curso')
    search_fields = ('estudiante__username', 'curso__titulo')
    list_select_related = ('estudiante', 'curso')
    filtro_profesor = 'curso__profesor'
    readonly_fields = ('fecha_inscripcion',)


# ============================================================
# CERTIFICADO
# ============================================================
@admin.register(Certificado)
class CertificadoAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('codigo', 'estudiante', 'curso', 'estado', 'fecha_emision', 'puntos_obtenidos')
    list_filter = ('estado', 'curso')
    search_fields = ('codigo', 'estudiante__username', 'curso__titulo')
    list_select_related = ('estudiante', 'curso')
    readonly_fields = ('codigo', 'fecha_emision', 'fecha_completado')
    filtro_profesor = 'curso__profesor'


# ============================================================
# PROGRESO ESTUDIANTE
# ============================================================
@admin.register(ProgresoEstudiante)
class ProgresoEstudianteAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('estudiante', 'leccion', 'completada', 'fecha_completado')
    list_filter = ('completada', 'leccion__curso')
    search_fields = ('estudiante__username', 'leccion__titulo')
    list_select_related = ('estudiante', 'leccion', 'leccion__curso')
    filtro_profesor = 'leccion__curso__profesor'


# ============================================================
# TAREA
# ============================================================
@admin.register(Tarea)
class TareaAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'tipo', 'estado', 'fecha_limite', 'puntaje_maximo')
    list_filter = ('estado', 'tipo', 'curso')
    search_fields = ('titulo', 'descripcion')
    filtro_profesor = 'curso__profesor'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'curso' and not request.user.is_superuser:
            kwargs['queryset'] = Curso.objects.filter(profesor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ============================================================
# ENTREGA
# ============================================================
@admin.register(Entrega)
class EntregaAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('estudiante', 'tarea', 'estado', 'calificacion', 'fecha_entrega')
    list_filter = ('estado', 'tarea__curso')
    search_fields = ('estudiante__username', 'tarea__titulo')
    list_select_related = ('estudiante', 'tarea', 'tarea__curso')
    readonly_fields = ('fecha_entrega', 'fecha_calificacion')
    filtro_profesor = 'tarea__curso__profesor'


# ============================================================
# EVALUACION
# ============================================================
class PreguntaInline(admin.StackedInline):
    model = PreguntaEvaluacion
    extra = 0
    show_change_link = True


@admin.register(Evaluacion)
class EvaluacionAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'estado', 'total_preguntas', 'total_intentos', 'promedio_puntaje')
    list_filter = ('estado', 'curso__materia')
    search_fields = ('titulo', 'descripcion', 'curso__titulo')
    inlines = [PreguntaInline]
    filtro_profesor = 'curso__profesor'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'curso' and not request.user.is_superuser:
            kwargs['queryset'] = Curso.objects.filter(profesor=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ============================================================
# PREGUNTA EVALUACION
# ============================================================
class OpcionInline(admin.TabularInline):
    model = OpcionRespuesta
    extra = 4
    fields = ('texto', 'es_correcta', 'orden')


@admin.register(PreguntaEvaluacion)
class PreguntaEvaluacionAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('texto_corto', 'evaluacion', 'puntaje', 'orden')
    list_filter = ('evaluacion',)
    search_fields = ('texto',)
    inlines = [OpcionInline]
    filtro_profesor = 'evaluacion__curso__profesor'

    def texto_corto(self, obj):
        return obj.texto[:60]
    texto_corto.short_description = 'Pregunta'


# ============================================================
# OPCION RESPUESTA
# ============================================================
@admin.register(OpcionRespuesta)
class OpcionRespuestaAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('texto_corto', 'pregunta', 'es_correcta', 'orden')
    list_filter = ('es_correcta',)
    search_fields = ('texto',)
    filtro_profesor = 'pregunta__evaluacion__curso__profesor'

    def texto_corto(self, obj):
        return obj.texto[:60]
    texto_corto.short_description = 'Opcion'


# ============================================================
# INTENTO EVALUACION
# ============================================================
@admin.register(IntentoEvaluacion)
class IntentoEvaluacionAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('estudiante', 'evaluacion', 'puntaje', 'aprobado', 'completado', 'fecha_inicio')
    list_filter = ('aprobado', 'completado', 'evaluacion')
    search_fields = ('estudiante__username', 'evaluacion__titulo')
    readonly_fields = ('fecha_inicio', 'fecha_fin')
    filtro_profesor = 'evaluacion__curso__profesor'


# ============================================================
# RESPUESTA INTENTO
# ============================================================
@admin.register(RespuestaIntento)
class RespuestaIntentoAdmin(ProfesorFilterMixin, admin.ModelAdmin):
    list_display = ('intento', 'pregunta', 'opcion_elegida', 'es_correcta')
    list_filter = ('es_correcta',)
    filtro_profesor = 'intento__evaluacion__curso__profesor'


# ============================================================
# ADMIN SITE: personalizar titulos
# ============================================================
admin.site.site_header = "Academia Puente Digital - Panel de Administracion"
admin.site.site_title = "Puente Digital Admin"
admin.site.index_title = "Gestion de cursos y contenidos"