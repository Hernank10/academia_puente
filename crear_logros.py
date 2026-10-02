# crear_logros.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import Logro

LOGROS = [
    # Primeros pasos
    ("primer-paso",       "Primer Paso",        "Completaste tu primera lección",         "🌱", "lecciones", 1,   10),
    ("primer-curso",      "Primer Curso",       "Te inscribiste en tu primer curso",      "📚", "cursos",    1,   10),

    # Lecciones
    ("diez-lecciones",    "Diez Lecciones",     "Completaste 10 lecciones",               "⭐", "lecciones", 10,  25),
    ("cincuenta-lecciones","Cincuenta Lecciones","Completaste 50 lecciones",              "🌟", "lecciones", 50,  100),
    ("cien-lecciones",    "Cien Lecciones",     "Completaste 100 lecciones",              "💎", "lecciones", 100, 250),
    ("quinientas-lecciones","Quinientas Lecciones","Completaste 500 lecciones",            "👑", "lecciones", 500, 1000),

    # Cursos
    ("tres-cursos",       "Tres Cursos",        "Inscrito en 3 cursos",                   "🥉", "cursos",    3,   50),
    ("cinco-cursos",      "Cinco Cursos",       "Inscrito en 5 cursos",                   "🥈", "cursos",    5,   100),
    ("diez-cursos",       "Diez Cursos",        "Inscrito en 10 cursos",                  "🥇", "cursos",    10,  250),

    # Puntos
    ("cien-puntos",       "Cien Puntos",        "Alcanzaste 100 puntos de sabiduría",     "🔥", "puntos",    100,  25),
    ("quinientos-puntos", "Quinientos Puntos",  "Alcanzaste 500 puntos",                  "🎯", "puntos",    500,  50),
    ("mil-puntos",        "Mil Puntos",         "Alcanzaste 1000 puntos",                 "🚀", "puntos",    1000, 100),
    ("cinco-mil-puntos",  "Cinco Mil Puntos",   "Alcanzaste 5000 puntos",                 "🏆", "puntos",    5000, 500),

    # Especiales
    ("licenciado",        "Licenciado",         "Marcaste tu perfil como licenciado",     "🎓", "especial",  1,   100),
    ("explorador",        "Explorador",         "Exploraste los recursos interactivos",   "🧭", "especial",  1,   10),
]


def main():
    print("=" * 60)
    print("CREADOR DE LOGROS")
    print("=" * 60)
    print()

    creados = 0
    actualizados = 0

    for codigo, nombre, desc, icono, tipo, umbral, bonus in LOGROS:
        obj, created = Logro.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": nombre,
                "descripcion": desc,
                "icono": icono,
                "tipo": tipo,
                "umbral": umbral,
                "puntos_bonus": bonus,
                "activo": True,
            }
        )
        if created:
            creados += 1
            print(f"  ✅ {icono} {nombre}")
        else:
            actualizados += 1
            print(f"  ♻️  {icono} {nombre} (actualizado)")

    print()
    print(f"Total: {Logro.objects.count()} logros")
    print(f"Creados: {creados} | Actualizados: {actualizados}")


if __name__ == "__main__":
    main()
