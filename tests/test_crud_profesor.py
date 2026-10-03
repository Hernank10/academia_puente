# -*- coding: utf-8 -*-
"""Tests de CRUD del profesor en la API."""
import pytest
from courses.models import Leccion, Tarea, Evaluacion


@pytest.mark.django_db
class TestProfesorLecciones:
    def test_crear_leccion(self, profesor_client, curso):
        resp = profesor_client.post("/api/v1/profesor/lecciones/", {
            "curso": curso.id,
            "titulo": "Nueva leccion",
            "pais_origen": "Espana",
            "explicacion": "Texto",
            "ejemplo_uso": "Ejemplo",
            "orden": 1,
        }, format="json")
        assert resp.status_code in (200, 201)

    def test_lista_lecciones(self, profesor_client, curso_con_lecciones):
        resp = profesor_client.get("/api/v1/profesor/lecciones/")
        assert resp.status_code == 200

    def test_alumno_no_crea(self, alumno_client, curso):
        resp = alumno_client.post("/api/v1/profesor/lecciones/", {
            "curso": curso.id, "titulo": "X",
        }, format="json")
        assert resp.status_code == 403


@pytest.mark.django_db
class TestProfesorTareas:
    def test_crear_tarea(self, profesor_client, curso):
        resp = profesor_client.post("/api/v1/profesor/tareas/", {
            "curso": curso.id,
            "titulo": "Tarea nueva",
            "descripcion": "Hacer X",
            "tipo": "texto",
            "estado": "publicada",
            "puntaje_maximo": 100,
        }, format="json")
        assert resp.status_code in (200, 201)

    def test_lista_tareas(self, profesor_client, tarea):
        resp = profesor_client.get("/api/v1/profesor/tareas/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestProfesorEvaluaciones:
    def test_crear_evaluacion(self, profesor_client, curso):
        resp = profesor_client.post("/api/v1/profesor/evaluaciones/", {
            "curso": curso.id,
            "titulo": "Eval nueva",
            "descripcion": "Hacer",
            "estado": "publicada",
            "puntaje_maximo": 100,
            "puntaje_aprobacion": 60,
        }, format="json")
        assert resp.status_code in (200, 201)

    def test_lista_evaluaciones(self, profesor_client, evaluacion):
        resp = profesor_client.get("/api/v1/profesor/evaluaciones/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestProfesorAislamiento:
    def test_no_ve_lecciones_de_otros(self, profesor_client, materia):
        from django.contrib.auth.models import User
        from courses.models import Curso
        otro = User.objects.create_user(username="otro_profe3", password="x")
        curso_ajeno = Curso.objects.create(
            titulo="Ajeno", materia=materia,
            idioma="ES", nivel="A1", profesor=otro,
        )
        Leccion.objects.create(
            curso=curso_ajeno, titulo="Leccion ajena",
            pais_origen="X", explicacion="X", ejemplo_uso="X",
        )
        resp = profesor_client.get("/api/v1/profesor/lecciones/")
        titulos = [l["titulo"] for l in resp.data.get("results", [])]
        assert "Leccion ajena" not in titulos
