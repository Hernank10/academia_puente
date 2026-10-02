# -*- coding: utf-8 -*-
r"""seed_usuarios.py - Crea usuarios de prueba para Academia Puente.

Uso:
    E:\pydj5.bat scripts\\seed_usuarios.py --verificar
    E:\pydj5.bat scripts\\seed_usuarios.py --crear
    E:\pydj5.bat scripts\\seed_usuarios.py --reset
"""
import os
import sys
import random
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from users.models import Perfil, Logro, LogroUsuario
from courses.models import (
    Curso, Leccion, ProgresoEstudiante, Inscripcion,
    Certificado, Materia,
)


# ============================================================
# CONFIGURACION
# ============================================================
N_ADMINS = 3
N_PROFESORES = 9
N_ESTUDIANTES = 96
N_CERTIFICADOS = 39
CURSOS_POR_ESTUDIANTE_MIN = 5
CURSOS_POR_ESTUDIANTE_MAX = 15

PASSWORD = "Test1234!"

# Prefijos
PREFIJO_ADMIN = "admin_test_"
PREFIJO_PROFE = "profe_test_"
PREFIJO_EST = "est_test_"


# ============================================================
# HELPERS
# ============================================================
def contar_existentes():
    return {
        "admins": User.objects.filter(username__startswith=PREFIJO_ADMIN).count(),
        "profesores": User.objects.filter(username__startswith=PREFIJO_PROFE).count(),
        "estudiantes": User.objects.filter(username__startswith=PREFIJO_EST).count(),
        "total_users": User.objects.count(),
        "cursos": Curso.objects.count(),
        "lecciones": Leccion.objects.count(),
        "inscripciones": Inscripcion.objects.count(),
        "progresos": ProgresoEstudiante.objects.count(),
        "certificados": Certificado.objects.count(),
        "logros_disponibles": Logro.objects.count(),
        "logros_usuario": LogroUsuario.objects.count(),
    }


def imprimir_estado(titulo, datos):
    print("")
    print("=" * 60)
    print(titulo)
    print("=" * 60)
    for k, v in datos.items():
        print("  {:<20s}: {}".format(k, v))
    print("=" * 60)


def crear_admin(n):
    username = "{}{:02d}".format(PREFIJO_ADMIN, n)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': "{}@test.local".format(username),
            'first_name': "Admin",
            'last_name': "Test {}".format(n),
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
        # Crear perfil
        Perfil.objects.get_or_create(usuario=user)
    return user, created


def crear_profesor(n):
    username = "{}{:02d}".format(PREFIJO_PROFE, n)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': "{}@test.local".format(username),
            'first_name': "Profesor",
            'last_name': "Test {}".format(n),
            'is_staff': True,
            'is_superuser': False,
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
    # Crear/actualizar perfil como profesor
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    perfil.rol_principal = 'profesor'
    perfil.estado_academico = random.choice(['licenciado', 'magister'])
    perfil.puede_publicar_cursos = True
    perfil.save()
    return user, created


def crear_estudiante(n):
    username = "{}{:03d}".format(PREFIJO_EST, n)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': "{}@test.local".format(username),
            'first_name': "Estudiante",
            'last_name': "Test {}".format(n),
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    perfil.rol_principal = 'estudiante'
    perfil.estado_academico = 'grado'
    perfil.save()
    return user, created


def asignar_cursos_a_profesor(profesor, cursos, n_cursos):
    """Asigna n cursos al profesor."""
    seleccion = random.sample(cursos, min(n_cursos, len(cursos)))
    for curso in seleccion:
        curso.profesor = profesor
        curso.save()
    return len(seleccion)


def inscribir_estudiante(estudiante, cursos):
    """Inscribe al estudiante en un rango aleatorio de cursos."""
    n = random.randint(CURSOS_POR_ESTUDIANTE_MIN, CURSOS_POR_ESTUDIANTE_MAX)
    n = min(n, len(cursos))
    seleccion = random.sample(cursos, n)
    inscritos = 0
    for curso in seleccion:
        _, created = Inscripcion.objects.get_or_create(
            estudiante=estudiante,
            curso=curso,
            defaults={'activa': True}
        )
        if created:
            inscritos += 1
    return inscritos


def progresar_curso(estudiante, curso, porcentaje):
    """Marca lecciones como completadas segun porcentaje."""
    lecciones = list(curso.lecciones.all())
    if not lecciones:
        return 0
    n_completar = int(len(lecciones) * porcentaje / 100)
    completadas = 0
    for leccion in lecciones[:n_completar]:
        prog, created = ProgresoEstudiante.objects.get_or_create(
            estudiante=estudiante,
            leccion=leccion,
            defaults={'completada': True}
        )
        if created:
            completadas += 1
        elif not prog.completada:
            prog.completada = True
            prog.save()
            completadas += 1
    return completadas

# ============================================================
# COMANDOS
# ============================================================
def cmd_verificar():
    datos = contar_existentes()
    imprimir_estado("ESTADO ACTUAL DE LA DB", datos)

    esperado = {
        "admins": N_ADMINS,
        "profesores": N_PROFESORES,
        "estudiantes": N_ESTUDIANTES,
    }
    print("")
    print("COMPARACION vs ESPERADO:")
    for k, v in esperado.items():
        actual = datos[k]
        estado = "OK" if actual >= v else "FALTAN {}".format(v - actual)
        print("  {:<15s}: {}/{}  [{}]".format(k, actual, v, estado))


def cmd_crear():
    print("CREANDO USUARIOS DE PRUEBA - ACADEMIA PUENTE")
    print("=" * 60)

    # 1. Materias (crear si no existen)
    materias_nombres = [
        'Gramatica', 'Ortografia', 'Vocabulario', 'Literatura',
        'Redaccion', 'Linguistica', 'Comunicacion',
    ]
    for nombre in materias_nombres:
        Materia.objects.get_or_create(nombre=nombre)
    print("[0] Materias aseguradas: {}".format(Materia.objects.count()))

    # 2. Admins
    print("")
    print("[1] Creando {} admins...".format(N_ADMINS))
    admins = []
    for i in range(1, N_ADMINS + 1):
        u, c = crear_admin(i)
        admins.append(u)
        print("  {}{:02d} {}".format(PREFIJO_ADMIN, i, "[nuevo]" if c else "[ya existe]"))

    # 3. Profesores
    print("")
    print("[2] Creando {} profesores...".format(N_PROFESORES))
    profesores = []
    for i in range(1, N_PROFESORES + 1):
        u, c = crear_profesor(i)
        profesores.append(u)
        print("  {}{:02d} {}".format(PREFIJO_PROFE, i, "[nuevo]" if c else "[ya existe]"))

    # 4. Estudiantes
    print("")
    print("[3] Creando {} estudiantes...".format(N_ESTUDIANTES))
    estudiantes = []
    for i in range(1, N_ESTUDIANTES + 1):
        u, c = crear_estudiante(i)
        estudiantes.append(u)
        if c and i % 20 == 0:
            print("  ...{}/{} creados".format(i, N_ESTUDIANTES))
    print("  Total estudiantes: {}".format(len(estudiantes)))

    # 5. Asignar cursos a profesores
    cursos = list(Curso.objects.all())
    if not cursos:
        print("")
        print("ERROR: no hay cursos. Crea cursos antes de ejecutar este script.")
        return

    print("")
    print("[4] Asignando {} cursos a {} profesores...".format(len(cursos), N_PROFESORES))
    cursos_por_profe = max(1, len(cursos) // N_PROFESORES)

    # Barajar y repartir
    random.shuffle(cursos)
    idx = 0
    for i, profe in enumerate(profesores):
        inicio = idx
        fin = min(idx + cursos_por_profe, len(cursos))
        for curso in cursos[inicio:fin]:
            curso.profesor = profe
            curso.save()
        print("  {} -> {} cursos".format(profe.username, fin - inicio))
        idx = fin

    # Si sobran cursos, repartirlos entre los primeros
    if idx < len(cursos):
        for i, curso in enumerate(cursos[idx:]):
            profe = profesores[i % len(profesores)]
            curso.profesor = profe
            curso.save()
        print("  {} cursos restantes repartidos".format(len(cursos) - idx))

    # 6. Inscribir estudiantes
    print("")
    print("[5] Inscribiendo estudiantes en cursos...")
    total_inscripciones = 0
    for i, est in enumerate(estudiantes, 1):
        n = inscribir_estudiante(est, cursos)
        total_inscripciones += n
        if i % 20 == 0:
            print("  ...{}/{} estudiantes ({} inscripciones)".format(i, N_ESTUDIANTES, total_inscripciones))

    # 7. Generar progreso aleatorio
    print("")
    print("[6] Generando progreso aleatorio...")
    for i, est in enumerate(estudiantes, 1):
        inscripciones = Inscripcion.objects.filter(estudiante=est)
        for insc in inscripciones:
            porcentaje = random.choice([0, 10, 25, 50, 75, 100])
            progresar_curso(est, insc.curso, porcentaje)
        if i % 20 == 0:
            print("  ...{}/{} estudiantes".format(i, N_ESTUDIANTES))

    # 8. Crear certificados (39)
    print("")
    print("[7] Creando {} certificados...".format(N_CERTIFICADOS))
    certs_creados = 0
    intentos_max = 500
    intentos = 0

    # Obtener todos los pares (estudiante, curso) al 100%
    pares_completos = []
    for est in estudiantes:
        for insc in Inscripcion.objects.filter(estudiante=est):
            curso = insc.curso
            total = curso.lecciones.count()
            if total == 0:
                continue
            completadas = ProgresoEstudiante.objects.filter(
                estudiante=est, leccion__curso=curso, completada=True
            ).count()
            if completadas >= total:
                pares_completos.append((est, curso))

    random.shuffle(pares_completos)

    for est, curso in pares_completos:
        if certs_creados >= N_CERTIFICADOS:
            break
        cert, created = Certificado.objects.get_or_create(
            estudiante=est,
            curso=curso,
            defaults={
                'puntos_obtenidos': curso.lecciones.count() * 10,
                'calificacion': random.choice(['Aprobado', 'Sobresaliente', 'Excelente']),
            }
        )
        if created:
            certs_creados += 1
            if certs_creados % 10 == 0:
                print("  ...{} certificados".format(certs_creados))

    print("  Total certificados creados: {}".format(certs_creados))

    # 9. Actualizar puntos de perfiles
    print("")
    print("[8] Actualizando puntos de perfiles...")
    for est in estudiantes:
        perfil, _ = Perfil.objects.get_or_create(usuario=est)
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=est, completada=True
        ).count()
        perfil.puntos = completadas * 5
        perfil.save()
    print("  Puntos actualizados")

    # 10. Asignar logros aleatorios
    print("")
    print("[9] Asignando logros aleatorios...")
    logros = list(Logro.objects.filter(activo=True))
    total_logros = 0
    if logros:
        for est in estudiantes:
            n = random.randint(0, 3)
            for logro in random.sample(logros, min(n, len(logros))):
                _, created = LogroUsuario.objects.get_or_create(
                    usuario=est, logro=logro
                )
                if created:
                    total_logros += 1
    print("  Total logros asignados: {}".format(total_logros))

    # Resumen final
    print("")
    datos = contar_existentes()
    imprimir_estado("RESUMEN FINAL", datos)
    print("")
    print("Password para todos: {}".format(PASSWORD))
    print("Ejemplo login estudiante: {}001 / {}".format(PREFIJO_EST, PASSWORD))
    print("Ejemplo login profesor:   {}01 / {}".format(PREFIJO_PROFE, PASSWORD))
    print("Ejemplo login admin:      {}01 / {}".format(PREFIJO_ADMIN, PASSWORD))


def cmd_reset():
    print("BORRANDO USUARIOS DE PRUEBA...")
    qs = User.objects.filter(
        username__startswith=PREFIJO_ADMIN
    ) | User.objects.filter(
        username__startswith=PREFIJO_PROFE
    ) | User.objects.filter(
        username__startswith=PREFIJO_EST
    )
    total = qs.count()
    qs.delete()
    print("Borrados: {} usuarios (+ inscripciones, progreso, certificados)".format(total))


# ============================================================
# MAIN
# ============================================================
def main():
    random.seed(42)
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--verificar"]

    if "--verificar" in args:
        cmd_verificar()
    elif "--crear" in args:
        cmd_crear()
    elif "--reset" in args:
        cmd_reset()
    else:
        print("Uso:")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --verificar")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --crear")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --reset")


if __name__ == "__main__":
    main()


# ============================================================
# COMANDOS
# ============================================================
def cmd_verificar():
    datos = contar_existentes()
    imprimir_estado("ESTADO ACTUAL DE LA DB", datos)

    esperado = {
        "admins": N_ADMINS,
        "profesores": N_PROFESORES,
        "estudiantes": N_ESTUDIANTES,
    }
    print("")
    print("COMPARACION vs ESPERADO:")
    for k, v in esperado.items():
        actual = datos[k]
        estado = "OK" if actual >= v else "FALTAN {}".format(v - actual)
        print("  {:<15s}: {}/{}  [{}]".format(k, actual, v, estado))


def cmd_crear():
    print("CREANDO USUARIOS DE PRUEBA - ACADEMIA PUENTE")
    print("=" * 60)

    # 1. Materias (crear si no existen)
    materias_nombres = [
        'Gramatica', 'Ortografia', 'Vocabulario', 'Literatura',
        'Redaccion', 'Linguistica', 'Comunicacion',
    ]
    for nombre in materias_nombres:
        Materia.objects.get_or_create(nombre=nombre)
    print("[0] Materias aseguradas: {}".format(Materia.objects.count()))

    # 2. Admins
    print("")
    print("[1] Creando {} admins...".format(N_ADMINS))
    admins = []
    for i in range(1, N_ADMINS + 1):
        u, c = crear_admin(i)
        admins.append(u)
        print("  {}{:02d} {}".format(PREFIJO_ADMIN, i, "[nuevo]" if c else "[ya existe]"))

    # 3. Profesores
    print("")
    print("[2] Creando {} profesores...".format(N_PROFESORES))
    profesores = []
    for i in range(1, N_PROFESORES + 1):
        u, c = crear_profesor(i)
        profesores.append(u)
        print("  {}{:02d} {}".format(PREFIJO_PROFE, i, "[nuevo]" if c else "[ya existe]"))

    # 4. Estudiantes
    print("")
    print("[3] Creando {} estudiantes...".format(N_ESTUDIANTES))
    estudiantes = []
    for i in range(1, N_ESTUDIANTES + 1):
        u, c = crear_estudiante(i)
        estudiantes.append(u)
        if c and i % 20 == 0:
            print("  ...{}/{} creados".format(i, N_ESTUDIANTES))
    print("  Total estudiantes: {}".format(len(estudiantes)))

    # 5. Asignar cursos a profesores
    cursos = list(Curso.objects.all())
    if not cursos:
        print("")
        print("ERROR: no hay cursos. Crea cursos antes de ejecutar este script.")
        return

    print("")
    print("[4] Asignando {} cursos a {} profesores...".format(len(cursos), N_PROFESORES))
    cursos_por_profe = max(1, len(cursos) // N_PROFESORES)

    # Barajar y repartir
    random.shuffle(cursos)
    idx = 0
    for i, profe in enumerate(profesores):
        inicio = idx
        fin = min(idx + cursos_por_profe, len(cursos))
        for curso in cursos[inicio:fin]:
            curso.profesor = profe
            curso.save()
        print("  {} -> {} cursos".format(profe.username, fin - inicio))
        idx = fin

    # Si sobran cursos, repartirlos entre los primeros
    if idx < len(cursos):
        for i, curso in enumerate(cursos[idx:]):
            profe = profesores[i % len(profesores)]
            curso.profesor = profe
            curso.save()
        print("  {} cursos restantes repartidos".format(len(cursos) - idx))

    # 6. Inscribir estudiantes
    print("")
    print("[5] Inscribiendo estudiantes en cursos...")
    total_inscripciones = 0
    for i, est in enumerate(estudiantes, 1):
        n = inscribir_estudiante(est, cursos)
        total_inscripciones += n
        if i % 20 == 0:
            print("  ...{}/{} estudiantes ({} inscripciones)".format(i, N_ESTUDIANTES, total_inscripciones))

    # 7. Generar progreso aleatorio
    print("")
    print("[6] Generando progreso aleatorio...")
    for i, est in enumerate(estudiantes, 1):
        inscripciones = Inscripcion.objects.filter(estudiante=est)
        for insc in inscripciones:
            porcentaje = random.choice([0, 10, 25, 50, 75, 100])
            progresar_curso(est, insc.curso, porcentaje)
        if i % 20 == 0:
            print("  ...{}/{} estudiantes".format(i, N_ESTUDIANTES))

    # 8. Crear certificados (39)
    print("")
    print("[7] Creando {} certificados...".format(N_CERTIFICADOS))
    certs_creados = 0
    intentos_max = 500
    intentos = 0

    # Obtener todos los pares (estudiante, curso) al 100%
    pares_completos = []
    for est in estudiantes:
        for insc in Inscripcion.objects.filter(estudiante=est):
            curso = insc.curso
            total = curso.lecciones.count()
            if total == 0:
                continue
            completadas = ProgresoEstudiante.objects.filter(
                estudiante=est, leccion__curso=curso, completada=True
            ).count()
            if completadas >= total:
                pares_completos.append((est, curso))

    random.shuffle(pares_completos)

    for est, curso in pares_completos:
        if certs_creados >= N_CERTIFICADOS:
            break
        cert, created = Certificado.objects.get_or_create(
            estudiante=est,
            curso=curso,
            defaults={
                'puntos_obtenidos': curso.lecciones.count() * 10,
                'calificacion': random.choice(['Aprobado', 'Sobresaliente', 'Excelente']),
            }
        )
        if created:
            certs_creados += 1
            if certs_creados % 10 == 0:
                print("  ...{} certificados".format(certs_creados))

    print("  Total certificados creados: {}".format(certs_creados))

    # 9. Actualizar puntos de perfiles
    print("")
    print("[8] Actualizando puntos de perfiles...")
    for est in estudiantes:
        perfil, _ = Perfil.objects.get_or_create(usuario=est)
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=est, completada=True
        ).count()
        perfil.puntos = completadas * 5
        perfil.save()
    print("  Puntos actualizados")

    # 10. Asignar logros aleatorios
    print("")
    print("[9] Asignando logros aleatorios...")
    logros = list(Logro.objects.filter(activo=True))
    total_logros = 0
    if logros:
        for est in estudiantes:
            n = random.randint(0, 3)
            for logro in random.sample(logros, min(n, len(logros))):
                _, created = LogroUsuario.objects.get_or_create(
                    usuario=est, logro=logro
                )
                if created:
                    total_logros += 1
    print("  Total logros asignados: {}".format(total_logros))

    # Resumen final
    print("")
    datos = contar_existentes()
    imprimir_estado("RESUMEN FINAL", datos)
    print("")
    print("Password para todos: {}".format(PASSWORD))
    print("Ejemplo login estudiante: {}001 / {}".format(PREFIJO_EST, PASSWORD))
    print("Ejemplo login profesor:   {}01 / {}".format(PREFIJO_PROFE, PASSWORD))
    print("Ejemplo login admin:      {}01 / {}".format(PREFIJO_ADMIN, PASSWORD))


def cmd_reset():
    print("BORRANDO USUARIOS DE PRUEBA...")
    qs = User.objects.filter(
        username__startswith=PREFIJO_ADMIN
    ) | User.objects.filter(
        username__startswith=PREFIJO_PROFE
    ) | User.objects.filter(
        username__startswith=PREFIJO_EST
    )
    total = qs.count()
    qs.delete()
    print("Borrados: {} usuarios (+ inscripciones, progreso, certificados)".format(total))


# ============================================================
# MAIN
# ============================================================
def main():
    random.seed(42)
    args = sys.argv[1:] if len(sys.argv) > 1 else ["--verificar"]

    if "--verificar" in args:
        cmd_verificar()
    elif "--crear" in args:
        cmd_crear()
    elif "--reset" in args:
        cmd_reset()
    else:
        print("Uso:")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --verificar")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --crear")
        print("  E:\\pydj5.bat scripts\\seed_usuarios.py --reset")


if __name__ == "__main__":
    main()
