# -*- coding: utf-8 -*-
"""generar_evaluaciones_5tipos.py

Genera 5 evaluaciones x 30 preguntas para cada curso de la DB.
Usa el contenido real de las lecciones (titulo, pais_origen, explicacion, ejemplo_uso).

Uso:
  python generar_evaluaciones_5tipos.py             -> dry-run
  python generar_evaluaciones_5tipos.py --apply     -> aplica
  python generar_evaluaciones_5tipos.py --apply --limite 5
  python generar_evaluaciones_5tipos.py --reset     -> borra las generadas
  python generar_evaluaciones_5tipos.py --curso 14  -> solo un curso
"""
import os, sys, random, re
from pathlib import Path
from collections import Counter

BASE = Path(r"E:\02_proyectos\academia_puente\_original")
sys.path.insert(0, str(BASE))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from courses.models import (
    Curso, Leccion, Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
)

APPLY = '--apply' in sys.argv
RESET = '--reset' in sys.argv
LIMITE = None
if '--limite' in sys.argv:
    idx = sys.argv.index('--limite')
    if idx + 1 < len(sys.argv):
        LIMITE = int(sys.argv[idx + 1])

CURSO_ID = None
if '--curso' in sys.argv:
    idx = sys.argv.index('--curso')
    if idx + 1 < len(sys.argv):
        CURSO_ID = int(sys.argv[idx + 1])

random.seed(42)

# Marcador para identificar las evaluaciones generadas
PREFIJO = "[AUTO]"
PREGUNTAS_POR_EVAL = 30


# ============================================================
# HELPERS
# ============================================================
def log(msg):
    print(msg)


def limpiar(texto, max_len=200):
    """Limpia HTML y trunca."""
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:max_len]


def extraer_palabras_clave(texto, n=3):
    """Extrae palabras "raras" (no comunes) del texto."""
    if not texto:
        return []
    texto = limpiar(texto)
    # Palabras de 5+ letras
    palabras = re.findall(r'\b[a-záéíóúñ]{5,}\b', texto.lower())
    # Excluir comunes
    stopwords = {
        'sobre', 'entre', 'desde', 'hasta', 'puede', 'tiene', 'hacer',
        'todas', 'todos', 'estos', 'estas', 'donde', 'cuando', 'porque',
        'aunque', 'suele', 'mismo', 'misma', 'estas', 'estos', 'sido',
        'hacia', 'hacia', 'hacia', 'parte', 'forma', 'modo', 'tipo',
        'ejemplo', 'ejemplos', 'palabra', 'palabras', 'frase', 'frases',
        'utiliza', 'utilizan', 'usada', 'usado', 'usadas', 'usados',
        'significa', 'significan', 'significado', 'contexto', 'cultural',
    }
    palabras = [p for p in palabras if p not in stopwords]
    # Contar frecuencia
    c = Counter(palabras)
    return [p for p, _ in c.most_common(n)]


# ============================================================
# GENERADORES DE PREGUNTAS POR TIPO
# ============================================================
def pregunta_unica(leccion, otras_lecciones):
    """Opcion unica. Intenta usar paises; si no, usa titulos como distractores."""
    # --- Estrategia A: paises (mas natural) ---
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
                "texto": "De que pais es tipica la expresion '{}'?".format(
                    limpiar(leccion.titulo, 60)),
                "tipo": "unica",
                "puntaje": 10,
                "explicacion": "La expresion es originaria de {}.".format(correcta),
                "opciones": [
                    {"texto": op, "es_correcta": (op == correcta)}
                    for op in opciones
                ],
            }

    # --- Estrategia B (fallback): titulos como distractores ---
    # Pregunta: "Cual es el titulo correcto de esta leccion?"
    # Correcta: titulo real. Distractores: titulos de OTRAS lecciones.
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
            "texto": "Cual es el titulo de la leccion cuyo pais de origen es '{}'?".format(
                leccion.pais_origen or "desconocido"),
            "tipo": "unica",
            "puntaje": 10,
            "explicacion": "El titulo correcto es '{}'.".format(correcta),
            "opciones": [
                {"texto": op, "es_correcta": (op == correcta)}
                for op in opciones
            ],
        }

    return None



def pregunta_multiple(leccion, otras_lecciones):
    """Multiple con 3 estrategias de fallback."""
    # --- Estrategia A: palabras clave ---
    texto = limpiar(leccion.explicacion, 500)
    if len(texto) >= 50:
        claves = extraer_palabras_clave(texto, n=8)
        if len(claves) >= 4:
            correctas = claves[:2]
            palabras_otras = set()
            for l in otras_lecciones[:15]:
                palabras_otras.update(extraer_palabras_clave(l.explicacion, n=5))
            palabras_otras = [
                p for p in palabras_otras
                if p not in texto.lower() and p not in correctas
            ][:8]
            if len(palabras_otras) >= 2:
                distractores = random.sample(palabras_otras, 2)
                opciones = correctas + distractores
                random.shuffle(opciones)
                return {
                    "texto": "Cuales de estas palabras aparecen en la explicacion de '{}'? (elige 2)".format(
                        limpiar(leccion.titulo, 60)),
                    "tipo": "multiple",
                    "puntaje": 10,
                    "explicacion": "Las 2 palabras correctas estan en el texto.",
                    "opciones": [{"texto": op, "es_correcta": (op in correctas)} for op in opciones],
                }

    # --- Estrategia B: titulos de otras lecciones ---
    titulos = [
        limpiar(l.titulo, 60) for l in otras_lecciones
        if l.titulo and l.id != leccion.id
    ][:20]
    if len(titulos) >= 4:
        correctas = titulos[:2]
        distractores = random.sample(titulos[2:], 2)
        opciones = correctas + distractores
        random.shuffle(opciones)
        return {
            "texto": "Cuales de estos son titulos reales de lecciones de este curso? (elige 2)",
            "tipo": "multiple",
            "puntaje": 10,
            "explicacion": "Los 2 primeros son titulos reales; los otros no existen.",
            "opciones": [{"texto": op, "es_correcta": (op in correctas)} for op in opciones],
        }

    # --- Estrategia C: paises (fallback siempre funciona) ---
    paises_reales = list(set(
        l.pais_origen for l in otras_lecciones if l.pais_origen
    ))
    if leccion.pais_origen and leccion.pais_origen not in paises_reales:
        paises_reales.append(leccion.pais_origen)

    if len(paises_reales) >= 2:
        correctas = random.sample(paises_reales, min(2, len(paises_reales)))
        # Si solo hay 1, duplicarla no tiene sentido; pero con 2+ funciona
        if len(correctas) == 1:
            correctas = correctas * 2  # Solo en caso extremo

        paises_falsos = [
            'Francia', 'Alemania', 'Rusia', 'Japon', 'China', 'Italia',
            'Brasil', 'Corea', 'Grecia', 'Egipto', 'Turquia', 'India',
        ]
        paises_falsos = [p for p in paises_falsos if p not in paises_reales]
        distractores = random.sample(paises_falsos, 2)

        opciones = correctas + distractores
        random.shuffle(opciones)
        return {
            "texto": "Cuales de estos paises corresponden a lecciones de este curso? (elige 2)",
            "tipo": "multiple",
            "puntaje": 10,
            "explicacion": "Los paises correctos aparecen en lecciones del curso.",
            "opciones": [{"texto": op, "es_correcta": (op in correctas)} for op in opciones],
        }

    return None



def pregunta_vf(leccion, otras_lecciones):
    """Verdadero/Falso: 'La lección X es de Y' (aleatorio verdadero o falso)."""
    if not leccion.pais_origen:
        return None

    # Aleatoriamente verdadero o falso
    es_verdadero = random.random() > 0.5

    if es_verdadero:
        pais = leccion.pais_origen
        enunciado = "La expresión '{}' es típica de {}.".format(
            limpiar(leccion.titulo, 60), pais
        )
    else:
        otros_paises = list(set(
            l.pais_origen for l in otras_lecciones
            if l.pais_origen and l.pais_origen != leccion.pais_origen
        ))
        if not otros_paises:
            return None
        pais_falso = random.choice(otros_paises)
        enunciado = "La expresión '{}' es típica de {}.".format(
            limpiar(leccion.titulo, 60), pais_falso
        )

    return {
        "texto": enunciado,
        "tipo": "vf",
        "puntaje": 5,
        "explicacion": "El país correcto es {}.".format(leccion.pais_origen),
        "opciones": [
            {"texto": "Verdadero", "es_correcta": es_verdadero},
            {"texto": "Falso", "es_correcta": not es_verdadero},
        ],
    }


def pregunta_corta(leccion, otras_lecciones):
    """Respuesta corta: '¿Cuál es el título de la lección que trata sobre X?'"""
    claves = extraer_palabras_clave(leccion.explicacion, n=2)
    if not claves:
        return None

    # El estudiante debe escribir una palabra clave
    palabra_objetivo = claves[0]

    return {
        "texto": "Escribe una palabra clave (5+ letras) que aparezca en la explicación de '{}'.".format(
            limpiar(leccion.titulo, 60)
        ),
        "tipo": "corta",
        "puntaje": 10,
        "explicacion": "Por ejemplo: '{}'.".format(palabra_objetivo),
        "respuesta_corta": "|".join(claves),  # Acepta cualquiera de las claves
        "opciones": [],
    }


def pregunta_emparejar(leccion, otras_lecciones):
    """Emparejamiento: título <-> país (2 pares)."""
    if not leccion.pais_origen:
        return None
    # Elegir otra lección con país distinto
    candidatas = [
        l for l in otras_lecciones
        if l.pais_origen and l.pais_origen != leccion.pais_origen and l.titulo
    ]
    if not candidatas:
        return None
    otra = random.choice(candidatas[:10])

    pares = [
        {"izq": limpiar(leccion.titulo, 40), "der": leccion.pais_origen},
        {"izq": limpiar(otra.titulo, 40), "der": otra.pais_origen},
    ]

    return {
        "texto": "Empareja cada expresión con su país de origen.",
        "tipo": "emparejar",
        "puntaje": 10,
        "explicacion": "Une cada expresión con su país.",
        "pares_json": pares,
        "opciones": [],
    }


# ============================================================
# CREADOR DE EVALUACION
# ============================================================
GENERADORES = {
    "unica": pregunta_unica,
    "multiple": pregunta_multiple,
    "vf": pregunta_vf,
    "corta": pregunta_corta,
    "emparejar": pregunta_emparejar,
}


def crear_evaluacion(curso, tipo_eval, n_preguntas, lecciones):
    """
    Crea una Evaluacion con n_preguntas del tipo dado.
    tipo_eval: 'unica', 'multiple', 'vf', 'corta', 'emparejar', 'mixta'
    """
    titulo = "{} Evaluación {} - {}".format(
        PREFIJO,
        tipo_eval.capitalize() if tipo_eval != "mixta" else "Mixta",
        curso.titulo[:50]
    )

    ev = Evaluacion.objects.create(
        curso=curso,
        titulo=titulo,
        descripcion="Evaluación generada automáticamente. {} preguntas tipo {}.".format(
            n_preguntas, tipo_eval
        ),
        estado="publicada",
        puntaje_maximo=n_preguntas * 10,
        puntaje_aprobacion=int(n_preguntas * 10 * 0.6),  # 60%
        intentos_maximos=3,
        tiempo_limite_minutos=45,
    )

    preguntas_creadas = 0
    intentos = 0
    max_intentos = n_preguntas * 5  # para evitar bucle infinito

    while preguntas_creadas < n_preguntas and intentos < max_intentos:
        intentos += 1

        # Elegir lección aleatoria
        lec = random.choice(lecciones)
        otras = [l for l in lecciones if l.id != lec.id]

        # Determinar tipo de pregunta
        if tipo_eval == "mixta":
            tipo_preg = random.choice(["unica", "multiple", "vf", "corta", "emparejar"])
        else:
            tipo_preg = tipo_eval

        # Generar
        generador = GENERADORES[tipo_preg]
        datos = generador(lec, otras)

        if not datos:
            continue

        # Crear pregunta
        p = PreguntaEvaluacion.objects.create(
            evaluacion=ev,
            texto=datos["texto"],
            explicacion=datos.get("explicacion", ""),
            puntaje=datos.get("puntaje", 10),
            orden=preguntas_creadas + 1,
            tipo=datos["tipo"],
            respuesta_corta=datos.get("respuesta_corta", ""),
            pares_json=datos.get("pares_json", []),
        )

        # Crear opciones (si aplica)
        for i, op in enumerate(datos.get("opciones", []), 1):
            OpcionRespuesta.objects.create(
                pregunta=p,
                texto=op["texto"][:500],
                es_correcta=op["es_correcta"],
                orden=i,
            )

        preguntas_creadas += 1

    return ev, preguntas_creadas


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("GENERADOR DE EVALUACIONES - 5 TIPOS x 30 PREGUNTAS")
    print("=" * 70)
    print("Modo:    {}".format("APPLY" if APPLY else "DRY-RUN"))
    print("Reset:   {}".format("SI" if RESET else "NO"))
    print("Limite:  {}".format(LIMITE if LIMITE else "sin limite"))
    print("Curso:   {}".format(CURSO_ID if CURSO_ID else "todos"))
    print("")

    # ============================================================
    # RESET
    # ============================================================
    if RESET:
        if not APPLY:
            print("AVISO: --reset requiere --apply para borrar.")
            return
        qs = Evaluacion.objects.filter(titulo__startswith=PREFIJO)
        total = qs.count()
        print("Borrando {} evaluaciones generadas...".format(total))
        qs.delete()
        print("OK: borradas")
        return

    # ============================================================
    # CURSOS
    # ============================================================
    cursos_qs = Curso.objects.all()
    if CURSO_ID:
        cursos_qs = cursos_qs.filter(id=CURSO_ID)
    if LIMITE:
        cursos_qs = cursos_qs[:LIMITE]

    cursos = list(cursos_qs)
    print("Cursos a procesar: {}".format(len(cursos)))
    print("")

    if not cursos:
        print("No hay cursos. Nada que hacer.")
        return

    # Tipos de evaluaciones a generar
    TIPOS = ["unica", "multiple", "vf", "corta", "mixta"]

    total_ev = 0
    total_preg = 0
    total_opc = 0
    cursos_ok = 0
    cursos_skip = 0

    for i, curso in enumerate(cursos, 1):
        lecciones = list(curso.lecciones.all())
        if len(lecciones) < 5:
            print("  [{}] SKIP: {} (solo {} lecciones)".format(i, curso.titulo[:40], len(lecciones)))
            cursos_skip += 1
            continue

        # Comprobar si ya existen las 5 evaluaciones
        existentes = Evaluacion.objects.filter(
            curso=curso, titulo__startswith=PREFIJO
        ).count()

        if existentes >= 5:
            print("  [{}] SKIP: {} (ya tiene {} evaluaciones generadas)".format(
                i, curso.titulo[:40], existentes))
            cursos_skip += 1
            continue

        print("  [{}] {} ({} lecciones)".format(i, curso.titulo[:50], len(lecciones)))

        if not APPLY:
            print("      -> generaria 5 evaluaciones x {} preguntas".format(PREGUNTAS_POR_EVAL))
            cursos_ok += 1
            continue

        # Crear las 5 evaluaciones
        for tipo in TIPOS:
            ev, n_preg = crear_evaluacion(curso, tipo, PREGUNTAS_POR_EVAL, lecciones)
            total_ev += 1
            total_preg += n_preg

            # Contar opciones creadas
            n_opc = OpcionRespuesta.objects.filter(pregunta__evaluacion=ev).count()
            total_opc += n_opc

            print("      OK: '{}' -> {} preguntas, {} opciones".format(
                tipo, n_preg, n_opc))

        cursos_ok += 1

    # ============================================================
    # RESUMEN
    # ============================================================
    print("")
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("Cursos procesados:        {}".format(cursos_ok))
    print("Cursos saltados:          {}".format(cursos_skip))
    print("Evaluaciones creadas:     {}".format(total_ev))
    print("Preguntas creadas:        {}".format(total_preg))
    print("Opciones creadas:         {}".format(total_opc))
    print("")

    if not APPLY:
        print("MODO DRY-RUN: nada ha sido creado.")
        print("")
        print("Para aplicar:")
        print("  python generar_evaluaciones_5tipos.py --apply")
        print("  python generar_evaluaciones_5tipos.py --apply --limite 5")
        print("  python generar_evaluaciones_5tipos.py --apply --curso 14")
    else:
        print("Totales en DB:")
        print("  Evaluaciones:  {}".format(Evaluacion.objects.count()))
        print("  Preguntas:     {}".format(PreguntaEvaluacion.objects.count()))
        print("  Opciones:      {}".format(OpcionRespuesta.objects.count()))


if __name__ == "__main__":
    main()