# reclasificar_huerfanos.py
"""
Segunda pasada de clasificación para las lecciones que quedaron
en el Curso de Soberanía Digital.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Count
from courses.models import Curso, Leccion


# ─────────────────────────────────────────────────────────────
# MAPEO EXTRA: categorías huérfanas → curso destino
# ─────────────────────────────────────────────────────────────

MAPEO_DIRECTO = {
    # ─── NARRATIVA ───
    "contemporanea": "texto-narrativo",
    "voz": "texto-narrativo",
    "tiempo": "texto-narrativo",
    "final": "texto-narrativo",
    "estructura": "texto-narrativo",
    "espacio_atmosfera": "texto-narrativo",
    "realismo": "texto-narrativo",
    "siglo_oro": "literatura-espanola",
    "Trama": "texto-narrativo",
    "Manejo del tiempo": "texto-narrativo",
    "Estructura interna": "texto-narrativo",
    "temas_motivos": "texto-narrativo",
    "humor": "texto-narrativo",
    "Género": "texto-narrativo",
    "Tema": "texto-narrativo",
    "Tradición castellana · tópicos": "literatura-espanola",
    "Tradición castellana": "literatura-espanola",
    "Identidad": "texto-narrativo",
    "Cosmovisión": "texto-narrativo",
    "Ideología": "texto-narrativo",

    # ─── PUNTUACIÓN Y USO DE LETRAS ───
    "Raya": "puntuacion",
    "Barra": "puntuacion",
    "Comillas": "puntuacion",
    "Interrogación": "puntuacion",
    "Modalidad oracional": "puntuacion",
    "Modalidad": "puntuacion",
    "Siglas": "uso-letras",
    "Abreviaturas": "uso-letras",

    # ─── PERIODISMO ───
    "Fuentes y verificación": "redaccion-periodistica",
    "Formato": "redaccion-periodistica",
    "Guion": "redaccion-periodistica",
    "Estructura informativa": "redaccion-periodistica",
    "Titulación": "redaccion-periodistica",
    "Formato digital": "redaccion-periodistica",

    # ─── PRAGMÁTICA ───
    "Contacto": "pragmatica",
    "Ritual": "pragmatica",
    "Análisis de la conversación": "pragmatica",
    "Actos de habla": "pragmatica",
    "Principio de cooperación": "pragmatica",
    "Implicatura": "pragmatica",
    "Polifonía": "pragmatica",
    "Cortesía": "pragmatica",
    "Deixis": "pragmatica",

    # ─── ESTILÍSTICA Y RETÓRICA ───
    "Recursos": "correccion-estilo",
    "Recursos estilísticos": "correccion-estilo",
    "Figuras de pensamiento": "figuras-retoricas",
    "Vicios del lenguaje": "correccion-estilo",
    "Variación": "correccion-estilo",
    "Estilo": "correccion-estilo",
    "experimentales": "texto-narrativo",

    # ─── GRAMÁTICA ───
    "Adverbios": "gramatica-basica",
    "Adjetivos": "gramatica-basica",
    "Comparativas": "gramatica-basica",
    "Estructuras enfáticas": "gramatica-basica",
    "Análisis crítico": "redaccion-academica",
    "Subordinadas adverbiales": "sintaxis",

    # ─── TEXTOLINGÜÍSTICA ───
    "Tipos de texto": "textolinguistica",
    "Propiedades textuales": "textolinguistica",
    "Superestructura": "textolinguistica",
    "Superestructuras": "textolinguistica",
    "Tipología textual": "textolinguistica",
    "Organización textual": "textolinguistica",
    "Estructura textual": "textolinguistica",
    "Estructura": "textolinguistica",

    # ─── LINGÜÍSTICA ───
    "Oralidad": "linguistica-general",
    "Vitalidad": "linguistica-general",
    "Contexto": "pragmatica",

    # ─── VARIOS ───
    "avanzadas": "ortografia-avanzada",
    "personajes": "texto-narrativo",
    "Punto de vista": "texto-narrativo",
    "Tipos de párrafo": "redaccion-parrafos",
    "Géneros periodísticos": "redaccion-periodistica",
    "Argumentación": "texto-argumentativo",
    "Ética y deontología": "correccion-estilo",
    "Entradilla (lead)": "redaccion-periodistica",
    "Coma": "puntuacion",
    "Puntuación": "puntuacion",
    "Ortografía y puntuación": "ortografia-basica",
    "Acentuación": "ortografia-basica",
    "Uso de letras": "uso-letras",
    "Figuras de sintaxis": "figuras-retoricas",
    "Tropos": "tropos",
    "Punto": "puntuacion",
    "narrativo": "texto-narrativo",
    "expositivo": "texto-expositivo",
    "descriptivo": "texto-descriptivo",
    "argumentativo": "texto-argumentativo",
    "voz_narrador": "texto-narrativo",
    "realismo_magico": "texto-narrativo",
    "estructura_tiempo": "texto-narrativo",
    "siglo_xx": "literatura-espanola",
    "generacion_98": "literatura-espanola",
    "climax": "texto-narrativo",
    "dialogo": "texto-dialogado",
    "descripcion": "texto-descriptivo",
}

# Mapeo de slug → título de curso
SLUG_A_TITULO = {
    "texto-narrativo": "Texto Narrativo",
    "texto-descriptivo": "Texto Descriptivo",
    "texto-expositivo": "Texto Expositivo",
    "texto-argumentativo": "Texto Argumentativo",
    "texto-dialogado": "Texto Dialogado y Dramaturgia",
    "literatura-espanola": "Literatura Española",
    "literatura-hispanoamericana": "Literatura Hispanoamericana",
    "literatura-universal": "Literatura Universal",
    "puntuacion": "Signos de Puntuación",
    "uso-letras": "Uso Correcto de las Letras",
    "ortografia-basica": "Ortografía Básica",
    "ortografia-avanzada": "Ortografía Avanzada",
    "redaccion-periodistica": "Redacción Periodística",
    "redaccion-academica": "Redacción Académica",
    "redaccion-parrafos": "Redacción de Párrafos",
    "redaccion-oraciones": "Redacción de Oraciones",
    "pragmatica": "Pragmática y Análisis del Discurso",
    "correccion-estilo": "Corrección y Estilo",
    "figuras-retoricas": "Figuras Retóricas",
    "tropos": "Tropos y Metáforas",
    "gramatica-basica": "Gramática Básica del Español",
    "sintaxis": "Sintaxis del Español",
    "textolinguistica": "Textolingüística",
    "linguistica-general": "Lingüística General",
}


def main():
    print("=" * 70)
    print("  RECLASIFICACIÓN DE LECCIONES HUÉRFANAS")
    print("=" * 70)
    print()

    curso_orig = Curso.objects.filter(titulo="Curso de Soberanía Digital").first()
    if not curso_orig:
        print("❌ No existe el curso original")
        return

    huerfanas = Leccion.objects.filter(curso=curso_orig)
    print(f"Lecciones huérfanas: {huerfanas.count()}")
    print()

    # Cachear cursos destino
    cursos_cache = {}
    for titulo in set(SLUG_A_TITULO.values()):
        try:
            cursos_cache[titulo] = Curso.objects.get(titulo=titulo)
        except Curso.DoesNotExist:
            pass

    print(f"Cursos destino disponibles: {len(cursos_cache)}")
    print()

    # Reasignar
    reasignadas = 0
    no_encontradas = []
    contador = {}

    for leccion in huerfanas:
        cat = (leccion.explicacion or "").strip()
        slug = MAPEO_DIRECTO.get(cat)

        if not slug:
            continue

        titulo_destino = SLUG_A_TITULO.get(slug)
        if not titulo_destino:
            continue

        curso_destino = cursos_cache.get(titulo_destino)
        if not curso_destino:
            continue

        leccion.curso = curso_destino
        contador[titulo_destino] = contador.get(titulo_destino, 0) + 1
        leccion.orden = contador[titulo_destino]
        leccion.save()
        reasignadas += 1

    print("=" * 70)
    print("  RESULTADO")
    print("=" * 70)
    print(f"  Reasignadas: {reasignadas}")
    print()

    print("Distribución por curso destino:")
    for titulo, n in sorted(contador.items(), key=lambda x: -x[1]):
        print(f"  {n:4d} | {titulo}")
    print()

    # Ver qué queda
    restantes = Leccion.objects.filter(curso=curso_orig).count()
    print(f"  Lecciones aún en curso original: {restantes}")

    if restantes > 0:
        print()
        print("  Categorías restantes:")
        cats = Leccion.objects.filter(curso=curso_orig).values('explicacion').annotate(
            n=Count('id')
        ).order_by('-n')[:20]
        for c in cats:
            print(f"    {c['n']:4d} | {c['explicacion'][:65]}")


if __name__ == "__main__":
    main()
