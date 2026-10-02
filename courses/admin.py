from django.contrib import admin
from .models import Materia, Curso, Leccion # Asegúrate de importar los tres

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'idioma', 'nivel', 'profesor')
    list_filter = ('idioma', 'nivel')

@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    # Esta es tu versión preferida, ¡conservada!
    list_display = ('titulo', 'pais_origen', 'fecha_publicacion')
    list_filter = ('pais_origen', 'curso')
    search_fields = ('titulo', 'explicacion')


# ============================================================
# ADMIN: Evaluaciones
# ============================================================
from django.contrib import admin
from .models import (
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
    IntentoEvaluacion, RespuestaIntento,
)


class OpcionInline(admin.TabularInline):
    model = OpcionRespuesta
    extra = 4
    fields = ('texto', 'es_correcta', 'orden')


class PreguntaInline(admin.StackedInline):
    model = PreguntaEvaluacion
    extra = 0
    show_change_link = True


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'estado', 'total_preguntas', 'total_intentos', 'promedio_puntaje')
    list_filter = ('estado', 'curso__materia')
    search_fields = ('titulo', 'descripcion', 'curso__titulo')
    inlines = [PreguntaInline]


@admin.register(PreguntaEvaluacion)
class PreguntaEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('texto_corto', 'evaluacion', 'puntaje', 'orden')
    list_filter = ('evaluacion',)
    search_fields = ('texto',)
    inlines = [OpcionInline]

    def texto_corto(self, obj):
        return obj.texto[:60]
    texto_corto.short_description = 'Pregunta'


@admin.register(IntentoEvaluacion)
class IntentoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'evaluacion', 'puntaje', 'aprobado', 'completado', 'fecha_inicio')
    list_filter = ('aprobado', 'completado', 'evaluacion')
    search_fields = ('estudiante__username', 'evaluacion__titulo')
    readonly_fields = ('fecha_inicio', 'fecha_fin')
