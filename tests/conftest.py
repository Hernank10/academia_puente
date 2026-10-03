# -*- coding: utf-8 -*-
"""Fixtures compartidas para todos los tests."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from users.models import Perfil, Logro, LogroUsuario, Notificacion
from courses.models import (
    Materia, Curso, Leccion, Inscripcion, ProgresoEstudiante,
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
    Tarea, Entrega, Certificado, RecursoInteractivo,
)


# ==================== USUARIOS ====================
@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        username="test_admin", password="Test1234!",
        is_staff=True, is_superuser=True,
    )
    Perfil.objects.get_or_create(usuario=u, defaults={"rol_principal": "profesor"})
    return u


@pytest.fixture
def profesor_user(db):
    u = User.objects.create_user(
        username="test_profe", password="Test1234!", is_staff=True
    )
    perfil, _ = Perfil.objects.get_or_create(usuario=u)
    perfil.rol_principal = "profesor"
    perfil.save()
    return u


@pytest.fixture
def alumno_user(db):
    u = User.objects.create_user(
        username="test_alumno", password="Test1234!"
    )
    Perfil.objects.get_or_create(usuario=u, defaults={"rol_principal": "estudiante"})
    return u


@pytest.fixture
def otro_alumno(db):
    u = User.objects.create_user(username="otro_alumno", password="Test1234!")
    Perfil.objects.get_or_create(usuario=u)
    return u


# ==================== CONTENIDO ====================
@pytest.fixture
def materia(db):
    return Materia.objects.create(nombre="Gramatica")


@pytest.fixture
def curso(db, profesor_user, materia):
    return Curso.objects.create(
        titulo="Curso de prueba",
        materia=materia,
        idioma="ES",
        nivel="A1",
        profesor=profesor_user,
    )


@pytest.fixture
def curso_con_lecciones(db, curso):
    for i in range(3):
        Leccion.objects.create(
            curso=curso,
            titulo="Leccion {}".format(i + 1),
            pais_origen="Espana",
            explicacion="Explicacion {}".format(i + 1),
            ejemplo_uso="Ejemplo {}".format(i + 1),
            orden=i + 1,
        )
    return curso


@pytest.fixture
def inscripcion(db, alumno_user, curso_con_lecciones):
    return Inscripcion.objects.create(
        estudiante=alumno_user, curso=curso_con_lecciones, activa=True
    )


@pytest.fixture
def evaluacion(db, curso_con_lecciones):
    return Evaluacion.objects.create(
        curso=curso_con_lecciones,
        titulo="Eval de prueba",
        estado="publicada",
        puntaje_maximo=30,
        puntaje_aprobacion=18,
        intentos_maximos=3,
    )


@pytest.fixture
def evaluacion_con_preguntas(db, evaluacion):
    """Crea 4 preguntas: unica, multiple, vf, corta."""
    # Pregunta unica
    p1 = PreguntaEvaluacion.objects.create(
        evaluacion=evaluacion, texto="Cual es correcta?",
        puntaje=10, orden=1, tipo="unica"
    )
    OpcionRespuesta.objects.create(pregunta=p1, texto="Correcta", es_correcta=True, orden=1)
    OpcionRespuesta.objects.create(pregunta=p1, texto="Incorrecta", es_correcta=False, orden=2)

    # Pregunta multiple
    p2 = PreguntaEvaluacion.objects.create(
        evaluacion=evaluacion, texto="Cuales son correctas?",
        puntaje=10, orden=2, tipo="multiple"
    )
    OpcionRespuesta.objects.create(pregunta=p2, texto="Correcta 1", es_correcta=True, orden=1)
    OpcionRespuesta.objects.create(pregunta=p2, texto="Correcta 2", es_correcta=True, orden=2)
    OpcionRespuesta.objects.create(pregunta=p2, texto="Incorrecta", es_correcta=False, orden=3)

    # Pregunta V/F
    p3 = PreguntaEvaluacion.objects.create(
        evaluacion=evaluacion, texto="V o F",
        puntaje=5, orden=3, tipo="vf"
    )
    OpcionRespuesta.objects.create(pregunta=p3, texto="Verdadero", es_correcta=True, orden=1)
    OpcionRespuesta.objects.create(pregunta=p3, texto="Falso", es_correcta=False, orden=2)

    # Pregunta corta
    PreguntaEvaluacion.objects.create(
        evaluacion=evaluacion, texto="Escribe haber",
        puntaje=5, orden=4, tipo="corta",
        respuesta_corta="haber|a ver",
    )

    return evaluacion


@pytest.fixture
def tarea(db, curso_con_lecciones):
    return Tarea.objects.create(
        curso=curso_con_lecciones,
        titulo="Tarea 1",
        descripcion="Entregar algo",
        tipo="texto",
        estado="publicada",
        puntaje_maximo=100,
    )


@pytest.fixture
def entrega(db, tarea, alumno_user):
    return Entrega.objects.create(
        tarea=tarea, estudiante=alumno_user,
        estado="entregada", contenido="Mi respuesta",
    )


@pytest.fixture
def logro(db):
    return Logro.objects.create(
        codigo="test_logro",
        nombre="Test Logro",
        descripcion="Logro de prueba",
        activo=True,
    )


@pytest.fixture
def recurso(db):
    return RecursoInteractivo.objects.create(
        titulo="Recurso de prueba",
        slug="recurso-prueba",
        archivo_html="html_999.html",
        tipo="tecnica",
        activo=True,
    )


# ==================== CLIENTES API ====================
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def alumno_client(api_client, alumno_user):
    token, _ = Token.objects.get_or_create(user=alumno_user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


@pytest.fixture
def profesor_client(api_client, profesor_user):
    token, _ = Token.objects.get_or_create(user=profesor_user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    token, _ = Token.objects.get_or_create(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client
