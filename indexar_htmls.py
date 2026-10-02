# indexar_htmls.py
import os
import re
import django
import glob

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils.text import slugify
from django.apps import apps

CARPETA = "templates/ejercicios_completos-lengua-castellana"


def extraer_titulo(path):
    try:
        with open(path, encoding="utf-8") as f:
            contenido = f.read(10000)
    except Exception:
        return os.path.basename(path).replace(".html", "")

    m = re.search(r'<title>([^<]+)</title>', contenido, re.IGNORECASE)
    if m:
        titulo = m.group(1).strip()
        titulo = re.sub(r'\s*\|.*$', '', titulo)
        return titulo[:300]
    return os.path.basename(path).replace(".html", "")


def detectar_tipo(nombre):
    n = nombre.lower()
    if n.startswith("flota "):
        return "flota"
    if "flashcard" in n or "tarjeta" in n:
        return "flashcards"
    if "cuaderno" in n or n.startswith("cuaderno-"):
        return "cuaderno"
    if "archivo de vector" in n:
        return "archivo_vector"
    if "app" in n or "play" in n or "mission" in n or "scriptorium" in n:
        return "app"
    if re.search(r'\b\d+\s*t[eé]cnicas?\b', n):
        return "tecnica"
    return "otro"


def slug_unico(base, slug_vistos):
    slug = slugify(base, allow_unicode=False)[:200]
    if not slug:
        slug = "recurso"
    original = slug
    i = 2
    while slug in slug_vistos:
        slug = "%s-%d" % (original[:195], i)
        i += 1
    slug_vistos.add(slug)
    return slug


def main():
    RecursoInteractivo = apps.get_model('courses', 'RecursoInteractivo')

    archivos = sorted(glob.glob(os.path.join(CARPETA, "*.html")))
    print("=" * 70)
    print("INDEXADOR DE HTMLs")
    print("=" * 70)
    print("Encontrados %d archivos HTML" % len(archivos))
    print()

    slug_vistos = set(RecursoInteractivo.objects.values_list('slug', flat=True))
    creados = 0
    saltados = 0
    errores = 0

    for i, path in enumerate(archivos, 1):
        nombre_archivo = os.path.basename(path)

        if RecursoInteractivo.objects.filter(archivo_html=nombre_archivo).exists():
            saltados += 1
            continue

        try:
            titulo = extraer_titulo(path)
            tipo = detectar_tipo(nombre_archivo)
            slug = slug_unico(titulo or nombre_archivo, slug_vistos)

            RecursoInteractivo.objects.create(
                titulo=titulo[:300],
                slug=slug,
                archivo_html=nombre_archivo,
                tipo=tipo,
                orden=i,
            )
            creados += 1

            if creados % 50 == 0:
                print("  ... %d creados" % creados)

        except Exception as e:
            errores += 1
            print("  ERROR en %s: %s" % (nombre_archivo[:50], e))

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("  Creados:   %3d" % creados)
    print("  Saltados:  %3d" % saltados)
    print("  Errores:   %3d" % errores)
    print("  Total BD:  %3d" % RecursoInteractivo.objects.count())

    from django.db.models import Count
    print()
    print("  Distribución por tipo:")
    for row in RecursoInteractivo.objects.values('tipo').annotate(n=Count('id')).order_by('-n'):
        print("    %-15s %3d" % (row['tipo'], row['n']))


if __name__ == "__main__":
    main()
