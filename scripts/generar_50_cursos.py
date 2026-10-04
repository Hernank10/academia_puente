# -*- coding: utf-8 -*-
"""generar_50_cursos.py

Genera 50 cursos nuevos completos (lecciones + evaluaciones + recursos vinculados)
a partir de los materiales existentes en la DB (recursos interactivos, lecciones, evaluaciones).

Uso:
  python scripts/generar_50_cursos.py            -> dry-run
  python scripts/generar_50_cursos.py --apply    -> aplica
  python scripts/generar_50_cursos.py --reset --apply  -> borra lo generado
"""
import os, sys, random, re, unicodedata
from pathlib import Path
from collections import Counter

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from courses.models import (
    Materia, Curso, Leccion, RecursoInteractivo,
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
)

APPLY = '--apply' in sys.argv
RESET = '--reset' in sys.argv
random.seed(2026)

PREFIJO_CURSO = "[NUEVO]"


# ============================================================
# DEFINICION DE LOS 50 CURSOS
# ============================================================
# Cada curso: (titulo, materia_nombre, idioma, nivel, tema_clave, n_lecciones)
CURSOS_NUEVOS = [
    # --- GRAMATICA ---
    ("Gramatica: Sustantivos y Adjetivos", "Gramatica", "ES", "A1", "sustantivo adjetivo", 15),
    ("Gramatica: Verbos y Conjugaciones", "Gramatica", "ES", "A2", "verbo conjugacion", 20),
    ("Gramatica: Tiempos Verbales Avanzados", "Gramatica", "ES", "B1", "tiempo verbal", 18),
    ("Gramatica: Oraciones Subordinadas", "Gramatica", "ES", "B2", "subordinada oracion", 22),
    ("Gramatica: Analisis Sintactico", "Gramatica", "ES", "B2", "sintaxis analisis", 25),
    ("Gramatica: Morfologia Avanzada", "Gramatica", "ES", "C1", "morfologia derivacion", 20),
    ("Gramatica Inglesa: Tenses", "Gramatica", "EN", "A2", "english tense verb", 18),
    ("Gramatica Francesa: Le Subjonctif", "Gramatica", "FR", "B1", "francais subjonctif", 15),

    # --- ORTOGRAFIA ---
    ("Ortografia: Acentuacion", "Ortografia", "ES", "A1", "acento tilde", 12),
    ("Ortografia: Uso de B y V", "Ortografia", "ES", "A2", "letra b v", 10),
    ("Ortografia: Uso de G y J", "Ortografia", "ES", "A2", "letra g j", 10),
    ("Ortografia: Uso de H", "Ortografia", "ES", "A1", "letra h", 10),
    ("Ortografia: Uso de C, S y Z", "Ortografia", "ES", "A2", "letra c s z", 12),
    ("Ortografia: Homofonos", "Ortografia", "ES", "B1", "homofono", 14),
    ("Ortografia: Signos de Puntuacion", "Ortografia", "ES", "B1", "puntuacion coma punto", 18),
    ("Ortografia: Mayusculas y Minusculas", "Ortografia", "ES", "A2", "mayuscula minuscula", 10),

    # --- LEXICO ---
    ("Lexico: Sinonimos y Antonimos", "Vocabulario", "ES", "A2", "sinonimo antonimo", 15),
    ("Lexico: Palabras Compuestas", "Vocabulario", "ES", "B1", "compuesta palabra", 12),
    ("Lexico: Prefijos y Sufijos", "Vocabulario", "ES", "B1", "prefijo sufijo", 14),
    ("Lexico: Expresiones Idiomaticas", "Vocabulario", "ES", "B2", "idiomatica expresion", 18),
    ("Lexico: Cultismos y Latinismos", "Vocabulario", "ES", "C1", "latin cultismo", 15),
    ("Lexico: Anglicismos", "Vocabulario", "ES", "B2", "anglicismo prestamo", 12),
    ("Lexico: Refranes y Proverbios", "Vocabulario", "ES", "B1", "refran proverbio", 14),

    # --- LITERATURA ---
    ("Literatura: Poesia Espanola del Siglo de Oro", "Literatura", "ES", "B2", "poesia siglo oro", 20),
    ("Literatura: Generacion del 27", "Literatura", "ES", "C1", "generacion 27 lorca", 15),
    ("Literatura: Novela Hispanoamericana", "Literatura", "ES", "B2", "novela hispanoamerica", 25),
    ("Literatura: Realismo Magico", "Literatura", "ES", "C1", "realismo magico garcia marquez", 18),
    ("Literatura: Teatro Clasico", "Literatura", "ES", "B1", "teatro clasico lope", 16),
    ("Literatura: Cuento Corto", "Literatura", "ES", "B1", "cuento corto narrativa", 15),

    # --- REDACCION ---
    ("Redaccion: El Parrafo", "Redaccion", "ES", "A2", "parrafo redaccion", 15),
    ("Redaccion: Texto Argumentativo", "Redaccion", "ES", "B2", "argumentativo tesis", 20),
    ("Redaccion: Texto Expositivo", "Redaccion", "ES", "B1", "expositivo informativo", 18),
    ("Redaccion: Texto Narrativo", "Redaccion", "ES", "B1", "narrativo narracion", 20),
    ("Redaccion: Texto Descriptivo", "Redaccion", "ES", "B1", "descriptivo descripcion", 15),
    ("Redaccion: Ensayo Academico", "Redaccion", "ES", "C1", "ensayo academico", 22),
    ("Redaccion: Escritura Cientifica", "Redaccion", "ES", "C1", "cientifico metodologia", 20),
    ("Redaccion: Redaccion Administrativa", "Redaccion", "ES", "B2", "administrativa carta oficio", 15),

    # --- FONETICA / FONOLOGIA ---
    ("Fonetica: Vocales y Consonantes", "Fonetica", "ES", "A1", "vocal consonante", 12),
    ("Fonetica: El Alfabeto Fonetico Internacional", "Fonetica", "ES", "B2", "afi alfabeto fonetico", 15),
    ("Fonologia: Fonemas del Espanol", "Fonetica", "ES", "B2", "fonema espanol", 18),

    # --- SINTAXIS ---
    ("Sintaxis: Sujeto y Predicado", "Sintaxis", "ES", "A2", "sujeto predicado", 12),
    ("Sintaxis: Complementos del Verbo", "Sintaxis", "ES", "B2", "complemento verbo", 18),
    ("Sintaxis: Oraciones Compuestas", "Sintaxis", "ES", "B2", "compuesta coordinada", 20),

    # --- INGLES ---
    ("Ingles: Basics for Beginners", "Vocabulario", "EN", "A1", "english basics", 15),
    ("Ingles: Phrasal Verbs", "Vocabulario", "EN", "B2", "phrasal verb", 18),
    ("Ingles: Business English", "Redaccion", "EN", "B1", "business english", 15),

    # --- FRANCES ---
    ("Frances: Grammaire de Base", "Gramatica", "FR", "A1", "francais grammaire", 15),
    ("Frances: Conversation Quotidienne", "Vocabulario", "FR", "A2", "francais conversation", 12),
]


# ============================================================
# HELPERS
# ============================================================
def log(msg):
    print(msg)


def limpiar(texto, max_len=300):
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:max_len]


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def buscar_materia(nombre, cache):
    """Busca o crea la Materia."""
    if nombre in cache:
        return cache[nombre]
    m, _ = Materia.objects.get_or_create(nombre=nombre)
    cache[nombre] = m
    return m


def buscar_recursos_por_tema(tema, limite=5):
    """Busca recursos interactivos que coincidan con el tema."""
    palabras = normalizar(tema).split()
    qs = RecursoInteractivo.objects.filter(activo=True)
    encontrados = []
    for r in qs[:2000]:
        titulo_norm = normalizar(r.titulo or "")
        desc_norm = normalizar(r.descripcion or "")
        for p in palabras:
            if len(p) >= 4 and (p in titulo_norm or p in desc_norm):
                encontrados.append(r)
                break
        if len(encontrados) >= limite:
            break
    return encontrados[:limite]


def elegir_profesor(profesores, materia):
    """Elige un profesor aleatorio."""
    if not profesores:
        return None
    return random.choice(profesores)


# ============================================================
# GENERADOR DE LECCIONES
# ============================================================
def crear_lecciones(curso, n_lecciones, tema, recursos_vinculados):
    """Crea n_lecciones con contenido coherente al tema."""
    lecciones_creadas = 0

    for i in range(1, n_lecciones + 1):
        # Generar título según tema
        if recursos_vinculados and i <= len(recursos_vinculados):
            r = recursos_vinculados[i - 1]
            titulo = "{}: {}".format(tema.title(), limpiar(r.titulo, 100))
        else:
            titulo = "{} - Leccion {}".format(tema.title(), i)

        # Contenido generado
        pais_origen = random.choice([
            "Espana", "Mexico", "Argentina", "Colombia", "Chile",
            "Peru", "Venezuela", "Cuba", "Uruguay",
        ])

        explicacion = (
            "En esta leccion se estudia {} con ejemplos y ejercicios "
            "practicos. El objetivo es dominar los conceptos clave del tema "
            "y aplicarlos en contexto real. Leccion numero {} del curso."
        ).format(tema, i)

        ejemplo_uso = (
            "Ejemplo practico {}: se presenta un caso tipico donde se aplica "
            "{} y se analiza paso a paso."
        ).format(i, tema)

        Leccion.objects.create(
            curso=curso,
            titulo=titulo,
            pais_origen=pais_origen,
            explicacion=explicacion,
            ejemplo_uso=ejemplo_uso,
            orden=i,
        )
        lecciones_creadas += 1

    return lecciones_creadas


# ============================================================
# GENERADOR DE EVALUACIONES
# ============================================================
def pregunta_unica(leccion, otras_lecciones):
    """Opcion unica."""
    if leccion.pais_origen:
        correcta = leccion.pais_origen
        paises_otros = list(set(
            l.pais_origen for l in otras_lecciones
            if l.pais_origen and l.pais_origen != correcta
        ))[:8]
        if len(paises_otros) >= 3:
            distractores = random.sample(paises_otros, 3)
            opciones = [correcta] + distractores
            random.shuffle(opciones)
            return {
                "texto": "De que pais es tipica la leccion '{}'?".format(
                    limpiar(leccion.titulo, 60)),
                "tipo": "unica",
                "puntaje": 10,
                "explicacion": "Es de {}.".format(correcta),
                "opciones": [{"texto": op, "es_correcta": (op == correcta)} for op in opciones],
            }

    # Fallback: usar titulos
    titulos_otros = [
        limpiar(l.titulo, 60) for l in otras_lecciones
        if l.titulo and l.id != leccion.id
    ][:10]
    if len(titulos_otros) >= 3:
        correcta = limpiar(leccion.titulo, 60)
        distractores = random.sample(titulos_otros, 3)
        opciones = [correcta] + distractores
        random.shuffle(opciones)
        return {
            "texto": "Cual es el titulo correcto de esta leccion?",
            "tipo": "unica",
            "puntaje": 10,
            "explicacion": "El titulo es '{}'.".format(correcta),
            "opciones": [{"texto": op, "es_correcta": (op == correcta)} for op in opciones],
        }
    return None


def pregunta_multiple(leccion, otras_lecciones):
    """Multiple con paises (siempre funciona)."""
    paises_reales = list(set(
        l.pais_origen for l in otras_lecciones if l.pais_origen
    ))[:6]
    if leccion.pais_origen and leccion.pais_origen not in paises_reales:
        paises_reales.append(leccion.pais_origen)

    if len(paises_reales) >= 2:
        correctas = random.sample(paises_reales, 2)
        paises_falsos = [
            'Italia', 'Alemania', 'Rusia', 'Japon', 'China',
            'Brasil', 'Grecia', 'Egipto', 'Turquia', 'India',
        ]
        paises_falsos = [p for p in paises_falsos if p not in paises_reales]
        if len(paises_falsos) >= 2:
            distractores = random.sample(paises_falsos, 2)
            opciones = correctas + distractores
            random.shuffle(opciones)
            return {
                "texto": "Cuales de estos paises corresponden a lecciones del curso? (elige 2)",
                "tipo": "multiple",
                "puntaje": 10,
                "explicacion": "Los 2 correctos aparecen en lecciones del curso.",
                "opciones": [{"texto": op, "es_correcta": (op in correctas)} for op in opciones],
            }
    return None


def pregunta_vf(leccion, otras_lecciones):
    """Verdadero/Falso."""
    if not leccion.pais_origen:
        return None

    es_v = random.random() > 0.5
    if es_v:
        enunciado = "La leccion '{}' esta asociada a {}.".format(
            limpiar(leccion.titulo, 60), leccion.pais_origen)
    else:
        otros = list(set(
            l.pais_origen for l in otras_lecciones
            if l.pais_origen and l.pais_origen != leccion.pais_origen
        ))
        if not otros:
            return None
        falso = random.choice(otros)
        enunciado = "La leccion '{}' esta asociada a {}.".format(
            limpiar(leccion.titulo, 60), falso)

    return {
        "texto": enunciado,
        "tipo": "vf",
        "puntaje": 5,
        "explicacion": "El pais correcto es {}.".format(leccion.pais_origen),
        "opciones": [
            {"texto": "Verdadero", "es_correcta": es_v},
            {"texto": "Falso", "es_correcta": not es_v},
        ],
    }


def pregunta_corta(leccion, otras_lecciones):
    """Respuesta corta: pais."""
    if leccion.pais_origen:
        return {
            "texto": "Escribe el pais de origen de la leccion '{}'.".format(
                limpiar(leccion.titulo, 60)),
            "tipo": "corta",
            "puntaje": 10,
            "explicacion": "Respuesta: {}".format(leccion.pais_origen),
            "respuesta_corta": leccion.pais_origen,
            "opciones": [],
        }

    # Fallback: pais aleatorio
    return {
        "texto": "Escribe el pais de origen de la leccion.",
        "tipo": "corta",
        "puntaje": 10,
        "explicacion": "Cualquier pais valido.",
        "respuesta_corta": "Espana|Mexico|Argentina|Colombia",
        "opciones": [],
    }


def pregunta_emparejar(leccion, otras_lecciones):
    """Emparejamiento: titulo <-> pais."""
    if not leccion.pais_origen:
        return None
    candidatas = [
        l for l in otras_lecciones
        if l.pais_origen and l.pais_origen != leccion.pais_origen and l.titulo
    ]
    if not candidatas:
        return None
    otra = random.choice(candidatas[:10])

    return {
        "texto": "Empareja cada leccion con su pais de origen.",
        "tipo": "emparejar",
        "puntaje": 10,
        "explicacion": "Une cada titulo con su pais.",
        "pares_json": [
            {"izq": limpiar(leccion.titulo, 40), "der": leccion.pais_origen},
            {"izq": limpiar(otra.titulo, 40), "der": otra.pais_origen},
        ],
        "opciones": [],
    }


GENERADORES = {
    "unica": pregunta_unica,
    "multiple": pregunta_multiple,
    "vf": pregunta_vf,
    "corta": pregunta_corta,
    "emparejar": pregunta_emparejar,
}


def crear_evaluacion(curso, tipo_eval, n_preguntas, lecciones):
    """Crea una Evaluacion con n_preguntas."""
    titulo = "[AUTO] Evaluacion {} - {}".format(
        tipo_eval.capitalize() if tipo_eval != "mixta" else "Mixta",
        curso.titulo[:50]
    )

    ev = Evaluacion.objects.create(
        curso=curso,
        titulo=titulo,
        descripcion="Evaluacion generada automaticamente.",
        estado="publicada",
        puntaje_maximo=n_preguntas * 10,
        puntaje_aprobacion=int(n_preguntas * 10 * 0.6),
        intentos_maximos=3,
        tiempo_limite_minutos=45,
    )

    creadas = 0
    intentos = 0
    max_intentos = n_preguntas * 5

    while creadas < n_preguntas and intentos < max_intentos:
        intentos += 1
        lec = random.choice(lecciones)
        otras = [l for l in lecciones if l.id != lec.id]

        tipo_preg = tipo_eval if tipo_eval != "mixta" else random.choice(
            list(GENERADORES.keys())
        )
        generador = GENERADORES[tipo_preg]
        datos = generador(lec, otras)
        if not datos:
            continue

        p = PreguntaEvaluacion.objects.create(
            evaluacion=ev,
            texto=datos["texto"],
            explicacion=datos.get("explicacion", ""),
            puntaje=datos.get("puntaje", 10),
            orden=creadas + 1,
            tipo=datos["tipo"],
            respuesta_corta=datos.get("respuesta_corta", ""),
            pares_json=datos.get("pares_json", []),
        )
        for i, op in enumerate(datos.get("opciones", []), 1):
            OpcionRespuesta.objects.create(
                pregunta=p,
                texto=op["texto"][:500],
                es_correcta=op["es_correcta"],
                orden=i,
            )
        creadas += 1

    return ev, creadas


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("GENERADOR DE 50 CURSOS NUEVOS")
    print("=" * 70)
    print("Modo: {}".format("APPLY" if APPLY else "DRY-RUN"))
    print("Reset: {}".format("SI" if RESET else "NO"))
    print("")

    # ============================================================
    # RESET
    # ============================================================
    if RESET:
        if not APPLY:
            print("AVISO: --reset requiere --apply")
            return
        qs = Curso.objects.filter(titulo__startswith=PREFIJO_CURSO)
        total = qs.count()
        print("Borrando {} cursos generados...".format(total))
        qs.delete()
        print("OK: borrados")
        return

    # ============================================================
    # Verificar prerequisitos
    # ============================================================
    profesores = list(User.objects.filter(
        perfil__rol_principal="profesor"
    )[:20])
    if not profesores:
        profesores = list(User.objects.filter(is_staff=True)[:10])
    if not profesores:
        profesores = list(User.objects.filter(is_superuser=True)[:5])

    if not profesores:
        print("ERROR: no hay profesores ni superusers en la DB")
        return

    print("Profesores disponibles: {}".format(len(profesores)))
    print("Recursos interactivos:   {}".format(RecursoInteractivo.objects.count()))
    print("Materias existentes:     {}".format(Materia.objects.count()))
    print("")

    # ============================================================
    # Procesar cada curso
    # ============================================================
    cache_materias = {}
    total_curso_ok = 0
    total_curso_skip = 0
    total_lecciones = 0
    total_evals = 0
    total_preguntas = 0
    total_opciones = 0
    total_recursos_vinculados = 0

    for i, (titulo, materia_nombre, idioma, nivel, tema, n_lec) in enumerate(CURSOS_NUEVOS, 1):
        titulo_completo = "{} {}".format(PREFIJO_CURSO, titulo)

        # Verificar si ya existe
        if Curso.objects.filter(titulo=titulo_completo).exists():
            print("  [{:2d}/50] SKIP: {}".format(i, titulo[:50]))
            total_curso_skip += 1
            continue

        print("  [{:2d}/50] {}".format(i, titulo[:55]))

        if not APPLY:
            print("         -> {} lecciones, 5 evaluaciones".format(n_lec))
            total_curso_ok += 1
            continue

        # 1. Materia
        materia = buscar_materia(materia_nombre, cache_materias)

        # 2. Profesor aleatorio
        profesor = elegir_profesor(profesores, materia)

        # 3. Curso
        curso = Curso.objects.create(
            titulo=titulo_completo,
            materia=materia,
            idioma=idioma,
            nivel=nivel,
            profesor=profesor,
        )

        # 4. Buscar recursos vinculados
        recursos = buscar_recursos_por_tema(tema, limite=n_lec)
        total_recursos_vinculados += len(recursos)

        # 5. Crear lecciones
        n_lecciones = crear_lecciones(curso, n_lec, tema, recursos)
        total_lecciones += n_lecciones

        # 6. Crear evaluaciones
        lecciones = list(curso.lecciones.all())
        for tipo in ["unica", "multiple", "vf", "corta", "mixta"]:
            ev, n_preg = crear_evaluacion(curso, tipo, 30, lecciones)
            total_evals += 1
            total_preguntas += n_preg
            n_opc = OpcionRespuesta.objects.filter(pregunta__evaluacion=ev).count()
            total_opciones += n_opc

        total_curso_ok += 1

    # ============================================================
    # RESUMEN
    # ============================================================
    print("")
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("Cursos creados:            {}".format(total_curso_ok))
    print("Cursos saltados:           {}".format(total_curso_skip))
    print("Lecciones creadas:         {}".format(total_lecciones))
    print("Evaluaciones creadas:      {}".format(total_evals))
    print("Preguntas creadas:         {}".format(total_preguntas))
    print("Opciones creadas:          {}".format(total_opciones))
    print("Recursos vinculados:       {}".format(total_recursos_vinculados))
    print("")

    if not APPLY:
        print("MODO DRY-RUN: nada fue creado.")
        print("Para aplicar:")
        print("  python scripts/generar_50_cursos.py --apply")
    else:
        print("Totales en DB:")
        print("  Cursos:       {}".format(Curso.objects.count()))
        print("  Lecciones:    {}".format(Leccion.objects.count()))
        print("  Evaluaciones: {}".format(Evaluacion.objects.count()))
        print("  Preguntas:    {}".format(PreguntaEvaluacion.objects.count()))


if __name__ == "__main__":
    main()