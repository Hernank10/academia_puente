# -*- coding: utf-8 -*-
"""Tests de autenticacion API."""
import pytest
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


@pytest.mark.django_db
class TestApiLogin:
    def test_login_ok(self, api_client, alumno_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "test_alumno",
            "password": "Test1234!",
        }, format="json")
        assert resp.status_code == 200
        assert "token" in resp.data
        assert resp.data["usuario"]["username"] == "test_alumno"
        assert "perfil" in resp.data

    def test_login_password_incorrecto(self, api_client, alumno_user):
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "test_alumno",
            "password": "WrongPassword",
        }, format="json")
        assert resp.status_code == 401

    def test_login_sin_datos(self, api_client):
        resp = api_client.post("/api/v1/auth/login/", {}, format="json")
        assert resp.status_code == 400
        assert "error" in resp.data


@pytest.mark.django_db
class TestApiRegister:
    def test_register_ok(self, api_client):
        resp = api_client.post("/api/v1/auth/register/", {
            "username": "nuevo_user",
            "email": "nuevo@test.com",
            "password": "Test1234!",
            "password2": "Test1234!",
            "first_name": "Nuevo",
            "last_name": "User",
        }, format="json")
        assert resp.status_code == 201
        assert "token" in resp.data
        assert User.objects.filter(username="nuevo_user").exists()

    def test_register_password_no_coincide(self, api_client):
        resp = api_client.post("/api/v1/auth/register/", {
            "username": "nuevo2",
            "password": "Test1234!",
            "password2": "Otro",
        }, format="json")
        assert resp.status_code == 400

    def test_register_username_duplicado(self, api_client, alumno_user):
        resp = api_client.post("/api/v1/auth/register/", {
            "username": "test_alumno",
            "password": "Test1234!",
            "password2": "Test1234!",
        }, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestApiMe:
    def test_me_requiere_token(self, api_client):
        resp = api_client.get("/api/v1/me/")
        assert resp.status_code == 401

    def test_me_con_token(self, alumno_client, alumno_user):
        resp = alumno_client.get("/api/v1/me/")
        assert resp.status_code == 200
        assert resp.data["usuario"]["username"] == "test_alumno"

    def test_patch_me(self, alumno_client):
        resp = alumno_client.patch("/api/v1/me/", {
            "biografia": "Mi biografia de prueba"
        }, format="json")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestApiLogout:
    def test_logout_elimina_token(self, alumno_client, alumno_user):
        assert Token.objects.filter(user=alumno_user).exists()
        resp = alumno_client.post("/api/v1/auth/logout/")
        assert resp.status_code == 200
        assert not Token.objects.filter(user=alumno_user).exists()
