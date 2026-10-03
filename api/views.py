# -*- coding: utf-8 -*-
"""Views de la API."""
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, inline_serializer,
)
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, AllowAny

from courses.models import (
    Materia, Curso, Leccion, ProgresoEstudiante, Inscripcion,
    Certificado, Tarea, Entrega, Evaluacion, PreguntaEvaluacion,
    OpcionRespuesta, IntentoEvaluacion, RespuestaIntento,
    RecursoInteractivo,
)
from users.models import Perfil, Logro, LogroUsuario, Notificacion
from users.notifications import crear_notificacion

from .serializers import (
    LoginSerializer,
    UserBasicSerializer, PerfilSerializer, RegisterSerializer,
    MateriaSerializer, CursoListSerializer, CursoDetailSerializer,
    LeccionSerializer, InscripcionSerializer, CertificadoSerializer,
    NotificacionSerializer, LogroSerializer, LogroUsuarioSerializer,
    RecursoSerializer, EvaluacionPublicaSerializer, IntentoSerializer,
    RendirEvaluacionSerializer, TareaSerializer, EntregaSerializer,
    RankingItemSerializer,
)
from .permissions import IsProfesor, IsProfesorDelCurso
from .pagination import StandardPagination


# ==================== AUTH ====================
@extend_schema(
    request=LoginSerializer,
    responses={200: OpenApiResponse(description="Token + usuario + perfil")},
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    """Login: recibe username + password, devuelve token."""
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    if not username or not password:
        return Response({"error": "Falta username o password."},
                        status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "Credenciales invalidas."},
                        status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({"error": "Usuario inactivo."},
                        status=status.HTTP_403_FORBIDDEN)
    token, _ = Token.objects.get_or_create(user=user)
    perfil, _ = Perfil.objects.get_or_create(usuario=user)
    return Response({
        "token": token.key,
        "usuario": UserBasicSerializer(user).data,
        "perfil": PerfilSerializer(perfil).data,
    })


@extend_schema(
    request=None,
    responses={200: OpenApiResponse(description="Sesion cerrada")},
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """Cierra sesion: elimina el token."""
    Token.objects.filter(user=request.user).delete()
    return Response({"ok": True, "mensaje": "Sesion cerrada."})


@extend_schema(
    request=RegisterSerializer,
    responses={201: OpenApiResponse(description="Usuario creado + token")},
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """Registro de nuevo usuario."""
    s = RegisterSerializer(data=request.data)
    if s.is_valid():
        user = s.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "token": token.key,
            "usuario": UserBasicSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=PerfilSerializer,
    responses={200: OpenApiResponse(description="Usuario + perfil")},
    tags=["Auth"],
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def api_me(request):
    """Perfil del usuario autenticado. PATCH para actualizar."""
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    if request.method == "PATCH":
        s = PerfilSerializer(perfil, data=request.data, partial=True)
        if s.is_valid():
            s.save()
        else:
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        "usuario": UserBasicSerializer(request.user).data,
        "perfil": PerfilSerializer(perfil).data,
    })


# ==================== CATALOGO ====================
class MateriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    permission_classes = [AllowAny]


class CursoViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogo publico de cursos."""
    queryset = Curso.objects.select_related("materia", "profesor").all()
    permission_classes = [AllowAny]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CursoDetailSerializer
        return CursoListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        idioma = self.request.query_params.get("idioma")
        nivel = self.request.query_params.get("nivel")
        materia = self.request.query_params.get("materia")
        q = self.request.query_params.get("q")
        if idioma:
            qs = qs.filter(idioma=idioma)
        if nivel:
            qs = qs.filter(nivel=nivel)
        if materia:
            qs = qs.filter(materia_id=materia)
        if q:
            qs = qs.filter(titulo__icontains=q)
        return qs.annotate(
            total_lecciones=Count("lecciones", distinct=True),
            total_inscritos=Count("inscritos", distinct=True),
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def inscribirse(self, request, pk=None):
        curso = self.get_object()
        insc, created = Inscripcion.objects.get_or_create(
            estudiante=request.user, curso=curso,
            defaults={"activa": True}
        )
        if created:
            return Response({"ok": True, "creado": True})
        return Response({"ok": True, "creado": False, "mensaje": "Ya estabas inscrito."})


class MiCursoViewSet(viewsets.ReadOnlyModelViewSet):
    """Mis cursos (inscripciones)."""
    serializer_class = InscripcionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Inscripcion.objects.filter(
            estudiante=self.request.user, activa=True
        ).select_related("curso", "curso__materia").order_by("-fecha_inscripcion")


# ==================== LECCIONES ====================
class LeccionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LeccionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        curso_id = self.request.query_params.get("curso")
        qs = Leccion.objects.select_related("curso").all().order_by("curso", "orden")
        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        return qs

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        leccion = self.get_object()
        progreso, _ = ProgresoEstudiante.objects.get_or_create(
            estudiante=request.user, leccion=leccion,
            defaults={"completada": True}
        )
        if not progreso.completada:
            progreso.completada = True
            progreso.save()

        # Verificar certificado
        curso = leccion.curso
        total = curso.lecciones.count()
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=request.user, leccion__curso=curso, completada=True
        ).count()
        curso_completado = (total > 0 and completadas >= total)

        if curso_completado:
            from courses.models import emitir_certificado
            cert, creado = emitir_certificado(request.user, curso)
            if creado:
                crear_notificacion(
                    request.user, "curso_completado",
                    "Completaste {}".format(curso.titulo),
                    "Has completado el 100% del curso.",
                    "/es/cuenta/mi-panel/certificados/"
                )
                # Notificar al profesor
                try:
                    crear_notificacion(
                        curso.profesor, "curso_completado",
                        "{} completo {}".format(request.user.username, curso.titulo),
                        "El estudiante ha completado el 100% del curso.",
                        "/es/cuenta/panel/certificados/"
                    )
                except Exception:
                    pass

        return Response({
            "ok": True,
            "completada": True,
            "curso_completado": curso_completado,
        })


# ==================== CERTIFICADOS ====================
class CertificadoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CertificadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Certificado.objects.filter(
            estudiante=self.request.user
        ).select_related("curso").order_by("-fecha_emision")


# ==================== NOTIFICACIONES ====================
class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    http_method_names = ["get", "post", "delete", "head"]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)

    @action(detail=False, methods=["get"])
    def sin_leer(self, request):
        qs = self.get_queryset().filter(leida=False)
        return Response({"count": qs.count(), "resultados": self.get_serializer(qs, many=True).data})

    @action(detail=True, methods=["post"])
    def leer(self, request, pk=None):
        n = self.get_object()
        n.leida = True
        n.save(update_fields=["leida"])
        return Response({"ok": True})

    @action(detail=False, methods=["post"])
    def marcar_todas(self, request):
        self.get_queryset().filter(leida=False).update(leida=True)
        return Response({"ok": True})


# ==================== LOGROS ====================
class LogroViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Logro.objects.filter(activo=True)
    serializer_class = LogroSerializer
    permission_classes = [AllowAny]


class MiLogroViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogroUsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LogroUsuario.objects.filter(
            usuario=self.request.user
        ).select_related("logro")


# ==================== RECURSOS ====================
class RecursoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RecursoInteractivo.objects.filter(activo=True).order_by("tipo", "orden", "titulo")
    serializer_class = RecursoSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardPagination
    lookup_field = "slug"

    def get_queryset(self):
        qs = super().get_queryset()
        tipo = self.request.query_params.get("tipo")
        q = self.request.query_params.get("q")
        if tipo:
            qs = qs.filter(tipo=tipo)
        if q:
            qs = qs.filter(Q(titulo__icontains=q) | Q(descripcion__icontains=q))
        return qs


# ==================== EVALUACIONES ====================
class EvaluacionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EvaluacionPublicaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        curso_id = self.request.query_params.get("curso")
        qs = Evaluacion.objects.filter(estado="publicada").prefetch_related("preguntas__opciones")
        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        return qs

    @action(detail=True, methods=["post"])
    def rendir(self, request, pk=None):
        evaluacion = self.get_object()
        s = RendirEvaluacionSerializer(data=request.data)
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)
        respuestas = s.validated_data["respuestas"]

        # Intentos previos
        intentos_hechos = IntentoEvaluacion.objects.filter(
            evaluacion=evaluacion, estudiante=request.user, completado=True
        ).count()
        if intentos_hechos >= evaluacion.intentos_maximos:
            return Response({"error": "Sin intentos restantes."},
                            status=status.HTTP_400_BAD_REQUEST)

        intento = IntentoEvaluacion.objects.create(
            evaluacion=evaluacion, estudiante=request.user
        )

        puntaje_total = 0
        for pregunta in evaluacion.preguntas.all():
            val = respuestas.get(str(pregunta.id), "").strip()
            if not val:
                continue
            # Tipo: unica
            try:
                if pregunta.tipo in ("unica", "multiple"):
                    opcion = OpcionRespuesta.objects.get(id=int(val), pregunta=pregunta)
                    if opcion.es_correcta:
                        puntaje_total += pregunta.puntaje
                elif pregunta.tipo == "vf":
                    # val = id de opcion elegida
                    opcion = OpcionRespuesta.objects.get(id=int(val), pregunta=pregunta)
                    if opcion.es_correcta:
                        puntaje_total += pregunta.puntaje
                elif pregunta.tipo == "corta":
                    def norm(t):
                        import unicodedata
                        t = (t or "").lower().strip()
                        t = unicodedata.normalize("NFKD", t)
                        return "".join(c for c in t if not unicodedata.combining(c))
                    validas = [norm(x) for x in (pregunta.respuesta_corta or "").split("|")]
                    if norm(val) in validas:
                        puntaje_total += pregunta.puntaje
            except Exception:
                pass

        intento.puntaje = puntaje_total
        intento.aprobado = puntaje_total >= evaluacion.puntaje_aprobacion
        intento.completado = True
        intento.fecha_fin = timezone.now()
        intento.save()

        crear_notificacion(
            request.user, "evaluacion",
            "Resultado: {}".format(evaluacion.titulo),
            "Obtuviste {}/{}".format(puntaje_total, evaluacion.puntaje_maximo),
            "/es/evaluacion/resultado/{}/".format(intento.id)
        )

        return Response({
            "intento_id": intento.id,
            "puntaje": puntaje_total,
            "puntaje_maximo": evaluacion.puntaje_maximo,
            "aprobado": intento.aprobado,
        })


class IntentoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IntentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IntentoEvaluacion.objects.filter(
            estudiante=self.request.user
        ).select_related("evaluacion").order_by("-fecha_inicio")


# ==================== TAREAS ====================
class TareaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TareaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        curso_id = self.request.query_params.get("curso")
        qs = Tarea.objects.filter(estado="publicada").select_related("curso")
        if curso_id:
            qs = qs.filter(curso_id=curso_id)
        return qs


# ==================== RANKING ====================
@extend_schema(
    responses={200: OpenApiResponse(description="Ranking del curso")},
    tags=["Ranking"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_ranking_curso(request, curso_id):
    """Ranking de un curso."""
    from users.ranking_utils import calcular_ranking
    curso = get_object_or_404(Curso, id=curso_id)
    ranking = calcular_ranking(curso, request.user)
    data = []
    for r in ranking:
        data.append({
            "posicion": r["posicion"],
            "usuario": UserBasicSerializer(r["estudiante"]).data,
            "completadas": r["completadas"],
            "total": r["total"],
            "pct": r["pct"],
            "promedio_eval": r["promedio_eval"],
            "promedio_entregas": r["promedio_entregas"],
            "es_yo": r["es_yo"],
        })
    return Response({
        "curso": {"id": curso.id, "titulo": curso.titulo},
        "total": len(data),
        "ranking": data,
    })


# ==================== PROFESOR ====================
class ProfesorCursoViewSet(viewsets.ModelViewSet):
    """CRUD de cursos para el profesor."""
    serializer_class = CursoListSerializer
    permission_classes = [IsProfesor]
    pagination_class = StandardPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Curso.objects.all()
        return Curso.objects.filter(profesor=self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            serializer.save(profesor=self.request.user)
        else:
            serializer.save()


class ProfesorLeccionViewSet(viewsets.ModelViewSet):
    serializer_class = LeccionSerializer
    permission_classes = [IsProfesor]

    def get_queryset(self):
        cursos_ids = Curso.objects.filter(profesor=self.request.user).values_list("id", flat=True)
        if self.request.user.is_superuser:
            return Leccion.objects.all()
        return Leccion.objects.filter(curso_id__in=cursos_ids)


class ProfesorEvaluacionViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluacionPublicaSerializer
    permission_classes = [IsProfesor]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Evaluacion.objects.all()
        return Evaluacion.objects.filter(curso__profesor=self.request.user)


class ProfesorTareaViewSet(viewsets.ModelViewSet):
    serializer_class = TareaSerializer
    permission_classes = [IsProfesor]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Tarea.objects.all()
        return Tarea.objects.filter(curso__profesor=self.request.user)


class ProfesorEntregaViewSet(viewsets.ModelViewSet):
    serializer_class = EntregaSerializer
    permission_classes = [IsProfesor]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Entrega.objects.all()
        return Entrega.objects.filter(tarea__curso__profesor=self.request.user)

    @action(detail=True, methods=["post"])
    def calificar(self, request, pk=None):
        e = self.get_object()
        calificacion = request.data.get("calificacion")
        retro = request.data.get("retroalimentacion", "")
        if calificacion is None:
            return Response({"error": "Falta calificacion."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            e.calificacion = int(calificacion)
        except ValueError:
            return Response({"error": "calificacion debe ser numero."},
                            status=status.HTTP_400_BAD_REQUEST)
        e.retroalimentacion = retro
        e.estado = "calificada"
        e.fecha_calificacion = timezone.now()
        e.save()
        crear_notificacion(
            e.estudiante, "entrega",
            "Tarea calificada: {}".format(e.tarea.titulo),
            "Nota: {}/{}".format(e.calificacion, e.tarea.puntaje_maximo),
            ""
        )
        return Response({"ok": True, "calificacion": e.calificacion})
