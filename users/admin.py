from django.contrib import admin
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    # Conservamos tu estructura y añadimos el rango dinámico al final
    list_display = (
        'usuario', 
        'rol_principal', 
        'estado_academico', 
        'rango_academico',  # <-- Se calcula solo, sin ser campo fijo
        'puntos',           # <-- Importante verlo para entender el rango
        'idioma_nativo', 
        'zona_horaria'
    )

    # Tus filtros originales que tanto te gustaron
    list_filter = ('rol_principal', 'estado_academico', 'idioma_nativo')

    # Tu buscador original
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')
    
    # Hacemos que el rango sea visible pero no editable dentro del perfil
    readonly_fields = ('rango_academico',)    


# ============================================================
# GAMIFICACIÓN: Admin
# ============================================================
from django.contrib import admin
from .models import Logro, LogroUsuario


@admin.register(Logro)
class LogroAdmin(admin.ModelAdmin):
    list_display = ('icono', 'nombre', 'codigo', 'tipo', 'umbral', 'puntos_bonus', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('codigo', 'nombre', 'descripcion')
    prepopulated_fields = {}


@admin.register(LogroUsuario)
class LogroUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'logro', 'fecha_desbloqueo')
    list_filter = ('logro',)
    search_fields = ('usuario__username', 'logro__nombre')
    autocomplete_fields = ()
