from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Perfil


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    """Crea o sincroniza el Perfil sin sobrescribir el rol de no-admins."""
    perfil, _ = Perfil.objects.get_or_create(usuario=instance)

    if instance.is_superuser:
        if perfil.rol_principal != 'profesor':
            perfil.rol_principal = 'profesor'
            perfil.puede_publicar_cursos = True
            if perfil.estado_academico == 'grado':
                perfil.estado_academico = 'licenciado'
            perfil.save()
    elif instance.is_staff:
        if perfil.rol_principal != 'profesor':
            perfil.rol_principal = 'profesor'
            perfil.puede_publicar_cursos = True
            perfil.save()
