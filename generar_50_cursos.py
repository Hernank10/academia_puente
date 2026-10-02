# generar_50_cursos.py
"""
Genera 50 cursos temáticos agrupando las lecciones existentes
por palabras clave en su campo 'explicacion'.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count

from courses.models import Curso, Materia, Leccion, Inscripcion


# ─────────────────────────────────────────────────────────────
# DEFINICIÓN DE LOS CURSOS TEMÁTICOS
# ─────────────────────────────────────────────────────────────

CURSOS = [
    # ═══════════ GRAMÁTICA (8 cursos) ═══════════
    {"slug": "gramatica-basica", "titulo": "Gramática Básica del Español",
     "materia": "Gramática", "nivel": "A1", "idioma": "ES",
     "keywords": ["gramatica basica", "fundamentos", "sustantiv", "adjetiv basic"]},

    {"slug": "morfologia", "titulo": "Morfología de la Lengua Castellana",
     "materia": "Morfología", "nivel": "A2", "idioma": "ES",
     "keywords": ["morfolog", "lexema", "morfema", "flexion", "derivacion", "composicion", "raices"]},

    {"slug": "sintaxis", "titulo": "Sintaxis del Español",
     "materia": "Sintaxis", "nivel": "B1", "idioma": "ES",
     "keywords": ["sintaxis", "sintactic", "sintaxi", "subordinad", "oracion simple", "oracion compuesta", "oraciones"]},

    {"slug": "morfosintaxis", "titulo": "Morfosintaxis Castellana",
     "materia": "Morfosintaxis", "nivel": "B1", "idioma": "ES",
     "keywords": ["morfosintaxis", "morfosintactic"]},

    {"slug": "verbos", "titulo": "El Verbo en Español",
     "materia": "Gramática", "nivel": "A2", "idioma": "ES",
     "keywords": ["verbo", "verbal", "conjugacion", "perifrasis", "participio", "gerundio", "regimen verbal", "irregular"]},

    {"slug": "preposiciones", "titulo": "Preposiciones y Conjunciones",
     "materia": "Gramática", "nivel": "A2", "idioma": "ES",
     "keywords": ["preposicion", "conjuncion", "preposicion a", "nexo"]},

    {"slug": "pronombres", "titulo": "Pronombres y Determinantes",
     "materia": "Gramática", "nivel": "A2", "idioma": "ES",
     "keywords": ["pronombre", "determinant", "demostrativ", "posesiv", "relativ", "leismo", "laismo", "loismo", "dequeismo"]},

    {"slug": "concordancia", "titulo": "Concordancia y Régimen",
     "materia": "Gramática", "nivel": "B1", "idioma": "ES",
     "keywords": ["concordancia", "regimen", "genero cambiante", "plural"]},

    # ═══════════ ORTOGRAFÍA (6 cursos) ═══════════
    {"slug": "ortografia-basica", "titulo": "Ortografía Básica",
     "materia": "Ortografía", "nivel": "A1", "idioma": "ES",
     "keywords": ["ortografia basica", "acentuacion", "agudas", "graves", "esdrujul", "sobresdrujul", "tilde diacritic", "monosilab", "ortografia"]},

    {"slug": "ortografia-avanzada", "titulo": "Ortografía Avanzada",
     "materia": "Ortografía", "nivel": "B2", "idioma": "ES",
     "keywords": ["ortografia avanzada", "nivel b", "nivel c", "avanzadas"]},

    {"slug": "puntuacion", "titulo": "Signos de Puntuación",
     "materia": "Ortografía", "nivel": "B1", "idioma": "ES",
     "keywords": ["puntuacion", "coma", "punto y coma", "punto", "puntuacion", "puntuacion"]},

    {"slug": "uso-letras", "titulo": "Uso Correcto de las Letras",
     "materia": "Ortografía", "nivel": "A2", "idioma": "ES",
     "keywords": ["uso de letras", "letras", "abreviatura", "mayuscul", "minuscul"]},

    {"slug": "caligrafia", "titulo": "Caligrafía y Escritura",
     "materia": "Caligrafía", "nivel": "A1", "idioma": "ES",
     "keywords": ["caligrafi", "cursiva", "palmer", "script", "firmas", "pedagogia-del-programa"]},

    {"slug": "correccion-estilo", "titulo": "Corrección y Estilo",
     "materia": "Ortografía", "nivel": "B2", "idioma": "ES",
     "keywords": ["estilo", "correccion", "claridad", "muletillas", "etica"]},

    # ═══════════ LÉXICO Y SEMÁNTICA (5 cursos) ═══════════
    {"slug": "etimologia", "titulo": "Etimologías Grecolatinas",
     "materia": "Etimología", "nivel": "B2", "idioma": "ES",
     "keywords": ["etimolog", "grecolatin", "raices", "prefijos", "sufijos", "helenism", "latinism", "grieg", "latin"]},

    {"slug": "semantica", "titulo": "Semántica del Español",
     "materia": "Semántica", "nivel": "B2", "idioma": "ES",
     "keywords": ["semantic", "significad", "lexic", "paronim", "sinonim", "antonim", "semantica"]},

    {"slug": "semiotica", "titulo": "Semiótica Aplicada",
     "materia": "Semiótica", "nivel": "C1", "idioma": "ES",
     "keywords": ["semiotic", "signo"]},

    {"slug": "lexicografia", "titulo": "Lexicografía y Diccionarios",
     "materia": "Léxico", "nivel": "B2", "idioma": "ES",
     "keywords": ["lexicograf", "diccionario"]},

    {"slug": "prestamos", "titulo": "Anglicismos, Galicismos y Préstamos",
     "materia": "Léxico", "nivel": "B2", "idioma": "ES",
     "keywords": ["anglicism", "galicism", "indigenism", "prestamo", "extranjerism", "galicism", "latinism"]},

    # ═══════════ FONÉTICA Y FONOLOGÍA (4 cursos) ═══════════
    {"slug": "fonetica", "titulo": "Fonética del Español",
     "materia": "Fonética", "nivel": "B1", "idioma": "ES",
     "keywords": ["fonetic", "sonido", "articulacion", "afi", "transcripcion", "separacion fonetica"]},

    {"slug": "fonologia", "titulo": "Fonología del Español",
     "materia": "Fonología", "nivel": "B2", "idioma": "ES",
     "keywords": ["fonolog", "fonema", "silab", "silaba", "separacion fonolog", "fonologia"]},

    {"slug": "fono-estructural", "titulo": "Fonología Estructuralista",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["fonologia estructural", "fonetica estructural", "estructural"]},

    {"slug": "fono-generativa", "titulo": "Fonología Generativa",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["fonologia generativ", "fonetica generativ"]},

    # ═══════════ RETÓRICA (5 cursos) ═══════════
    {"slug": "retorica-clasica", "titulo": "Retórica Clásica",
     "materia": "Retórica", "nivel": "B2", "idioma": "ES",
     "keywords": ["retorica clasica", "aristoteles", "ethos", "pathos", "logos", "inventio", "dispositio", "lugares comunes", "topoi", "retorica"]},

    {"slug": "figuras-retoricas", "titulo": "Figuras Retóricas",
     "materia": "Retórica", "nivel": "B1", "idioma": "ES",
     "keywords": ["figuras retoricas", "metafora", "metonimia", "hiperbole", "simil", "anafora", "epiteto", "oximoron", "alegoria", "personificacion", "sinestesia"]},

    {"slug": "tropos", "titulo": "Tropos y Metáforas",
     "materia": "Retórica", "nivel": "B2", "idioma": "ES",
     "keywords": ["tropos", "metafora pura", "metafora cognitiv", "lakoff"]},

    {"slug": "silogismo", "titulo": "Silogismo y Entimema",
     "materia": "Lógica", "nivel": "B2", "idioma": "ES",
     "keywords": ["silogism", "entimem", "logica", "argumentacion"]},

    {"slug": "preceptos-clasicos", "titulo": "Preceptos de Teón, Hermógenes y Aftonio",
     "materia": "Retórica", "nivel": "C1", "idioma": "ES",
     "keywords": ["teon", "hermogenes", "aftonio", "chria", "apologo", "fabula", "ecfrasis", "parafrasis", "antitesis", "contraargumentacion"]},

    # ═══════════ REDACCIÓN (8 cursos) ═══════════
    {"slug": "redaccion-basica", "titulo": "Redacción Básica",
     "materia": "Redacción", "nivel": "A2", "idioma": "ES",
     "keywords": ["redaccion basica", "escritura", "escribir", "redaccion"]},

    {"slug": "redaccion-parrafos", "titulo": "Redacción de Párrafos",
     "materia": "Redacción", "nivel": "B1", "idioma": "ES",
     "keywords": ["parraf", "tipos de parraf", "parrafo", "parrafos"]},

    {"slug": "redaccion-oraciones", "titulo": "Redacción de Oraciones",
     "materia": "Redacción", "nivel": "A2", "idioma": "ES",
     "keywords": ["oraciones simples", "oraciones compuestas", "tipos de oraciones", "ordenamiento de frases"]},

    {"slug": "redaccion-cientifica", "titulo": "Redacción Científica",
     "materia": "Redacción", "nivel": "B2", "idioma": "ES",
     "keywords": ["redaccion cientific", "cientific", "ciencia"]},

    {"slug": "redaccion-periodistica", "titulo": "Redacción Periodística",
     "materia": "Redacción", "nivel": "B2", "idioma": "ES",
     "keywords": ["periodistic", "periodism", "entradilla", "lead", "noticia", "generos periodisticos", "titulacion"]},

    {"slug": "redaccion-academica", "titulo": "Redacción Académica",
     "materia": "Redacción", "nivel": "B2", "idioma": "ES",
     "keywords": ["redaccion academic", "academic", "universitari", "ensay"]},

    {"slug": "redaccion-bilingue", "titulo": "Redacción Bilingüe Castellano-Inglés",
     "materia": "Redacción", "nivel": "B1", "idioma": "ES",
     "keywords": ["bilingue", "bilingue", "redaccion en ingles"]},

    {"slug": "conectores", "titulo": "Conectores del Discurso",
     "materia": "Redacción", "nivel": "B1", "idioma": "ES",
     "keywords": ["conector", "anafora", "catafora", "deixis", "cohesion", "coherencia", "conectores"]},

    # ═══════════ TIPOLOGÍAS TEXTUALES (7 cursos) ═══════════
    {"slug": "texto-narrativo", "titulo": "Texto Narrativo",
     "materia": "Tipologías Textuales", "nivel": "B1", "idioma": "ES",
     "keywords": ["narrativ", "narracion", "cuento", "novela", "relato", "historia", "narrador", "personajes", "climax", "estructura_tiempo", "realismo_magico", "ciencia ficcion", "ficcion"]},

    {"slug": "texto-descriptivo", "titulo": "Texto Descriptivo",
     "materia": "Tipologías Textuales", "nivel": "B1", "idioma": "ES",
     "keywords": ["descriptiv", "descripcion", "prosopograf", "etopey", "topograf", "descripcion"]},

    {"slug": "texto-expositivo", "titulo": "Texto Expositivo",
     "materia": "Tipologías Textuales", "nivel": "B1", "idioma": "ES",
     "keywords": ["expositiv", "exposicion", "explicacion", "expositivo"]},

    {"slug": "texto-argumentativo", "titulo": "Texto Argumentativo",
     "materia": "Tipologías Textuales", "nivel": "B2", "idioma": "ES",
     "keywords": ["argumentativ", "argumentacion", "tesis", "contraargument", "argumentativo"]},

    {"slug": "texto-dialogado", "titulo": "Texto Dialogado y Dramaturgia",
     "materia": "Tipologías Textuales", "nivel": "B2", "idioma": "ES",
     "keywords": ["dialogo", "dramaturgi", "teatro", "teatrum", "pantomima"]},

    {"slug": "texto-epistolar", "titulo": "Texto Epistolar y Cartas",
     "materia": "Tipologías Textuales", "nivel": "B2", "idioma": "ES",
     "keywords": ["epistol", "carta", "correo", "cartas", "familiares"]},

    {"slug": "tipologias-mixtas", "titulo": "Tipologías Textuales Mixtas",
     "materia": "Tipologías Textuales", "nivel": "B2", "idioma": "ES",
     "keywords": ["narrativas, descriptivas, argumentativas y expositivas", "tipologias"]},

    # ═══════════ LITERATURA (5 cursos) ═══════════
    {"slug": "literatura-espanola", "titulo": "Literatura Española",
     "materia": "Literatura", "nivel": "B2", "idioma": "ES",
     "keywords": ["literatura espanol", "novela espanol", "generacion_98", "siglo_xx", "vanguardia espanol"]},

    {"slug": "literatura-hispanoamericana", "titulo": "Literatura Hispanoamericana",
     "materia": "Literatura", "nivel": "B2", "idioma": "ES",
     "keywords": ["hispanoamerican", "latinoamerican", "boom", "garcia marquez", "borges", "realismo magico"]},

    {"slug": "literatura-universal", "titulo": "Literatura Universal",
     "materia": "Literatura", "nivel": "C1", "idioma": "ES",
     "keywords": ["literatura universal", "poesia", "epica", "lirica", "ensay"]},

    {"slug": "ciencia-ficcion", "titulo": "Ciencia Ficción y Narrativa Especulativa",
     "materia": "Literatura", "nivel": "B2", "idioma": "ES",
     "keywords": ["ciencia ficcion", "science", "especulativ", "futurist", "cromatismo", "iconografia", "disfemismo", "eufemismo", "hipotiposis", "oximoron"]},

    {"slug": "historias-lugares", "titulo": "Historias y Leyendas de Lugares",
     "materia": "Literatura", "nivel": "B1", "idioma": "ES",
     "keywords": ["escocia", "dublin", "londres", "reino unido", "bahia", "temple bar"]},

    # ═══════════ LINGÜÍSTICA AVANZADA (7 cursos) ═══════════
    {"slug": "linguistica-general", "titulo": "Lingüística General",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["linguistica general", "linguistica aplicada", "linguistica"]},

    {"slug": "psicolinguistica", "titulo": "Psicolingüística",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["psicolinguistic", "psicolinguistica"]},

    {"slug": "sociolinguistica", "titulo": "Sociolingüística",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["sociolinguistic", "sociolinguistica"]},

    {"slug": "antropolinguistica", "titulo": "Antropolingüística",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["antropolinguistic", "antropolog", "antropologia"]},

    {"slug": "pragmatica", "titulo": "Pragmática y Análisis del Discurso",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["pragmatic", "discurso", "analisis del discurso", "cortesia"]},

    {"slug": "textolinguistica", "titulo": "Textolingüística",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["textolinguistic", "textolinguistica"]},

    {"slug": "etnolinguistica", "titulo": "Etnolingüística",
     "materia": "Lingüística", "nivel": "C1", "idioma": "ES",
     "keywords": ["etnolingüistic", "etnografia"]},

    # ═══════════ INGLÉS (2 cursos) ═══════════
    {"slug": "ingles-gramatica", "titulo": "Gramática Inglesa",
     "materia": "Inglés", "nivel": "A2", "idioma": "EN",
     "keywords": ["gramatica inglesa", "grammar", "sintaxis inglesa", "morfologia de la lengua inglesa"]},

    {"slug": "ingles-redaccion", "titulo": "Redacción en Inglés",
     "materia": "Inglés", "nivel": "B1", "idioma": "EN",
     "keywords": ["redaccion en ingles", "english", "cambridge"]},

    # ═══════════ TEMAS PRÁCTICOS (3 cursos) ═══════════
    {"slug": "preparacion-saber-pro", "titulo": "Preparación Saber Pro",
     "materia": "Preparación Pruebas", "nivel": "B2", "idioma": "ES",
     "keywords": ["saber pro", "saber-pro", "lectura critica", "competencia"]},

    {"slug": "concurso-docente", "titulo": "Preparación Concurso Docente",
     "materia": "Preparación Pruebas", "nivel": "B2", "idioma": "ES",
     "keywords": ["concurso docente", "men", "estandares", "competencias", "isabel sole", "comprension lectora", "macrohabilidades"]},

    {"slug": "escritura-creativa", "titulo": "Escritura Creativa",
     "materia": "Escritura Creativa", "nivel": "B1", "idioma": "ES",
     "keywords": ["escritores", "creativa", "haiku", "haikus", "aforismo", "aphorism", "ensayoteca"]},
]


# ─────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────

def normalizar(texto):
    """Minúsculas + sin tildes."""
    if not texto:
        return ""
    t = texto.lower()
    for a, b in [('á','a'),('é','e'),('í','i'),('ó','o'),('ú','u'),('ü','u'),('ñ','n')]:
        t = t.replace(a, b)
    return t


def clasificar_leccion(leccion, cursos_def):
    """Devuelve el slug del curso al que pertenece la lección."""
    cat = normalizar(leccion.explicacion or "")
    titulo = normalizar(leccion.titulo or "")
    texto = cat + " " + titulo

    mejor_match = None
    mejor_puntaje = 0

    for curso in cursos_def:
        puntaje = 0
        for kw in curso["keywords"]:
            kw_norm = normalizar(kw)
            if kw_norm in texto:
                puntaje += len(kw_norm)  # keywords más largas valen más
        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_match = curso

    return mejor_match["slug"] if mejor_match else None


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

@transaction.atomic
def main():
    print("=" * 70)
    print("  GENERADOR DE CURSOS TEMÁTICOS")
    print("=" * 70)
    print()

    profesor = User.objects.filter(is_superuser=True).first()
    if not profesor:
        print("❌ No hay superusuario.")
        return
    print(f"👤 Profesor: {profesor.username}")
    print()

    total_lecciones = Leccion.objects.count()
    print(f"📚 Lecciones: {total_lecciones}")
    print(f"📚 Cursos actuales: {Curso.objects.count()}")
    print()

    if total_lecciones == 0:
        print("❌ No hay lecciones.")
        return

    # 1. Crear cursos
    print("─" * 70)
    print("  CREANDO CURSOS")
    print("─" * 70)

    cursos_creados = {}
    nuevos = 0

    for definicion in CURSOS:
        materia, _ = Materia.objects.get_or_create(nombre=definicion["materia"])

        curso, creado = Curso.objects.get_or_create(
            titulo=definicion["titulo"],
            defaults={
                'materia': materia,
                'idioma': definicion["idioma"],
                'nivel': definicion["nivel"],
                'profesor': profesor,
            }
        )
        cursos_creados[definicion["slug"]] = curso
        if creado:
            nuevos += 1

    print(f"  ✅ {nuevos} cursos nuevos")
    print(f"  ♻️  {len(CURSOS) - nuevos} reutilizados")
    print()

    # 2. Reasignar lecciones
    print("─" * 70)
    print("  REASIGNANDO LECCIONES")
    print("─" * 70)

    curso_original = Curso.objects.filter(titulo="Curso de Soberanía Digital").first()

    lecciones = Leccion.objects.all()
    asignadas = 0
    no_clasificadas = 0
    contador = {}

    for leccion in lecciones:
        slug = clasificar_leccion(leccion, CURSOS)
        if slug and slug in cursos_creados:
            curso_destino = cursos_creados[slug]
            leccion.curso = curso_destino
            contador[slug] = contador.get(slug, 0) + 1
            leccion.orden = contador[slug]
            leccion.save()
            asignadas += 1
        else:
            no_clasificadas += 1

    print(f"  ✅ {asignadas} asignadas")
    print(f"  ⚠️  {no_clasificadas} sin clasificar (quedan en curso original)")
    print()

    # 3. Reporte
    print("─" * 70)
    print("  DISTRIBUCIÓN POR CURSO")
    print("─" * 70)
    print()

    cursos_con_lecciones = Curso.objects.annotate(
        n_lecciones=Count('lecciones')
    ).filter(n_lecciones__gt=0).order_by('-n_lecciones')

    for c in cursos_con_lecciones:
        print(f"  {c.n_lecciones:5d} | {c.titulo[:65]}")

    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print(f"  Cursos creados:          {nuevos}")
    print(f"  Cursos con lecciones:    {cursos_con_lecciones.count()}")
    print(f"  Lecciones reasignadas:   {asignadas}")
    print(f"  Lecciones sin clasificar:{no_clasificadas}")
    print(f"  Total lecciones:         {total_lecciones}")


if __name__ == "__main__":
    main()
