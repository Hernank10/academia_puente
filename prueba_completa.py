import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count, Avg, Sum
from courses.models import (
    Materia, Curso, Leccion, Inscripcion, Certificado,
    ProgresoEstudiante, Evaluacion, PreguntaEvaluacion
)
from users.models import Perfil, Logro, LogroUsuario


def sec(titulo):
    print()
    print("=" * 70)
    print("  " + titulo)
    print("=" * 70)


def prueba():
    sec("ESTADO GENERAL")
    print("  Usuarios:       %d" % User.objects.count())
    print("  Materias:       %d" % Materia.objects.count())
    print("  Cursos:         %d" % Curso.objects.count())
    print("  Lecciones:      %d" % Leccion.objects.count())
    print("  Inscripciones:  %d" % Inscripcion.objects.count())
    print("  Progresos:      %d" % ProgresoEstudiante.objects.count())
    print("  Certificados:   %d" % Certificado.objects.count())
    print("  Evaluaciones:   %d" % Evaluacion.objects.count())
    print("  Preguntas:      %d" % PreguntaEvaluacion.objects.count())
    print("  Logros:         %d" % Logro.objects.count())
    print("  Logros ganados: %d" % LogroUsuario.objects.count())

    sec("CERTIFICADOS EMITIDOS")
    certs = Certificado.objects.select_related('estudiante', 'curso').order_by('-fecha_emision')
    if certs.exists():
        for c in certs[:20]:
            print("  %s | %s | %s" % (c.codigo, c.estudiante.username, c.curso.titulo[:40]))
    else:
        print("  No hay certificados emitidos.")

    sec("TOP 10 ESTUDIANTES POR PUNTOS")
    perfiles = Perfil.objects.select_related('usuario').order_by('-puntos')[:10]
    for i, p in enumerate(perfiles, 1):
        n = LogroUsuario.objects.filter(usuario=p.usuario).count()
        print("  %2d. %s %6d pts | %2d logros" % (i, p.usuario.username.ljust(15), p.puntos, n))

    sec("LOGROS MAS GANADOS")
    logros = Logro.objects.annotate(n=Count('logrousuario')).order_by('-n')
    for l in logros[:10]:
        print("  %3d usuarios | %s" % (l.n, l.nombre))

    sec("RESUMEN FINAL")
    print("  Cursos con lecciones:   %d" % Curso.objects.annotate(n=Count('lecciones')).filter(n__gt=0).count())
    print("  Estudiantes activos:    %d" % User.objects.filter(is_superuser=False).count())
    print("  Certificados emitidos:  %d" % Certificado.objects.count())
    print("  Logros otorgados:       %d" % LogroUsuario.objects.count())

    if Certificado.objects.count() > 0:
        print()
        print("  SISTEMA FUNCIONANDO CORRECTAMENTE")
    else:
        print()
        print("  Ejecuta crear_certificados.py primero")


if __name__ == "__main__":
    prueba()
