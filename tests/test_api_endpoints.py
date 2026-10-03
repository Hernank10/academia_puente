# -*- coding: utf-8 -*-
"""Tests de endpoints API para alumno."""
import pytest


@pytest.mark.django_db
class TestApiCursos:
    def test_lista_publica(self, api_client, curso):
        resp = api_client.get("/api/v1/cursos/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_detalle_curso(self, api_client, curso_con_lecciones):
        resp = api_client.get("/api/v1/cursos/{}/".format(curso_con_lecciones.id))
        assert resp.status_code == 200
        assert "lecciones" in resp.data
        assert len(resp.data["lecciones"]) == 3

    def test_filtro_por_idioma(self, api_client, curso):
        resp = api_client.get("/api/v1/cursos/?idioma=ES")
        assert resp.status_code == 200

    def test_inscribirse(self, alumno_client, curso_con_lecciones):
        resp = alumno_client.post(
            "/api/v1/cursos/{}/inscribirse/".format(curso_con_lecciones.id)
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True


@pytest.mark.django_db
class TestApiMisCursos:
    def test_vacio_sin_inscripciones(self, alumno_client):
        resp = alumno_client.get("/api/v1/mis-cursos/")
        assert resp.status_code == 200

    def test_con_inscripcion(self, alumno_client, inscripcion):
        resp = alumno_client.get("/api/v1/mis-cursos/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1


@pytest.mark.django_db
class TestApiLecciones:
    def test_listar_por_curso(self, alumno_client, curso_con_lecciones):
        resp = alumno_client.get(
            "/api/v1/lecciones/?curso={}".format(curso_con_lecciones.id)
        )
        assert resp.status_code == 200
        assert resp.data["count"] == 3

    def test_completar_leccion(self, alumno_client, curso_con_lecciones, alumno_user):
        leccion = curso_con_lecciones.lecciones.first()
        resp = alumno_client.post(
            "/api/v1/lecciones/{}/completar/".format(leccion.id)
        )
        assert resp.status_code == 200
        assert resp.data["completada"] is True

        # Verifica que se creo el ProgresoEstudiante
        from courses.models import ProgresoEstudiante
        assert ProgresoEstudiante.objects.filter(
            estudiante=alumno_user, leccion=leccion, completada=True
        ).exists()


@pytest.mark.django_db
class TestApiRecursos:
    def test_lista_publica(self, api_client, recurso):
        resp = api_client.get("/api/v1/recursos/")
        assert resp.status_code == 200

    def test_filtro_tipo(self, api_client, recurso):
        resp = api_client.get("/api/v1/recursos/?tipo=tecnica")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestApiNotificaciones:
    def test_vacio(self, alumno_client):
        resp = alumno_client.get("/api/v1/notificaciones/")
        assert resp.status_code == 200

    def test_con_notificacion(self, alumno_client, alumno_user):
        from users.models import Notificacion
        Notificacion.objects.create(
            usuario=alumno_user, tipo="sistema", titulo="Test"
        )
        resp = alumno_client.get("/api/v1/notificaciones/")
        assert resp.data["count"] == 1

    def test_marcar_leida(self, alumno_client, alumno_user):
        from users.models import Notificacion
        n = Notificacion.objects.create(
            usuario=alumno_user, tipo="sistema", titulo="Test"
        )
        resp = alumno_client.post(
            "/api/v1/notificaciones/{}/leer/".format(n.id)
        )
        assert resp.status_code == 200
        n.refresh_from_db()
        assert n.leida is True


@pytest.mark.django_db
class TestApiLogros:
    def test_lista_logros(self, api_client, logro):
        resp = api_client.get("/api/v1/logros/")
        assert resp.status_code == 200
