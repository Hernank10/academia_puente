# -*- coding: utf-8 -*-
"""Tests del middleware CORS y headers de seguridad."""
import pytest


@pytest.mark.django_db
class TestCorsMiddleware:
    def test_cors_en_api(self, api_client):
        resp = api_client.get("/api/v1/cursos/")
        assert resp.get("Access-Control-Allow-Origin") == "*"

    def test_cors_methods(self, api_client):
        resp = api_client.get("/api/v1/cursos/")
        methods = resp.get("Access-Control-Allow-Methods", "")
        assert "POST" in methods
        assert "GET" in methods

    def test_cors_headers(self, api_client):
        resp = api_client.get("/api/v1/cursos/")
        headers = resp.get("Access-Control-Allow-Headers", "")
        assert "Authorization" in headers
        assert "Content-Type" in headers

    def test_cors_no_en_web(self, client):
        resp = client.get("/es/")
        assert "Access-Control-Allow-Origin" not in resp


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_xframe_sameorigin(self, client):
        resp = client.get("/es/")
        assert resp.get("X-Frame-Options") == "SAMEORIGIN"

    def test_content_type_nosniff(self, client):
        resp = client.get("/es/")
        assert resp.get("X-Content-Type-Options") == "nosniff"
