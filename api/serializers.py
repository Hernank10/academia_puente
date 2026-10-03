# -*- coding: utf-8 -*-
"""Serializers de la API."""
from django.contrib.auth.models import User
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from courses.models import (
    Materia, Curso, Leccion, ProgresoEstudiante, Inscripcion,
    Certificado, Tarea, Entrega, Evaluacion, PreguntaEvaluacion,
    OpcionRespuesta, IntentoEvaluacion, RespuestaIntento,
    RecursoInteractivo,
)
from users.models import Perfil, Logro, LogroUsuario, Notificacion


# ==================== USERS ====================
class UserBasicSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name",
                  "nombre_completo"]

    @extend_schema_field(serializers.CharField)
    def get_nombre_completo(self, obj):
        return obj.get_full_name() or obj.username


class PerfilSerializer(serializers.ModelSerializer):
    usuario = UserBasicSerializer(read_only=True)
    rol_display = serializers.CharField(source="get_rol_principal_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_academico_display", read_only=True)
    rango = serializers.CharField(source="rango_academico", read_only=True)

    class Meta:
        model = Perfil
        fields = ["id", "usuario", "rol_principal", "rol_display",
                  "estado_academico", "estado_display", "puntos", "rango",
                  "biografia", "idioma_nativo", "variante_interes",
                  "zona_horaria", "puede_publicar_cursos"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name",
                  "password", "password2"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Las contrasenas no coinciden."})
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError({"username": "Ya existe."})
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        Perfil.objects.get_or_create(usuario=user)
        return user


# ==================== CURSOS ====================
class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ["id", "nombre"]


class CursoListSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source="materia.nombre", read_only=True)
    profesor_nombre = serializers.CharField(source="profesor.username", read_only=True)
    idioma_display = serializers.CharField(source="get_idioma_display", read_only=True)
    total_lecciones = serializers.IntegerField(read_only=True)
    total_inscritos = serializers.IntegerField(read_only=True)

    class Meta:
        model = Curso
        fields = ["id", "titulo", "materia", "materia_nombre",
                  "idioma", "idioma_display", "nivel",
                  "profesor_nombre", "total_lecciones", "total_inscritos"]


class LeccionSerializer(serializers.ModelSerializer):
    completada = serializers.SerializerMethodField()
    fecha_completado = serializers.SerializerMethodField()

    class Meta:
        model = Leccion
        fields = ["id", "curso", "titulo", "pais_origen", "explicacion",
                  "ejemplo_uso", "orden", "fecha_publicacion",
                  "completada", "fecha_completado"]

    @extend_schema_field(serializers.BooleanField)
    def get_completada(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        return ProgresoEstudiante.objects.filter(
            estudiante=user, leccion=obj, completada=True
        ).exists()

    @extend_schema_field(serializers.DateTimeField(allow_null=True))
    def get_fecha_completado(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return None
        p = ProgresoEstudiante.objects.filter(
            estudiante=user, leccion=obj, completada=True
        ).first()
        return p.fecha_completado if p else None


class CursoDetailSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source="materia.nombre", read_only=True)
    profesor_nombre = serializers.CharField(source="profesor.username", read_only=True)
    idioma_display = serializers.CharField(source="get_idioma_display", read_only=True)
    lecciones = LeccionSerializer(many=True, read_only=True)
    total_inscritos = serializers.SerializerMethodField()
    inscrito = serializers.SerializerMethodField()
    progreso_pct = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = ["id", "titulo", "materia", "materia_nombre",
                  "idioma", "idioma_display", "nivel",
                  "profesor_nombre", "lecciones",
                  "total_inscritos", "inscrito", "progreso_pct"]

    @extend_schema_field(serializers.IntegerField)
    def get_total_inscritos(self, obj):
        return obj.inscritos.filter(activa=True).count()

    @extend_schema_field(serializers.BooleanField)
    def get_inscrito(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return False
        return Inscripcion.objects.filter(estudiante=user, curso=obj, activa=True).exists()

    @extend_schema_field(serializers.IntegerField)
    def get_progreso_pct(self, obj):
        user = self.context.get("request").user if self.context.get("request") else None
        if not user or not user.is_authenticated:
            return 0
        total = obj.lecciones.count()
        if not total:
            return 0
        comp = ProgresoEstudiante.objects.filter(
            estudiante=user, leccion__curso=obj, completada=True
        ).count()
        return int(comp * 100 / total)


# ==================== INSCRIPCION ====================
class InscripcionSerializer(serializers.ModelSerializer):
    curso = CursoListSerializer(read_only=True)
    progreso_pct = serializers.IntegerField(read_only=True)

    class Meta:
        model = Inscripcion
        fields = ["id", "curso", "fecha_inscripcion", "activa", "progreso_pct"]


# ==================== CERTIFICADOS ====================
class CertificadoSerializer(serializers.ModelSerializer):
    curso_titulo = serializers.CharField(source="curso.titulo", read_only=True)
    estudiante_nombre = serializers.CharField(source="estudiante.username", read_only=True)

    class Meta:
        model = Certificado
        fields = ["id", "codigo", "curso", "curso_titulo",
                  "estudiante", "estudiante_nombre",
                  "fecha_emision", "fecha_completado", "estado",
                  "puntos_obtenidos", "calificacion"]


# ==================== NOTIFICACIONES ====================
class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "titulo", "mensaje", "url",
                  "leida", "creada"]


# ==================== LOGROS ====================
class LogroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logro
        fields = ["codigo", "nombre", "descripcion", "icono", "tipo", "umbral", "puntos_bonus", "activo", "creado"]

class LogroUsuarioSerializer(serializers.ModelSerializer):
    logro = LogroSerializer(read_only=True)

    class Meta:
        model = LogroUsuario
        fields = ["id", "logro", "fecha_desbloqueo"]


# ==================== RECURSOS INTERACTIVOS ====================
class RecursoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    url = serializers.CharField(source="get_url", read_only=True)
    tags_lista = serializers.ListField(read_only=True)

    class Meta:
        model = RecursoInteractivo
        fields = ["id", "titulo", "subtitulo", "slug", "descripcion",
                  "tipo", "tipo_display", "num_tecnicas", "color",
                  "url", "tags_lista", "activo"]


# ==================== EVALUACIONES ====================
class OpcionRespuestaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionRespuesta
        # No enviamos es_correcta al alumno
        fields = ["id", "texto", "orden"]


class PreguntaPublicaSerializer(serializers.ModelSerializer):
    """Pregunta vista por el alumno. Sin respuestas correctas."""
    opciones = OpcionRespuestaSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = PreguntaEvaluacion
        fields = ["id", "texto", "puntaje", "orden",
                  "tipo", "tipo_display", "opciones"]


class EvaluacionPublicaSerializer(serializers.ModelSerializer):
    preguntas = PreguntaPublicaSerializer(many=True, read_only=True)
    curso_titulo = serializers.CharField(source="curso.titulo", read_only=True)

    class Meta:
        model = Evaluacion
        fields = ["id", "titulo", "descripcion", "curso", "curso_titulo",
                  "puntaje_maximo", "puntaje_aprobacion",
                  "intentos_maximos", "tiempo_limite_minutos",
                  "preguntas"]


class IntentoSerializer(serializers.ModelSerializer):
    evaluacion_titulo = serializers.CharField(source="evaluacion.titulo", read_only=True)

    class Meta:
        model = IntentoEvaluacion
        fields = ["id", "evaluacion", "evaluacion_titulo",
                  "puntaje", "aprobado", "completado",
                  "fecha_inicio", "fecha_fin"]


class RendirEvaluacionSerializer(serializers.Serializer):
    """Recibe las respuestas del alumno."""
    respuestas = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        help_text="Dict: {pregunta_id: respuesta}"
    )


# ==================== TAREAS Y ENTREGAS ====================
class TareaSerializer(serializers.ModelSerializer):
    curso_titulo = serializers.CharField(source="curso.titulo", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Tarea
        fields = ["id", "curso", "curso_titulo", "titulo", "descripcion",
                  "tipo", "tipo_display", "estado", "fecha_limite",
                  "puntaje_maximo", "orden", "creada"]


class EntregaSerializer(serializers.ModelSerializer):
    tarea_titulo = serializers.CharField(source="tarea.titulo", read_only=True)
    estudiante_nombre = serializers.CharField(source="estudiante.username", read_only=True)

    class Meta:
        model = Entrega
        fields = ["id", "tarea", "tarea_titulo",
                  "estudiante", "estudiante_nombre",
                  "estado", "contenido", "enlace",
                  "calificacion", "retroalimentacion",
                  "fecha_entrega", "fecha_calificacion"]


# ==================== RANKING ====================
class RankingItemSerializer(serializers.Serializer):
    posicion = serializers.IntegerField()
    usuario = UserBasicSerializer()
    completadas = serializers.IntegerField()
    total = serializers.IntegerField()
    pct = serializers.IntegerField()
    promedio_eval = serializers.FloatField()
    promedio_entregas = serializers.FloatField()
    es_yo = serializers.BooleanField()

# ==================== LOGIN ====================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})
