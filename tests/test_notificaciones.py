# -*- coding: utf-8 -*-
"""Tests de notificaciones."""
import pytest
from users.models import Notificacion
from users.notifications import crear_notificacion


@pytest.mark.django_db
class TestCrearNotificacion:
    def test_crea_notificacion(self, alumno_user):
        n = crear_notificacion(
            alumno_user, "sistema", "Titulo", "Mensaje", "/url/"
        )
        assert n is not None
        assert n.usuario == alumno_user
        assert n.titulo == "Titulo"

    def test_usuario_none_no_crea(self):
        n = crear_notificacion(None, "sistema", "Titulo")
        assert n is None


@pytest.mark.django_db
class TestNotificacionAlCompletarCurso:
    def test_notifica_al_completar_100(self, alumno_client, alumno_user, curso_con_lecciones):
        """Al completar todas las lecciones, se notifica."""
        curso = curso_con_lecciones
        for leccion in curso.lecciones.all():
            alumno_client.post("/api/v1/lecciones/{}/completar/".format(leccion.id))

        # Debe existir notificacion de curso completado
        assert Notificacion.objects.filter(
            usuario=alumno_user, tipo="curso_completado"
        ).exists()

    def test_notifica_al_profesor(self, alumno_client, profesor_user, curso_con_lecciones):
        """Al completar 100%, tambien se notifica al profesor."""
        curso = curso_con_lecciones
        for leccion in curso.lecciones.all():
            alumno_client.post("/api/v1/lecciones/{}/completar/".format(leccion.id))

        assert Notificacion.objects.filter(
            usuario=profesor_user, tipo="curso_completado"
        ).exists()


@pytest.mark.django_db
class TestNotificacionAlCalificar:
    def test_notifica_al_calificar_entrega(self, profesor_client, entrega, alumno_user):
        profesor_client.post(
            "/api/v1/profesor/entregas/{}/calificar/".format(entrega.id),
            {"calificacion": 90}, format="json",
        )
        # Debe notificar al alumno
        assert Notificacion.objects.filter(
            usuario=alumno_user, tipo="entrega"
        ).exists()
