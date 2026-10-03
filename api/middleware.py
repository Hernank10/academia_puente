# -*- coding: utf-8 -*-
"""Middleware CORS simple (sin django-cors-headers)."""
from django.conf import settings


class ApiCorsMiddleware:
    """Anade cabeceras CORS a las respuestas de /api/."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = (
                "Authorization, Content-Type, X-Requested-With, Accept, Origin"
            )
            response["Access-Control-Max-Age"] = "86400"
            if request.method == "OPTIONS":
                response.status_code = 200
        return response
