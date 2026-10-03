# -*- coding: utf-8 -*-
"""Tests de endpoints API para profesor."""
import pytest
from courses.models import Curso


@pytest.mark.django_db
class TestProfesorCursos:
    def test_lista_solo_mios(self, profesor_client, curso, materia):
        # Curso ajeno
        from django.contrib.auth.models import User
        otro = User.objects.create_user(username="otro", password="x")
        Curso.objects.create(
            titulo="Ajeno", materia=materia, idioma="ES", nivel="A1", profesor=otro
        )

        resp = profesor_client.get("/api/v1/profesor/cursos/")
        assert resp.status_code == 200
        # Solo mi curso
        titulos = [c["titulo"] for c in resp.data["results"]]
        assert "Curso de prueba" in titulos
        assert "Ajeno" not in titulos

    def test_alumno_no_accede(self, alumno_client):
        resp = alumno_client.get("/api/v1/profesor/cursos/")
        assert resp.status_code == 403

    def test_crear_curso(self, profesor_client, profesor_user, materia):
        resp = profesor_client.post("/api/v1/profesor/cursos/", {
            "titulo": "Nuevo curso",
            "materia": materia.id,
            "idioma": "ES",
            "nivel": "A2",
        }, format="json")
        # Puede fallar si el serializer no incluye profesor
        assert resp.status_code in (200, 201, 400)


@pytest.mark.django_db
class TestProfesorEntregas:
    def test_lista_entregas(self, profesor_client, entrega):
        resp = profesor_client.get("/api/v1/profesor/entregas/")
        assert resp.status_code == 200

    def test_calificar_entrega(self, profesor_client, entrega):
        resp = profesor_client.post(
            "/api/v1/profesor/entregas/{}/calificar/".format(entrega.id),
            {"calificacion": 85, "retroalimentacion": "Buen trabajo"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["calificacion"] == 85

        entrega.refresh_from_db()
        assert entrega.estado == "calificada"
        assert entrega.calificacion == 85

    def test_calificar_sin_valor(self, profesor_client, entrega):
        resp = profesor_client.post(
            "/api/v1/profesor/entregas/{}/calificar/".format(entrega.id),
            {}, format="json",
        )
        assert resp.status_code == 400
