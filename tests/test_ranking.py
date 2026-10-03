# -*- coding: utf-8 -*-
"""Tests de ranking por curso."""
import pytest
from courses.models import Inscripcion, ProgresoEstudiante
from users.ranking_utils import calcular_ranking


@pytest.mark.django_db
class TestCalcularRanking:
    def test_ranking_vacio(self, curso_con_lecciones):
        ranking = calcular_ranking(curso_con_lecciones)
        assert ranking == []

    def test_un_solo_estudiante(self, curso_con_lecciones, alumno_user):
        Inscripcion.objects.create(
            estudiante=alumno_user, curso=curso_con_lecciones, activa=True
        )
        ranking = calcular_ranking(curso_con_lecciones)
        assert len(ranking) == 1
        assert ranking[0]["estudiante"] == alumno_user
        assert ranking[0]["pct"] == 0

    def test_ordena_por_pct(self, curso_con_lecciones, alumno_user, otro_alumno):
        # Inscribir a los dos
        Inscripcion.objects.create(
            estudiante=alumno_user, curso=curso_con_lecciones, activa=True
        )
        Inscripcion.objects.create(
            estudiante=otro_alumno, curso=curso_con_lecciones, activa=True
        )

        # alumno_user completa 2 de 3
        lecciones = list(curso_con_lecciones.lecciones.all())
        for l in lecciones[:2]:
            ProgresoEstudiante.objects.create(
                estudiante=alumno_user, leccion=l, completada=True
            )

        # otro_alumno completa 3 de 3
        for l in lecciones:
            ProgresoEstudiante.objects.create(
                estudiante=otro_alumno, leccion=l, completada=True
            )

        ranking = calcular_ranking(curso_con_lecciones)
        assert ranking[0]["estudiante"] == otro_alumno  # 100% primero
        assert ranking[0]["pct"] == 100
        assert ranking[1]["estudiante"] == alumno_user
        assert ranking[1]["pct"] == 66


@pytest.mark.django_db
class TestRankingApi:
    def test_ranking_endpoint(self, alumno_client, curso_con_lecciones, alumno_user):
        Inscripcion.objects.create(
            estudiante=alumno_user, curso=curso_con_lecciones, activa=True
        )
        resp = alumno_client.get(
            "/api/v1/ranking/curso/{}/".format(curso_con_lecciones.id)
        )
        assert resp.status_code == 200
        assert "ranking" in resp.data
        assert resp.data["total"] == 1

    def test_ranking_yo_marcado(self, alumno_client, curso_con_lecciones, alumno_user):
        Inscripcion.objects.create(
            estudiante=alumno_user, curso=curso_con_lecciones, activa=True
        )
        resp = alumno_client.get(
            "/api/v1/ranking/curso/{}/".format(curso_con_lecciones.id)
        )
        assert resp.data["ranking"][0]["es_yo"] is True
