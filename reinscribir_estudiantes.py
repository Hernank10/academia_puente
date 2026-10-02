# reinscribir_estudiantes.py
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count
from courses.models import Curso, Inscripcion, ProgresoEstudiante
from users.models import Perfil


ESTUDIANTES = [
    "ana_lopez", "carlos_ruiz", "maria_garcia", "juan_perez",
    "lucia_torres", "diego_mora", "sofia_vega", "andres_cruz",
    "valentina_rio", "pablo_soto",
]


def main():
    print("=" * 70)
    print("  REINSCRIBIENDO ESTUDIANTES EN CURSOS NUEVOS")
    print("=" * 70)
    print()

    cursos = list(Curso.objects.annotate(n=Count('lecciones')).filter(n__gt=0))
    print(f"Cursos disponibles: {len(cursos)}")
    print()

    curso_orig = Curso.objects.filter(titulo="Curso de Soberanía Digital").first()

    for username in ESTUDIANTES:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print(f"⚠️  {username} no existe")
            continue

        cursos_elegibles = [c for c in cursos if c != curso_orig]
        num = random.randint(5, 10)
        seleccion = random.sample(cursos_elegibles, min(num, len(cursos_elegibles)))

        inscrito = 0
        progreso_total = 0

        for curso in seleccion:
            _, creada = Inscripcion.objects.get_or_create(
                estudiante=user, curso=curso,
                defaults={'activa': True}
            )
            if not creada:
                continue
            inscrito += 1

            fraccion = random.uniform(0.1, 1.0)
            lecciones = list(curso.lecciones.all())
            num_completar = int(len(lecciones) * fraccion)
            completar = random.sample(lecciones, num_completar)

            for lec in completar:
                ProgresoEstudiante.objects.get_or_create(
                    estudiante=user, leccion=lec,
                    defaults={'completada': True}
                )
            progreso_total += num_completar

        perfil, _ = Perfil.objects.get_or_create(usuario=user)
        perfil.puntos += progreso_total * 5
        perfil.save()

        print(f"  {username:20s} → {inscrito} cursos nuevos | +{progreso_total} lecciones")

    print()
    print("=" * 70)
    print("  ESTADO FINAL")
    print("=" * 70)
    print(f"  Inscripciones: {Inscripcion.objects.count()}")
    print(f"  Progresos:     {ProgresoEstudiante.objects.count()}")
    print(f"  Lecciones:     {Leccion.objects.count() if False else '—'}")
    print(f"  Cursos:        {Curso.objects.count()}")


if __name__ == "__main__":
    main()
