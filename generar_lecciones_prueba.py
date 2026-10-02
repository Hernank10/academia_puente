# generar_lecciones_prueba.py
"""
Genera lecciones de prueba coherentes para cada curso
que tenga pocas lecciones.
"""

import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import Curso, Leccion


# ─────────────────────────────────────────────────────────────
# PLANTILLAS POR MATERIA
# ─────────────────────────────────────────────────────────────

PLANTILLAS = {
    "Gramática": {
        "titulos": [
            "Identificación de sustantivos", "Uso correcto de adjetivos",
            "Concordancia de género y número", "El verbo y sus conjugaciones",
            "Tiempos verbales simples", "Tiempos verbales compuestos",
            "Los determinantes", "Los pronombres personales",
            "Preposiciones de lugar", "Preposiciones de tiempo",
            "Conjunciones coordinantes", "Conjunciones subordinantes",
            "El adverbio", "Análisis morfológico básico",
            "El sujeto y el predicado", "Complemento directo",
            "Complemento indirecto", "Complemento circunstancial",
            "Oraciones simples vs compuestas", "Oraciones subordinadas",
        ],
        "preguntas": [
            "¿Cuál de las siguientes palabras es un sustantivo?",
            "Identifica el verbo en la oración.",
            "¿Cuál es el tiempo verbal correcto?",
            "¿Cuál es la función sintáctica del elemento subrayado?",
            "¿Cuál de las siguientes es una oración compuesta?",
        ],
        "respuestas": [
            "La respuesta correcta es la opción A.",
            "El elemento analizado cumple la función indicada.",
            "La concordancia es correcta.",
            "El verbo está en pretérito perfecto simple.",
            "Es una oración coordinada copulativa.",
        ],
    },
    "Ortografía": {
        "titulos": [
            "Uso de la B y V", "Uso de la G y J", "Uso de la H",
            "Uso de la C, S y Z", "Uso de la X", "Uso de la Y y LL",
            "Palabras agudas", "Palabras graves o llanas",
            "Palabras esdrújulas", "Palabras sobresdrújulas",
            "Acentuación de diptongos", "Acentuación de hiatos",
            "Tilde diacrítica en monosílabos", "Signos de interrogación",
            "Signos de exclamación", "El punto y coma",
            "Los dos puntos", "Las comillas", "Los paréntesis",
            "Los puntos suspensivos",
        ],
        "preguntas": [
            "¿Cuál es la forma correcta de escribir la palabra?",
            "¿Lleva tilde la siguiente palabra?",
            "¿Qué signo de puntuación falta en la oración?",
            "¿Cuál es la ortografía correcta?",
            "¿En qué caso se usa la tilde diacrítica?",
        ],
        "respuestas": [
            "La forma correcta es con B.",
            "Sí, lleva tilde por ser aguda terminada en vocal.",
            "Falta una coma antes de la conjunción.",
            "La palabra se escribe con H intermedia.",
            "La tilde diacrítica distingue funciones gramaticales.",
        ],
    },
    "Redacción": {
        "titulos": [
            "Estructura del párrafo", "La idea principal y secundaria",
            "Tipos de párrafos", "El párrafo argumentativo",
            "El párrafo descriptivo", "El párrafo narrativo",
            "El párrafo expositivo", "Conectores textuales",
            "Coherencia y cohesión", "La introducción",
            "El desarrollo", "La conclusión",
            "Cómo hacer un ensayo", "Cómo escribir una carta formal",
            "Cómo escribir un correo profesional", "Cómo hacer un resumen",
            "Cómo hacer una reseña", "Cómo hacer una síntesis",
            "Cómo hacer un informe", "Cómo revisar y editar",
        ],
        "preguntas": [
            "¿Cuál es la estructura básica de un párrafo?",
            "¿Qué tipo de párrafo se usa para narrar hechos?",
            "¿Qué conector es adecuado para añadir información?",
            "¿Qué debe contener una conclusión?",
            "¿Cuál es la diferencia entre coherencia y cohesión?",
        ],
        "respuestas": [
            "Introducción, desarrollo y conclusión.",
            "El párrafo narrativo.",
            "El conector 'además' o 'asimismo'.",
            "Una síntesis y una reflexión final.",
            "La coherencia es el sentido global; la cohesión son los enlaces.",
        ],
    },
    "Literatura": {
        "titulos": [
            "El Siglo de Oro español", "El Barroco", "El Romanticismo",
            "El Realismo", "El Modernismo", "La Generación del 98",
            "La Generación del 27", "La Novela Hispanoamericana",
            "El Boom Latinoamericano", "El Realismo Mágico",
            "La Poesía del Siglo XX", "El Teatro Contemporáneo",
            "Análisis de personajes", "El narrador y su punto de vista",
            "El tiempo narrativo", "El espacio narrativo",
            "El tema y los motivos", "El estilo literario",
            "La intertextualidad", "La crítica literaria",
        ],
        "preguntas": [
            "¿Quién escribió la obra mencionada?",
            "¿A qué movimiento literario pertenece el autor?",
            "¿Cuál es el tema principal de la obra?",
            "¿Qué tipo de narrador tiene el texto?",
            "¿Qué figura literaria predomina en el fragmento?",
        ],
        "respuestas": [
            "El autor es el indicado en la opción correcta.",
            "Pertenece al movimiento literario señalado.",
            "El tema central es el amor y la muerte.",
            "El narrador es omnisciente en tercera persona.",
            "Predomina la metáfora y el símbolo.",
        ],
    },
    "Lingüística": {
        "titulos": [
            "¿Qué es la lingüística?", "Niveles de análisis lingüístico",
            "Saussure y el estructuralismo", "Chomsky y la gramática generativa",
            "La competencia lingüística", "El signo lingüístico",
            "El significante y el significado", "La doble articulación",
            "La fonología estructural", "La semántica estructural",
            "El análisis del discurso", "La pragmática",
            "Los actos de habla", "La teoría de la relevancia",
            "La sociolingüística", "La etnolingüística",
            "La psicolingüística", "La neurolingüística",
            "La adquisición del lenguaje", "El bilingüismo",
        ],
        "preguntas": [
            "¿Qué estudia la lingüística?",
            "¿Cuál es la unidad mínima del lenguaje?",
            "¿Quién propuso el concepto de 'signo lingüístico'?",
            "¿Qué es la competencia lingüística?",
            "¿Cuál es la diferencia entre lengua y habla?",
        ],
        "respuestas": [
            "El lenguaje humano en todas sus manifestaciones.",
            "El fonema es la unidad mínima sin significado.",
            "Ferdinand de Saussure.",
            "Es el conocimiento interno que un hablante tiene de su lengua.",
            "La lengua es social; el habla es individual.",
        ],
    },
    "Retórica": {
        "titulos": [
            "Introducción a la retórica", "El arte de la persuasión",
            "Ethos, pathos y logos", "Las cinco partes del discurso",
            "La inventio", "La dispositio", "La elocutio",
            "La memoria y la actio", "Las figuras retóricas",
            "La metáfora y la metonimia", "La hipérbole y la litotes",
            "La ironía y el sarcasmo", "La anáfora y el epífora",
            "El paralelismo y la antítesis", "La elipsis y el asíndeton",
            "El polisíndeton", "La aliteración y la onomatopeya",
            "Los tropos", "La alegoría", "La fábula y la parábola",
        ],
        "preguntas": [
            "¿Cuál es el objetivo principal de la retórica?",
            "¿Qué tipo de apelación es el pathos?",
            "¿Cuál es la diferencia entre metáfora y metonimia?",
            "¿Qué figura retórica se usa en la frase?",
            "¿Cuál es la función del ethos?",
        ],
        "respuestas": [
            "Persuadir mediante el lenguaje.",
            "Apelación a las emociones del auditorio.",
            "La metáfora sustituye; la metonimia designa por contigüidad.",
            "Se usa una hipérbole para exagerar.",
            "Es la credibilidad del orador.",
        ],
    },
    "Léxico": {
        "titulos": [
            "Palabras patrimoniales", "Cultismos y semicultismos",
            "Préstamos del latín", "Préstamos del griego",
            "Arabismos en español", "Galicismos",
            "Italianismos", "Anglicismos",
            "Indigenismos americanos", "Neologismos",
            "Arcaísmos", "Palabras compuestas",
            "Palabras derivadas", "Palabras parasintéticas",
            "Siglas y acrónimos", "Abreviaturas",
            "Onomatopeyas", "Palabras tabú y eufemismos",
            "Palabras jergales", "Variantes dialectales",
        ],
        "preguntas": [
            "¿De qué lengua proviene la palabra?",
            "¿Qué tipo de préstamo es la palabra?",
            "¿Cuál es el significado etimológico de la palabra?",
            "¿Qué palabra es un neologismo?",
            "¿Cuál es un ejemplo de cultismo?",
        ],
        "respuestas": [
            "Proviene del árabe hispánico.",
            "Es un anglicismo adaptado al español.",
            "El significado proviene de sus raíces latinas.",
            "'Software' es un neologismo.",
            "'Filosofía' es un cultismo del griego.",
        ],
    },
    "Semántica": {
        "titulos": [
            "El significado y el sentido", "Denotación y connotación",
            "Sinonimia", "Antonimia", "Polisemia", "Homonimia",
            "Paronimia", "Hiperonimia e hiponimia", "Campos semánticos",
            "Relaciones léxicas", "Cambio semántico",
            "Metáfora y metonimia como fenómenos semánticos",
            "La ambigüedad", "Los actos de habla y el significado",
            "La deixis", "La presuposición", "La implicatura",
            "La teoría de los prototipos", "Los marcos semánticos",
            "La semántica cognitiva",
        ],
        "preguntas": [
            "¿Cuál es la diferencia entre significado y sentido?",
            "¿Qué tipo de relación semántica hay entre las palabras?",
            "¿Cuál es la denotación de la palabra?",
            "¿Qué ejemplo de polisemia hay en la frase?",
            "¿Cuál es un sinónimo de la palabra?",
        ],
        "respuestas": [
            "El significado es objetivo; el sentido es contextual.",
            "Son sinónimos parciales.",
            "La denotación es el significado literal.",
            "La palabra 'banco' tiene múltiples significados.",
            "Un sinónimo posible es el indicado.",
        ],
    },
    "Psicolingüística": {
        "titulos": [
            "¿Qué es la psicolingüística?", "Procesamiento del lenguaje",
            "Comprensión lectora", "Producción del lenguaje",
            "Adquisición del lenguaje", "Etapas del desarrollo lingüístico",
            "El bilingüismo", "Trastornos del lenguaje",
            "La memoria y el lenguaje", "La atención y el lenguaje",
            "El procesamiento léxico", "El procesamiento sintáctico",
            "El procesamiento semántico", "El procesamiento del discurso",
            "Modelos conexionistas", "Modelos simbólicos",
            "La lectura y sus procesos", "La escritura y sus procesos",
            "La conciencia fonológica", "La conciencia morfológica",
        ],
        "preguntas": [
            "¿Qué estudia la psicolingüística?",
            "¿En qué etapa se adquiere el lenguaje?",
            "¿Qué proceso interviene en la lectura?",
            "¿Qué es la conciencia fonológica?",
            "¿Cómo se procesa una oración?",
        ],
        "respuestas": [
            "Los procesos mentales involucrados en el lenguaje.",
            "En la primera infancia (0-6 años).",
            "El acceso léxico y la integración semántica.",
            "Es la capacidad de manipular sonidos del lenguaje.",
            "Se procesa en niveles sintáctico y semántico.",
        ],
    },
    "Antropolingüística": {
        "titulos": [
            "Lenguaje y cultura", "El relativismo lingüístico",
            "La hipótesis Sapir-Whorf", "Etnografía de la comunicación",
            "Comunidades de habla", "Repertorios lingüísticos",
            "Variación dialectal", "Lenguas en contacto",
            "Bilingüismo social", "Diglosia", "Lenguas minorizadas",
            "Revitalización lingüística", "Lenguaje y género",
            "Lenguaje y poder", "Lenguaje e identidad",
            "Rituales del habla", "Cortesía intercultural",
            "Metáforas culturales", "Semántica cultural",
            "Etnociencia",
        ],
        "preguntas": [
            "¿Qué estudia la antropolingüística?",
            "¿Qué sostiene la hipótesis Sapir-Whorf?",
            "¿Qué es una comunidad de habla?",
            "¿Qué es la diglosia?",
            "¿Cómo influye la cultura en el lenguaje?",
        ],
        "respuestas": [
            "La relación entre lenguaje, cultura y sociedad.",
            "Que el lenguaje determina el pensamiento.",
            "Un grupo que comparte normas de uso lingüístico.",
            "Es la coexistencia de dos lenguas con funciones distintas.",
            "La cultura moldea los significados y usos del lenguaje.",
        ],
    },
}


# ─────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────

def elegir_plantilla(materia_nombre):
    """Devuelve la plantilla adecuada según la materia."""
    if not materia_nombre:
        return PLANTILLAS["Gramática"]

    for clave in PLANTILLAS:
        if clave.lower() in materia_nombre.lower():
            return PLANTILLAS[clave]

    # Fallback por si no coincide
    return PLANTILLAS["Gramática"]


def generar_lecciones(curso, cantidad):
    """Genera y guarda lecciones para un curso."""
    plantilla = elegir_plantilla(curso.materia.nombre if curso.materia else "")

    # Cuántas lecciones tiene el curso actualmente
    offset = curso.lecciones.count()

    nuevos = []
    for i in range(cantidad):
        idx_titulo = (offset + i) % len(plantilla["titulos"])
        idx_pregunta = (offset + i) % len(plantilla["preguntas"])
        idx_respuesta = (offset + i) % len(plantilla["respuestas"])

        titulo = plantilla["titulos"][idx_titulo]
        pregunta = plantilla["preguntas"][idx_pregunta]
        respuesta = plantilla["respuestas"][idx_respuesta]

        # Ejercicio JSON
        ejercicio = {
            "pregunta": pregunta,
            "respuesta": respuesta,
            "explicacion": f"Ejercicio de {curso.materia.nombre if curso.materia else 'la materia'}",
        }

        leccion = Leccion(
            curso=curso,
            titulo=f"{titulo} ({offset + i + 1})",
            pais_origen="Digital",
            explicacion=f"Lección {offset + i + 1} del curso {curso.titulo}. "
                        f"Contenido temático de {curso.materia.nombre if curso.materia else 'la materia'}.",
            ejemplo_uso=f"Ejemplo aplicado de {titulo.lower()} en contexto real.",
            ejercicio_datos=ejercicio,
            orden=offset + i + 1,
        )
        nuevos.append(leccion)

    Leccion.objects.bulk_create(nuevos)
    return len(nuevos)


def main():
    print("=" * 70)
    print("  GENERADOR DE LECCIONES DE PRUEBA")
    print("=" * 70)
    print()

    # Elegir cursos con pocas lecciones
    cursos = Curso.objects.all()
    print(f"Cursos totales: {cursos.count()}")
    print()

    # Configuración: cuántas lecciones por curso
    CANTIDAD_POR_CURSO = 10
    MINIMO_LECCIONES = 15

    actualizados = 0
    total_lecciones = 0

    for curso in cursos:
        n_actual = curso.lecciones.count()

        if n_actual >= MINIMO_LECCIONES:
            print(f"  ⏭️  {curso.titulo[:50]:50s} | {n_actual} lecciones (ya tiene suficientes)")
            continue

        cantidad = CANTIDAD_POR_CURSO
        creadas = generar_lecciones(curso, cantidad)
        total_lecciones += creadas
        actualizados += 1
        print(f"  ✅ {curso.titulo[:50]:50s} | +{creadas} lecciones (total: {n_actual + creadas})")

    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print(f"  Cursos actualizados: {actualizados}")
    print(f"  Lecciones creadas:   {total_lecciones}")
    print(f"  Total lecciones BD:  {Leccion.objects.count()}")


if __name__ == "__main__":
    main()
