# -*- coding: utf-8 -*-
"""Tests de vistas web."""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from courses.models import Curso


# ==================== HOME ====================
@pytest.mark.django_db
class TestHome:
    def test_home_carga(self, client):
        resp = client.get("/es/")
        assert resp.status_code == 200


# ==================== DASHBOARD ALUMNO ====================
@pytest.mark.django_db
class TestDashboardAlumno:
    def test_requiere_login(self, client):
        resp = client.get("/es/cuenta/dashboard/")
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_carga_con_login(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/dashboard/")
        assert resp.status_code == 200

    def test_mi_panel_carga(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/mi-panel/")
        assert resp.status_code == 200

    def test_mi_panel_cursos(self, client, alumno_user, inscripcion):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/mi-panel/cursos/")
        assert resp.status_code == 200

    def test_mi_panel_certificados(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/mi-panel/certificados/")
        assert resp.status_code == 200

    def test_mi_panel_logros(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/mi-panel/logros/")
        assert resp.status_code == 200


# ==================== DASHBOARD PROFESOR ====================
@pytest.mark.django_db
class TestDashboardProfesor:
    def test_requiere_login(self, client):
        resp = client.get("/es/cuenta/dashboard-profesor/")
        assert resp.status_code == 302

    def test_alumno_no_accede(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/dashboard-profesor/")
        # Redirige o 403
        assert resp.status_code in (302, 403)

    def test_profesor_accede(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/dashboard-profesor/")
        assert resp.status_code == 200

    def test_panel_home(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/")
        assert resp.status_code == 200

    def test_panel_cursos(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/cursos/")
        assert resp.status_code == 200

    def test_panel_estudiantes(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/estudiantes/")
        assert resp.status_code == 200

    def test_panel_evaluaciones(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/evaluaciones/")
        assert resp.status_code == 200

    def test_panel_entregas(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/entregas/")
        assert resp.status_code == 200

    def test_panel_certificados(self, client, profesor_user):
        client.force_login(profesor_user)
        resp = client.get("/es/cuenta/panel/certificados/")
        assert resp.status_code == 200


# ==================== CURSO DEL PROFESOR ====================
@pytest.mark.django_db
class TestCursoProfesor:
    def test_profesor_ve_su_curso(self, client, profesor_user, curso):
        client.force_login(profesor_user)
        url = "/es/cuenta/profesor/curso/{}/".format(curso.id)
        resp = client.get(url)
        assert resp.status_code == 200

    def test_profesor_no_ve_curso_ajeno(self, client, profesor_user, alumno_user, materia):
        # Curso de otro profesor
        otro = User.objects.create_user(username="otro_profe", password="x")
        curso_ajeno = Curso.objects.create(
            titulo="Ajeno", materia=materia, idioma="ES", nivel="A1", profesor=otro
        )
        client.force_login(profesor_user)
        url = "/es/cuenta/profesor/curso/{}/".format(curso_ajeno.id)
        resp = client.get(url)
        # Debe redirigir
        assert resp.status_code == 302


# ==================== NOTIFICACIONES ====================
@pytest.mark.django_db
class TestNotificaciones:
    def test_lista_vacia(self, client, alumno_user):
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/notificaciones/")
        assert resp.status_code == 200

    def test_lista_con_notificaciones(self, client, alumno_user):
        from users.models import Notificacion
        Notificacion.objects.create(
            usuario=alumno_user, tipo="sistema", titulo="Test"
        )
        client.force_login(alumno_user)
        resp = client.get("/es/cuenta/notificaciones/")
        assert resp.status_code == 200
        assert "Test" in resp.content.decode()


