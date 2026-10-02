import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count, Avg, Sum
from courses.models import Curso, Leccion, Inscripcion, Certificado, ProgresoEstudiante, Materia
from users.models import Perfil, Logro, LogroUsuario


def reporte():
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    print()
    print("=" * 70)
    print("  REPORTE ACADEMIA PUENTE DIGITAL")
    print("  " + fecha)
    print("=" * 70)

    print()
    print("ESTADISTICAS GLOBALES")
    print("-" * 70)
    print("  Usuarios:        %d" % User.objects.count())
    print("  Estudiantes:     %d" % User.objects.filter(is_superuser=False).count())
    print("  Materias:        %d" % Materia.objects.count())
    print("  Cursos:          %d" % Curso.objects.count())
    print("  Lecciones:       %d" % Leccion.objects.count())
    print("  Inscripciones:   %d" % Inscripcion.objects.count())
    print("  Progresos:       %d" % ProgresoEstudiante.objects.count())
    print("  Certificados:    %d" % Certificado.objects.count())
    print("  Logros:          %d" % Logro.objects.count())
    print("  Logros ganados:  %d" % LogroUsuario.objects.count())

    print()
    print("PROGRESO PROMEDIO")
    print("-" * 70)
    perfiles = Perfil.objects.all()
    if perfiles.exists():
        prom = perfiles.aggregate(prom=Avg('puntos'))['prom'] or 0
        total = perfiles.aggregate(total=Sum('puntos'))['total'] or 0
        print("  Puntos promedio: %d" % int(prom))
        print("  Puntos totales:  %d" % total)

    print()
    print("TOP 5 CURSOS POR INSCRITOS")
    print("-" * 70)
    cursos = Curso.objects.annotate(n=Count('inscripcion')).order_by('-n')[:5]
    for i, c in enumerate(cursos, 1):
        print("  %d. %s | %3d inscritos" % (i, c.titulo[:50].ljust(50), c.n))

    print()
    print("TOP 5 LOGROS MAS GANADOS")
    print("-" * 70)
    logros = Logro.objects.annotate(n=Count('logrousuario')).order_by('-n')[:5]
    for i, l in enumerate(logros, 1):
        print("  %d. %s | %3d usuarios" % (i, l.nombre[:50].ljust(50), l.n))

    print()
    print("=" * 70)
    print("  Reporte generado el " + fecha)
    print("=" * 70)
    print()


if __name__ == "__main__":
    reporte()