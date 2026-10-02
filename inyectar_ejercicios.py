import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.apps import apps
from django.contrib.auth.models import User

def cargar_datos():
    Materia = apps.get_model('courses', 'Materia')
    Curso = apps.get_model('courses', 'Curso')
    Leccion = apps.get_model('courses', 'Leccion')

    print("🚀 Iniciando Protocolo de Inyección Maestra...")

    profesor = User.objects.filter(is_superuser=True).first()
    if not profesor:
        print("❌ ERROR: No hay superusuario. Ejecute: python manage.py createsuperuser")
        return

    # 1. Crear la Materia (Solo con nombre, sin profesor)
    materia_base, _ = Materia.objects.get_or_create(
        nombre="Ingeniería de Software Soberano"
    )

    # 2. Crear el Curso (Aquí el profesor SÍ es obligatorio según logs previos)
    curso_base, _ = Curso.objects.get_or_create(
        titulo="Curso de Soberanía Digital",
        defaults={
            'materia': materia_base,
            'profesor': profesor,
            'nivel': 'Intermedio'
        }
    )

    # 3. Cargar e Inyectar
    try:
        with open('semilla_ejercicios.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
    except FileNotFoundError:
        print("❌ ERROR: No se encontró semilla_ejercicios.json")
        return

    for item in datos:
        datos_ejercicio = {
            "pregunta": item['pregunta'],
            "respuesta": item['respuesta'],
            "explicacion": "Validación técnica obligatoria."
        }

        leccion, created = Leccion.objects.get_or_create(
            id=item['id'],
            defaults={
                'curso': curso_base,
                'titulo': f"Hito {item['id']}: {item['categoria']}",
                'pais_origen': "Digital",
                'explicacion': f"Entrenamiento en {item['categoria']}",
                'ejemplo_uso': item['pregunta'],
                'ejercicio_datos': datos_ejercicio,
                'orden': item['id']
            }
        )
        if created:
            print(f"✅ Hito {item['id']} inyectado.")
        else:
            print(f"⚠️ Hito {item['id']} ya existía.")

if __name__ == '__main__':
    cargar_datos()
