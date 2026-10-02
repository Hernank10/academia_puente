import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Curso, Certificado, Inscripcion, ProgresoEstudiante


def generar_codigo(curso_id, estudiante_id):
    return "CERT-%03d-%03d" % (curso_id, estudiante_id)


def crear_certificados():
    print("=" * 70)
    print("  GENERADOR DE CERTIFICADOS")
    print("=" * 70)
    print()

    creados = 0
    existentes = 0
    no_califican = 0

    estudiantes = User.objects.filter(is_superuser=False).order_by('username')

    for estudiante in estudiantes:
        inscripciones = Inscripcion.objects.filter(estudiante=estudiante)

        for inscripcion in inscripciones:
            curso = inscripcion.curso
            total = curso.lecciones.count()
            if total == 0:
                continue

            completadas = ProgresoEstudiante.objects.filter(
                estudiante=estudiante,
                leccion__curso=curso,
                completada=True,
            ).count()

            if completadas >= total:
                if Certificado.objects.filter(estudiante=estudiante, curso=curso).exists():
                    existentes += 1
                    continue

                codigo = generar_codigo(curso.id, estudiante.id)
                try:
                    puntos = 0
                    if hasattr(estudiante, 'perfil'):
                        puntos = estudiante.perfil.puntos

                    Certificado.objects.create(
                        codigo=codigo,
                        estudiante=estudiante,
                        curso=curso,
                        fecha_completado=timezone.now(),
                        estado='emitido',
                        puntos_obtenidos=puntos,
                        calificacion='Aprobado',
                    )
                    creados += 1
                    print("  OK %s | %s | %s" % (codigo, estudiante.username, curso.titulo[:40]))
                except Exception as e:
                    print("  ERROR con %s: %s" % (estudiante.username, e))
            else:
                no_califican += 1

    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print("  Certificados creados:      %d" % creados)
    print("  Certificados existentes:   %d" % existentes)
    print("  Cursos sin completar:      %d" % no_califican)
    print("  Total certificados en BD:  %d" % Certificado.objects.count())


if __name__ == "__main__":
    crear_certificados()
