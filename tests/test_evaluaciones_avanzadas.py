# -*- coding: utf-8 -*-
"""Tests avanzados de evaluaciones."""
import pytest
from courses.models import (
    OpcionRespuesta, PreguntaEvaluacion, Evaluacion, IntentoEvaluacion,
)


@pytest.fixture
def eval_multiple(db, curso_con_lecciones):
    ev = Evaluacion.objects.create(
        curso=curso_con_lecciones, titulo="Multiple",
        estado="publicada", puntaje_maximo=10, puntaje_aprobacion=6,
    )
    p = PreguntaEvaluacion.objects.create(
        evaluacion=ev, texto="Selecciona", puntaje=10, tipo="multiple", orden=1,
    )
    OpcionRespuesta.objects.create(pregunta=p, texto="A", es_correcta=True, orden=1)
    OpcionRespuesta.objects.create(pregunta=p, texto="B", es_correcta=True, orden=2)
    OpcionRespuesta.objects.create(pregunta=p, texto="C", es_correcta=False, orden=3)
    return ev


@pytest.mark.django_db
class TestEvaluacionMultiple:
    def test_correcta(self, alumno_client, eval_multiple):
        p = eval_multiple.preguntas.first()
        correcta = p.opciones.filter(es_correcta=True).first()
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(eval_multiple.id),
            {"respuestas": {str(p.id): str(correcta.id)}},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["puntaje"] == 10

    def test_incorrecta(self, alumno_client, eval_multiple):
        p = eval_multiple.preguntas.first()
        incorrecta = p.opciones.filter(es_correcta=False).first()
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(eval_multiple.id),
            {"respuestas": {str(p.id): str(incorrecta.id)}},
            format="json",
        )
        assert resp.data["puntaje"] == 0

    def test_sin_respuesta(self, alumno_client, eval_multiple):
        resp = alumno_client.post(
            "/api/v1/evaluaciones/{}/rendir/".format(eval_multiple.id),
            {"respuestas": {}}, format="json",
        )
        assert resp.data["puntaje"] == 0
        assert resp.data["aprobado"] is False


@pytest.mark.django_db
class TestHistorialIntentos:
    def test_multiples_intentos(self, alumno_client, alumno_user, evaluacion_con_preguntas):
        for _ in range(2):
            alumno_client.post(
                "/api/v1/evaluaciones/{}/rendir/".format(evaluacion_con_preguntas.id),
                {"respuestas": {}}, format="json",
            )
        count = IntentoEvaluacion.objects.filter(
            estudiante=alumno_user, evaluacion=evaluacion_con_preguntas
        ).count()
        assert count == 2

    def test_lista_mis_intentos(self, alumno_client, alumno_user, evaluacion_con_preguntas):
        IntentoEvaluacion.objects.create(
            evaluacion=evaluacion_con_preguntas,
            estudiante=alumno_user,
            puntaje=25, aprobado=True, completado=True,
        )
        resp = alumno_client.get("/api/v1/mis-intentos/")
        assert resp.status_code == 200
        assert resp.data["count"] == 1
