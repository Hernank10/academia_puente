# -*- coding: utf-8 -*-
"""Tests del motor de evaluaciones."""
import pytest
from courses.models import OpcionRespuesta, PreguntaEvaluacion, IntentoEvaluacion


@pytest.mark.django_db
class TestMotorCalificacion:
    def test_evaluacion_unica_correcta(self, alumno_client, evaluacion_con_preguntas):
        p = evaluacion_con_preguntas.preguntas.filter(tipo="unica").first()
        opcion_correcta = p.opciones.filter(es_correcta=True).first()

        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {str(p.id): str(opcion_correcta.id)}},
            format="json",
        )
        assert resp.status_code == 200
        # Solo se respondio 1 de 4, debe tener 10 puntos
        assert resp.data["puntaje"] == 10

    def test_evaluacion_unica_incorrecta(self, alumno_client, evaluacion_con_preguntas):
        p = evaluacion_con_preguntas.preguntas.filter(tipo="unica").first()
        opcion_incorrecta = p.opciones.filter(es_correcta=False).first()

        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {str(p.id): str(opcion_incorrecta.id)}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["puntaje"] == 0

    def test_evaluacion_corta_con_variantes(self, alumno_client, evaluacion_con_preguntas):
        p = evaluacion_con_preguntas.preguntas.filter(tipo="corta").first()

        # Probar "haber"
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {str(p.id): "haber"}},
            format="json",
        )
        assert resp.data["puntaje"] == 5

    def test_evaluacion_corta_insensible_tildes(self, alumno_client, evaluacion_con_preguntas):
        p = evaluacion_con_preguntas.preguntas.filter(tipo="corta").first()

        # "HABER" en mayusculas debe pasar
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {str(p.id): "HABER"}},
            format="json",
        )
        assert resp.data["puntaje"] == 5

    def test_evaluacion_vf(self, alumno_client, evaluacion_con_preguntas):
        p = evaluacion_con_preguntas.preguntas.filter(tipo="vf").first()
        opcion_v = p.opciones.filter(es_correcta=True).first()

        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {str(p.id): str(opcion_v.id)}},
            format="json",
        )
        assert resp.data["puntaje"] == 5

    def test_evaluacion_completa_todas_correctas(self, alumno_client, evaluacion_con_preguntas):
        respuestas = {}
        for p in evaluacion_con_preguntas.preguntas.all():
            if p.tipo in ("unica", "vf"):
                op = p.opciones.filter(es_correcta=True).first()
                respuestas[str(p.id)] = str(op.id)
            elif p.tipo == "corta":
                respuestas[str(p.id)] = "haber"
            elif p.tipo == "multiple":
                op = p.opciones.filter(es_correcta=True).first()
                respuestas[str(p.id)] = str(op.id)

        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": respuestas},
            format="json",
        )
        assert resp.status_code == 200
        # 30 puntos maximos con todas correctas
        assert resp.data["puntaje"] == 30
        assert resp.data["aprobado"] is True

    def test_crea_intento(self, alumno_client, alumno_user, evaluacion_con_preguntas):
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {}},
            format="json",
        )
        assert resp.status_code == 200
        assert IntentoEvaluacion.objects.filter(
            evaluacion=evaluacion_con_preguntas,
            estudiante=alumno_user,
        ).exists()

    def test_sin_intentos_restantes(self, alumno_client, evaluacion_con_preguntas, alumno_user):
        # Crear 3 intentos previos
        for _ in range(3):
            IntentoEvaluacion.objects.create(
                evaluacion=evaluacion_con_preguntas,
                estudiante=alumno_user, completado=True,
            )
        # Cuarto intento debe fallar
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
            {"respuestas": {}}, format="json",
        )
        assert resp.status_code == 400
