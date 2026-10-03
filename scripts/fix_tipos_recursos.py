# -*- coding: utf-8 -*-
"""fix_tipos_recursos.py - Clasifica los 432 recursos que quedaron en tipo='otro'.

Uso:
  python fix_tipos_recursos.py            -> dry-run (solo muestra)
  python fix_tipos_recursos.py --apply    -> aplica los cambios
"""
import os, sys, django, unicodedata
from collections import Counter

BASE = r"E:\02_proyectos\academia_puente\_original"
sys.path.insert(0, BASE)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import RecursoInteractivo


def normalizar(texto):
    """Minusculas, sin tildes."""
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def inferir_tipo(r):
    """Devuelve la clave de tipo segun el contenido del recurso."""
    campos = " ".join([
        r.titulo or "",
        r.subtitulo or "",
        r.descripcion or "",
        r.tags or "",
        r.archivo_html or "",
    ])
    t = normalizar(campos)

    # Reglas ordenadas: de mas especifica a mas generica
    reglas = [
        ('archivo_vector', ['vector', 'vectores']),
        ('flashcards',    ['flashcard', 'flash card']),
        ('flota',         ['flota tematica', 'flota', 'globo']),
        ('cuaderno',      ['cuaderno', 'libreta', 'cuadernillo']),
        ('tecnica',       ['tecnica', 'tecnicas']),
        ('app',           ['app interactiva', 'aplicacion interactiva']),
    ]
    for clave, patrones in reglas:
        for p in patrones:
            if p in t:
                return clave

    # Si tiene num_tecnicas, es tecnicas numeradas
    if r.num_tecnicas and r.num_tecnicas > 0:
        return 'tecnica'

    return 'otro'


def main():
    apply = '--apply' in sys.argv
    qs = RecursoInteractivo.objects.all()
    total = qs.count()

    print("=" * 60)
    print("CLASIFICACION DE RECURSOS ({})".format("APLICAR" if apply else "DRY-RUN"))
    print("=" * 60)
    print("Total recursos: {}".format(total))
    print("")

    cambios = Counter()
    detalle = []

    for r in qs:
        nuevo = inferir_tipo(r)
        if nuevo != r.tipo:
            cambios[nuevo] += 1
            detalle.append((r.id, r.tipo, nuevo, (r.titulo or "")[:60]))

    print("CAMBIOS PROPUESTOS:")
    for k, v in sorted(cambios.items()):
        print("  -> {}: {}".format(k, v))
    print("  TOTAL A CAMBIAR: {}".format(sum(cambios.values())))
    print("")

    print("PRIMEROS 40 CAMBIOS:")
    for rid, viejo, nuevo, titulo in detalle[:40]:
        print("  [{}] {} -> {} | {}".format(rid, viejo, nuevo, titulo))
    print("")

    if apply:
        cont = 0
        for r in qs:
            nuevo = inferir_tipo(r)
            if nuevo != r.tipo:
                r.tipo = nuevo
                r.save(update_fields=['tipo'])
                cont += 1
        print("APLICADOS: {} cambios".format(cont))
        print("")
        print("NUEVA DISTRIBUCION EN LA DB:")
        c = Counter(RecursoInteractivo.objects.values_list('tipo', flat=True))
        for k, v in sorted(c.items()):
            print("  {!r}: {}".format(k, v))
    else:
        print("(Nada guardado. Ejecuta con --apply para aplicar los cambios.)")


if __name__ == "__main__":
    main()