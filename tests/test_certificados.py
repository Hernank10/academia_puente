# -*- coding: utf-8 -*-
"""Tests de certificados."""
import pytest
from courses.models import Certificado, ProgresoEstudiante, emitir_certificado


@pytest.mark.django_db
class TestEmitirCertificado:
    def test_no_emite_si_no_completo(self, alumno_user, curso_con_lecciones):
        cert, creado = emitir_certificado(alumno_user, curso_con_lecciones)
        assert cert is None
        assert creado is False

    def test_emite_al_completar(self, alumno_user, curso_con_lecciones):
        for lec in curso_con_lecciones.lecciones.all():
            ProgresoEstudiante.objects.create(
                estudiante=alumno_user, leccion=lec, completada=True
            )
        cert, creado = emitir_certificado(alumno_user, curso_con_lecciones)
        assert cert is not None
        assert creado is True
        assert cert.codigo.startswith("PD-")

    def test_no_duplica(self, alumno_user, curso_con_lecciones):
        for lec in curso_con_lecciones.lecciones.all():
            ProgresoEstudiante.objects.create(
                estudiante=alumno_user, leccion=lec, completada=True
            )
        cert1, c1 = emitir_certificado(alumno_user, curso_con_lecciones)
        cert2, c2 = emitir_certificado(alumno_user, curso_con_lecciones)
        assert c1 is True and c2 is False
        assert cert1.id == cert2.id


@pytest.mark.django_db
class TestCertificadoApi:
    def test_lista_mis_certificados(self, alumno_client, alumno_user, curso):
        Certificado.objects.create(
            estudiante=alumno_user, curso=curso,
            puntos_obtenidos=100, calificacion="Aprobado",
        )
        resp = alumno_client.get("/api/v1/mis-certificados/")
        assert resp.status_code == 200
        assert resp.data["count"] == 1

    def test_vacio(self, alumno_client):
        resp = alumno_client.get("/api/v1/mis-certificados/")
        assert resp.data["count"] == 0


@pytest.mark.django_db
class TestCertificadoPublico:
    def test_vista_publica(self, client, alumno_user, curso):
        cert = Certificado.objects.create(
            estudiante=alumno_user, curso=curso,
            puntos_obtenidos=100,
        )
        url = "/es/cuenta/certificado-publico/{}/".format(cert.codigo)
        resp = client.get(url)
        assert resp.status_code == 200

    def test_404_si_no_existe(self, client):
        url = "/es/cuenta/certificado-publico/PD-9999-XXXXXX/"
        resp = client.get(url)
        assert resp.status_code == 404
