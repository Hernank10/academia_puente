# -*- coding: utf-8 -*-
"""Tests de modelos."""
import pytest
from django.contrib.auth.models import User

from users.models import Perfil, Notificacion
from courses.models import Curso, Leccion, ProgresoEstudiante, Certificado


# ==================== PERFIL ====================
@pytest.mark.django_db
class TestPerfil:
    def test_crear_perfil(self, alumno_user):
        perfil = alumno_user.perfil
        assert perfil.rol_principal == "estudiante"
        assert perfil.puntos == 0

    def test_rango_inicial(self, alumno_user):
        perfil = alumno_user.perfil
        assert perfil.rango_academico == "Aprendiz de Idiomas"

    def test_rango_intermedio(self, alumno_user):
        perfil = alumno_user.perfil
        perfil.puntos = 250
        assert perfil.rango_academico == "Intérprete Cultural"

    def test_rango_avanzado(self, alumno_user):
        perfil = alumno_user.perfil
        perfil.puntos = 1000
        assert perfil.rango_academico == "Sabio Licenciado"


# ==================== CURSO ====================
@pytest.mark.django_db
class TestCurso:
    def test_crear_curso(self, curso, profesor_user):
        assert curso.profesor == profesor_user
        assert curso.idioma == "ES"
        assert curso.nivel == "A1"

    def test_str_curso(self, curso):
        assert curso.titulo in str(curso)

    def test_lecciones_por_orden(self, curso_con_lecciones):
        lecciones = list(curso_con_lecciones.lecciones.all())
        assert len(lecciones) == 3
        assert lecciones[0].orden == 1
        assert lecciones[2].orden == 3


# ==================== PROGRESO ====================
@pytest.mark.django_db
class TestProgresoEstudiante:
    def test_marcar_completada_da_puntos(self, alumno_user, curso_con_lecciones):
        leccion = curso_con_lecciones.lecciones.first()
        puntos_antes = alumno_user.perfil.puntos
        ProgresoEstudiante.objects.create(
            estudiante=alumno_user, leccion=leccion, completada=True
        )
        alumno_user.perfil.refresh_from_db()
        assert alumno_user.perfil.puntos == puntos_antes + 5

    def test_inscripcion_progreso_pct(self, inscripcion, alumno_user):
        curso = inscripcion.curso
        lecciones = list(curso.lecciones.all())
        # Completar 1 de 3
        ProgresoEstudiante.objects.create(
            estudiante=alumno_user, leccion=lecciones[0], completada=True
        )
        assert inscripcion.progreso_pct == 33  # 1/3 * 100 redondeado


# ==================== CERTIFICADO ====================
@pytest.mark.django_db
class TestCertificado:
    def test_codigo_unico_generado(self, alumno_user, curso):
        cert = Certificado.objects.create(
            estudiante=alumno_user, curso=curso,
            puntos_obtenidos=100, calificacion="Aprobado",
        )
        assert cert.codigo.startswith("PD-")
        assert len(cert.codigo) > 10

    def test_url_publica(self, alumno_user, curso):
        cert = Certificado.objects.create(
            estudiante=alumno_user, curso=curso,
            puntos_obtenidos=100,
        )
        assert cert.codigo in cert.url_publica


# ==================== NOTIFICACIONES ====================
@pytest.mark.django_db
class TestNotificacion:
    def test_crear_notificacion(self, alumno_user):
        n = Notificacion.objects.create(
            usuario=alumno_user, tipo="sistema",
            titulo="Test", mensaje="Mensaje"
        )
        assert n.leida is False
        assert n.usuario == alumno_user

    def test_icono_por_tipo(self, alumno_user):
        n = Notificacion.objects.create(
            usuario=alumno_user, tipo="curso_completado",
            titulo="Test"
        )
        assert n.icono == "\U0001F389"  # 🎉
