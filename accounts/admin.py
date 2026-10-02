from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Esto hace que los campos nuevos aparezcan al editar un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Información de la Academia', {'fields': ('pais', 'avatar', 'perfil_cultural')}),
    )
    # Esto muestra el país en la lista principal de usuarios
    list_display = ['username', 'email', 'pais', 'is_staff']
