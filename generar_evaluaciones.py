# generar_evaluaciones.py
"""
Genera evaluaciones (quizzes) para cada curso a partir
de sus lecciones. Cada evaluación tiene 10 preguntas de opción múltiple.
"""

import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from courses.models import (
    Curso, Leccion, Evaluacion, PreguntaEvaluacion,
    OpcionRespuesta, IntentoEvaluacion, RespuestaIntento,
)


# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────

# Cuántas preguntas por evaluación
PREGUNTAS_POR_EVALUACION = 10

# Cuántas evaluaciones crear por curso
EVALUACIONES_POR_CURSO = 2

# Distractores genéricos para las opciones incorrectas
DISTRACTORES = [
    "Ninguna de las anteriores",
    "Todas las anteriores",
    "La respuesta depende del contexto",
    "No es posible determinarlo",
    "Es una excepción a la regla",
    "Solo en casos específicos",
    "Es un error común",
    "Es una variante dialectal",
    "Es un arcaísmo",
    "Es un neologismo",
]


# ─────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────

def extraer_pregunta_respuesta(leccion):
    """Extrae pregunta y respuesta del ejercicio_datos si existe."""
    if not leccion.ejercicio_datos:
        return None, None

    datos = leccion.ejercicio_datos
    pregunta = datos.get('pregunta', '').strip()
    respuesta = datos.get('respuesta', '').strip()

    if not pregunta or not respuesta:
        return None, None

    # Truncar textos muy largos
    return pregunta[:500], respuesta[:500]


def generar_evaluacion(curso, numero, lecciones_con_ejercicios):
    """Crea una evaluación con preguntas de la lista dada."""
    titulo = f"Evaluación {numero}: {curso.titulo[:60]}"
    descripcion = (
        f"Evaluación de conocimientos sobre {curso.materia.nombre if curso.materia else 'el curso'}. "
        f"Contiene {PREGUNTAS_POR_EVALUACION} preguntas de opción múltiple. "
        f"Puntaje mínimo para aprobar: {curso.nivel}."
    )

    evaluacion, creada = Evaluacion.objects.get_or_create(
        curso=curso,
        titulo=titulo,
        defaults={
            'descripcion': descripcion,
            'estado': 'publicada',
            'puntaje_maximo': PREGUNTAS_POR_EVALUACION * 10,
            'puntaje_aprobacion': int(PREGUNTAS_POR_EVALUACION * 10 * 0.6),
            'intentos_maximos': 3,
            'tiempo_limite_minutos': 30,
            'aleatorizar_preguntas': True,
        }
    )

    if not creada:
        return evaluacion, 0  # Ya existía

    # Elegir lecciones aleatorias
    muestra = random.sample(lecciones_con_ejercicios, min(PREGUNTAS_POR_EVALUACION, len(lecciones_con_ejercicios)))

    preguntas_creadas = 0
    for i, lec in enumerate(muestra, 1):
        pregunta_txt, respuesta_txt = extraer_pregunta_respuesta(lec)
        if not pregunta_txt or not respuesta_txt:
            continue

        # Crear pregunta
        pregunta = PreguntaEvaluacion.objects.create(
            evaluacion=evaluacion,
            texto=pregunta_txt,
            explicacion=f"Respuesta correcta: {respuesta_txt}",
            puntaje=10,
            orden=i,
        )

        # Opciones: correcta + 3 distractores
        opciones = [respuesta_txt]
        distractores_unicos = random.sample(DISTRACTORES, 3)
        opciones.extend(distractores_unicos)

        # Aleatorizar orden
        random.shuffle(opciones)

        for j, opcion_txt in enumerate(opciones, 1):
            OpcionRespuesta.objects.create(
                pregunta=pregunta,
                texto=opcion_txt,
                es_correcta=(opcion_txt == respuesta_txt),
                orden=j,
            )

        preguntas_creadas += 1

    return evaluacion, preguntas_creadas


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  GENERADOR DE EVALUACIONES")
    print("=" * 70)
    print()

    cursos = Curso.objects.all()
    print(f"Cursos totales: {cursos.count()}")
    print(f"Evaluaciones por curso: {EVALUACIONES_POR_CURSO}")
    print(f"Preguntas por evaluación: {PREGUNTAS_POR_EVALUACION}")
    print()

    # Filtrar cursos con al menos N lecciones con ejercicio
    cursos_validos = []
    for curso in cursos:
        lecciones_con_ej = [
            lec for lec in curso.lecciones.all()
            if lec.ejercicio_datos and lec.ejercicio_datos.get('pregunta')
        ]
        if len(lecciones_con_ej) >= PREGUNTAS_POR_EVALUACION:
            cursos_validos.append((curso, lecciones_con_ej))

    print(f"Cursos válidos (con ≥{PREGUNTAS_POR_EVALUACION} lecciones con ejercicio): {len(cursos_validos)}")
    print()

    total_evals = 0
    total_preguntas = 0

    for curso, lecciones in cursos_validos:
        for i in range(1, EVALUACIONES_POR_CURSO + 1):
            evaluacion, n = generar_evaluacion(curso, i, lecciones)
            if n > 0:
                total_evals += 1
                total_preguntas += n
                print(f"  ✅ {curso.titulo[:45]:45s} | Eval {i}: {n} preguntas")
            else:
                print(f"  ⏭️  {curso.titulo[:45]:45s} | Eval {i}: ya existía")

    print()
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print(f"  Evaluaciones creadas: {total_evals}")
    print(f"  Preguntas creadas:    {total_preguntas}")
    print(f"  Total evaluaciones:   {Evaluacion.objects.count()}")
    print(f"  Total preguntas:      {PreguntaEvaluacion.objects.count()}")
    print(f"  Total opciones:       {OpcionRespuesta.objects.count()}")


if __name__ == "__main__":
    main()
