# poblar_estudiantes.py
"""
Crea 10 estudiantes de prueba que toman el curso principal,
con progreso, puntos, medallas, entregas y certificados realistas.
"""

import os
import django
import random
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from courses.models import (
    Curso, Leccion, Inscripcion, ProgresoEstudiante,
    Tarea, Entrega, Certificado, emitir_certificado,
)
from users.models import (
    Perfil, Logro, LogroUsuario,
    calcular_rango, verificar_logros, otorgar_logro,
)


# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────

ESTUDIANTES = [
    {"username": "ana_lopez",     "first": "Ana",     "last": "López",    "email": "ana@test.com",      "perfil": 0.95},
    {"username": "carlos_ruiz",   "first": "Carlos",  "last": "Ruiz",     "email": "carlos@test.com",   "perfil": 0.80},
    {"username": "maria_garcia",  "first": "María",   "last": "García",   "email": "maria@test.com",    "perfil": 0.65},
    {"username": "juan_perez",    "first": "Juan",    "last": "Pérez",    "email": "juan@test.com",     "perfil": 0.50},
    {"username": "lucia_torres",  "first": "Lucía",   "last": "Torres",   "email": "lucia@test.com",    "perfil": 0.40},
    {"username": "diego_mora",    "first": "Diego",   "last": "Mora",     "email": "diego@test.com",    "perfil": 0.30},
    {"username": "sofia_vega",    "first": "Sofía",   "last": "Vega",     "email": "sofia@test.com",    "perfil": 0.20},
    {"username": "andres_cruz",   "first": "Andrés",  "last": "Cruz",     "email": "andres@test.com",   "perfil": 0.15},
    {"username": "valentina_rio", "first": "Valentina","last": "Río",     "email": "valentina@test.com","perfil": 0.08},
    {"username": "pablo_soto",    "first": "Pablo",   "last": "Soto",     "email": "pablo@test.com",    "perfil": 0.03},
]

PASSWORD = "test123456"


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def crear_usuario(info):
    """Crea el User + Perfil si no existe."""
    user, created = User.objects.get_or_create(
        username=info["username"],
        defaults={
            "first_name": info["first"],
            "last_name": info["last"],
            "email": info["email"],
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()

    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    perfil.rol_principal = "estudiante"
    perfil.save()

    return user, created


def inscribir_estudiante(user, curso):
    """Inscribe al estudiante si no lo está."""
    inscripcion, created = Inscripcion.objects.get_or_create(
        estudiante=user, curso=curso,
        defaults={"activa": True}
    )
    return inscripcion, created


def completar_lecciones(user, curso, fraccion):
    """Marca un % de las lecciones del curso como completadas."""
    lecciones = list(curso.lecciones.all().order_by('orden'))
    total = len(lecciones)
    num_completar = int(total * fraccion)

    if num_completar == 0:
        return 0

    # Barajar para simular que completó en orden aleatorio
    # (pero los primeros suelen estar completados primero)
    seleccionadas = lecciones[:num_completar]

    completadas = 0
    for lec in seleccionadas:
        _, created = ProgresoEstudiante.objects.get_or_create(
            estudiante=user, leccion=lec,
            defaults={"completada": True}
        )
        if created:
            completadas += 1

    # Sumar puntos en el perfil
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    perfil.puntos += completadas * 10
    perfil.save()

    return completadas


def otorgar_logros_auto(user):
    """Otorga todos los logros que correspondan."""
    from courses.models import Inscripcion, ProgresoEstudiante

    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    lecciones = ProgresoEstudiante.objects.filter(estudiante=user, completada=True).count()
    cursos = Inscripcion.objects.filter(estudiante=user, activa=True).count()

    reglas = [
        (lecciones >= 1,   'primer-paso'),
        (lecciones >= 10,  'diez-lecciones'),
        (lecciones >= 50,  'cincuenta-lecciones'),
        (lecciones >= 100, 'cien-lecciones'),
        (lecciones >= 500, 'quinientas-lecciones'),
        (cursos >= 1,      'primer-curso'),
        (perfil.puntos >= 100,  'cien-puntos'),
        (perfil.puntos >= 500,  'quinientos-puntos'),
        (perfil.puntos >= 1000, 'mil-puntos'),
        (perfil.puntos >= 5000, 'cinco-mil-puntos'),
    ]

    for condicion, codigo in reglas:
        if condicion:
            try:
                logro = Logro.objects.get(codigo=codigo, activo=True)
                LogroUsuario.objects.get_or_create(usuario=user, logro=logro)
            except Logro.DoesNotExist:
                pass


def crear_entregas(user, curso):
    """Crea entregas aleatorias para las tareas del curso."""
    tareas = list(curso.tareas.all())
    if not tareas:
        return 0

    # Elegir cuántas tareas entrega (0 a todas)
    num_entregas = random.randint(0, len(tareas))
    tareas_entregar = random.sample(tareas, num_entregas)

    entregadas = 0
    for tarea in tareas_entregar:
        # 60% calificadas, 40% pendientes
        calificada = random.random() < 0.6

        if calificada:
            estado = 'calificada'
            calificacion = random.choice([70, 75, 80, 85, 90, 95, 100])
            retro = random.choice([
                "Excelente trabajo, muy completo.",
                "Buen análisis, pero profundiza más en los ejemplos.",
                "Falta desarrollo en la parte argumentativa.",
                "Muy bien estructurado. ¡Sigue así!",
                "Buen intento, revisa la ortografía.",
            ])
            fecha_cal = timezone.now() - timedelta(days=random.randint(1, 15))
        else:
            estado = 'entregada'
            calificacion = None
            retro = ''
            fecha_cal = None

        _, created = Entrega.objects.get_or_create(
            tarea=tarea, estudiante=user,
            defaults={
                'estado': estado,
                'contenido': f"Entrega de {user.first_name} para la tarea: {tarea.titulo}",
                'calificacion': calificacion,
                'retroalimentacion': retro,
                'fecha_calificacion': fecha_cal,
            }
        )
        if created:
            entregadas += 1
            if calificada and calificacion:
                perfil, _ = Perfil.objects.get_or_create(usuario=user)
                perfil.puntos += calificacion
                perfil.save()

    return entregadas


def crear_certificados(user, curso):
    """Emite certificado si completó el 100%."""
    cert, creado = emitir_certificado(user, curso)
    return cert, creado


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

@transaction.atomic
def main():
    print("=" * 70)
    print("  POBLADOR DE ESTUDIANTES DE PRUEBA")
    print("=" * 70)
    print()

    # 1. Buscar el curso principal
    curso = Curso.objects.first()
    if not curso:
        print("❌ No hay cursos. Crea uno primero.")
        return

    print(f"📚 Curso: {curso.titulo}")
    print(f"   Lecciones: {curso.lecciones.count()}")
    print(f"   Tareas: {curso.tareas.count()}")
    print()

    # 2. Verificar que hay logros
    if Logro.objects.count() == 0:
        print("⚠️  No hay logros. Ejecuta primero: python crear_logros.py")
        return
    print(f"🏅 Logros disponibles: {Logro.objects.count()}")
    print()

    # 3. Crear tareas de ejemplo si no hay
    if curso.tareas.count() == 0:
        print("📝 Creando 3 tareas de ejemplo...")
        for i, (titulo, desc) in enumerate([
            ("Ensayo sobre retórica clásica",
             "Escribe un ensayo de 500 palabras aplicando al menos 3 figuras retóricas."),
            ("Análisis sintáctico",
             "Analiza sintácticamente las siguientes 5 oraciones compuestas."),
            ("Ejercicios de ortografía avanzada",
             "Resuelve los 20 ejercicios de ortografía del capítulo 3."),
        ], 1):
            Tarea.objects.create(
                curso=curso,
                titulo=titulo,
                descripcion=desc,
                tipo='texto',
                estado='publicada',
                puntaje_maximo=100,
                orden=i,
            )
        print(f"   ✅ {curso.tareas.count()} tareas creadas")
        print()

    # 4. Procesar cada estudiante
    stats = {
        'creados': 0,
        'existentes': 0,
        'inscritos': 0,
        'lecciones_completadas': 0,
        'entregas': 0,
        'certificados': 0,
        'logros': 0,
    }

    for i, info in enumerate(ESTUDIANTES, 1):
        print(f"[{i}/10] 👤 {info['username']}")

        # Crear usuario
        user, created = crear_usuario(info)
        if created:
            stats['creados'] += 1
            print(f"     ✅ Usuario creado")
        else:
            stats['existentes'] += 1
            print(f"     ⏭️  Ya existía")

        # Inscribir
        _, inscrito = inscribir_estudiante(user, curso)
        if inscrito:
            stats['inscritos'] += 1
            print(f"     ✅ Inscrito en el curso")

        # Completar lecciones según fracción
        fraccion = info["perfil"] * random.uniform(0.9, 1.1)
        fraccion = min(1.0, max(0.0, fraccion))
        completadas = completar_lecciones(user, curso, fraccion)
        stats['lecciones_completadas'] += completadas
        print(f"     📖 {completadas} lecciones completadas ({int(fraccion*100)}%)")

        # Entregas
        num_entregas = crear_entregas(user, curso)
        stats['entregas'] += num_entregas
        print(f"     📝 {num_entregas} entregas")

        # Logros
        antes = LogroUsuario.objects.filter(usuario=user).count()
        otorgar_logros_auto(user)
        despues = LogroUsuario.objects.filter(usuario=user).count()
        nuevos = despues - antes
        stats['logros'] += nuevos
        if nuevos:
            print(f"     🏅 {nuevos} logros otorgados")

        # Certificado si completó 100%
        if fraccion >= 0.99:
            cert, creado_cert = crear_certificados(user, curso)
            if creado_cert:
                stats['certificados'] += 1
                print(f"     🎓 Certificado emitido: {cert.codigo}")

        # Ver rango
        perfil, _ = Perfil.objects.get_or_create(usuario=user)
        rango, icono, _ = calcular_rango(perfil.puntos)
        print(f"     ⭐ {perfil.puntos} puntos | {icono} {rango}")
        print()

    # 5. Resumen
    print("=" * 70)
    print("  RESUMEN")
    print("=" * 70)
    print(f"  Usuarios creados:       {stats['creados']}")
    print(f"  Usuarios existentes:    {stats['existentes']}")
    print(f"  Inscripciones nuevas:   {stats['inscritos']}")
    print(f"  Lecciones completadas:  {stats['lecciones_completadas']}")
    print(f"  Entregas creadas:       {stats['entregas']}")
    print(f"  Logros otorgados:       {stats['logros']}")
    print(f"  Certificados emitidos:  {stats['certificados']}")
    print()
    print("=" * 70)
    print("  CREDENCIALES")
    print("=" * 70)
    print(f"  Contraseña para TODOS: {PASSWORD}")
    print()
    for info in ESTUDIANTES:
        print(f"    {info['username']:20s} ({info['first']} {info['last']})")
    print()
    print("=" * 70)
    print("  ✅ Listo. Visita /cuenta/dashboard-profesor/ para ver los resultados.")
    print("=" * 70)


if __name__ == "__main__":
    main()
