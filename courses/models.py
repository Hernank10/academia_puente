from django.db import models
from django.conf import settings

class Materia(models.Model):
    nombre = models.CharField(max_length=100) # Ej: Modismos, Sintaxis, Caligrafía

    def __str__(self):
        return self.nombre

class Curso(models.Model):
    NIVELES = [
        ('A1', 'A1'), ('A2', 'A2'), ('B1', 'B1'),
        ('B2', 'B2'), ('C1', 'C1'), ('C2', 'C2 (HASC2)')
    ]

    IDIOMAS = [
        ('ES', 'Español'), ('EN', 'English'), ('ZH', 'Chino'),
        ('HI', 'Hindi'), ('FR', 'Français'), ('AR', 'Árabe'),
        ('BN', 'Bengalí'), ('PT', 'Portugués'), ('RU', 'Ruso'), ('UR', 'Urdu')
    ]

    titulo = models.CharField(max_length=200)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    idioma = models.CharField(max_length=2, choices=IDIOMAS)
    nivel = models.CharField(max_length=2, choices=NIVELES)
    profesor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.titulo} - {self.get_idioma_display()} ({self.nivel})"

class Leccion(models.Model):
    curso = models.ForeignKey(Curso, related_name='lecciones', on_delete=models.CASCADE, null=True)
    titulo = models.CharField(max_length=200, verbose_name="Título de la frase/modismo")
    pais_origen = models.CharField(max_length=100, verbose_name="País donde se usa")
    explicacion = models.TextField(verbose_name="Significado y contexto cultural")
    ejemplo_uso = models.TextField(verbose_name="Ejemplo en una frase real")
    
    # --- NUEVOS CAMPOS PARA VOZ Y EJERCICIOS ---
    video_explicativo = models.FileField(upload_to='videos/', null=True, blank=True)
    ejercicio_datos = models.JSONField(default=dict, blank=True, help_text="Datos JSON: pregunta, respuesta, explicacion")
    # -------------------------------------------

    orden = models.PositiveIntegerField(default=1, verbose_name="Orden de la lección")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Lecciones"
        ordering = ['orden']

    def __str__(self):
        return f"{self.titulo} - {self.pais_origen}"

class ProgresoEstudiante(models.Model):
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE)
    completada = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Mantenemos intacta tu lógica de puntos (Gamificación)
        if self.pk:
            antiguo_progreso = ProgresoEstudiante.objects.get(pk=self.pk)
            if not antiguo_progreso.completada and self.completada:
                perfil = self.estudiante.perfil
                perfil.puntos += 5
                perfil.save()
        else:
            if self.completada:
                perfil = self.estudiante.perfil
                perfil.puntos += 5
                perfil.save()
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('estudiante', 'leccion')
        verbose_name = "Progreso de Estudiante"
        verbose_name_plural = "Progresos de Estudiantes"


# ============================================================
# FASE 2: Recursos interactivos (apps HTML)
# ============================================================

class RecursoInteractivo(models.Model):
    """Catálogo de apps HTML interactivas."""
    TIPOS = [
        ('flota', 'Flota temática'),
        ('flashcards', 'Flashcards + Quiz'),
        ('cuaderno', 'Cuaderno'),
        ('app', 'App interactiva'),
        ('tecnica', 'Técnicas numeradas'),
        ('archivo_vector', 'Archivo de Vector'),
        ('otro', 'Otro'),
    ]

    titulo = models.CharField(max_length=300)
    subtitulo = models.CharField(max_length=300, blank=True,
        help_text="Frase corta que describe el recurso")
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    archivo_html = models.CharField(
        max_length=500,
        help_text="Nombre del archivo dentro de templates/ejercicios_completos-lengua-castellana/"
    )
    descripcion = models.TextField(blank=True,
        help_text="Descripción extraída del HTML")
    tags = models.CharField(max_length=300, blank=True,
        help_text="Etiquetas separadas por coma")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='otro')
    num_tecnicas = models.IntegerField(default=0,
        help_text="Número de técnicas/ejercicios, si aplica")
    color = models.CharField(max_length=20, blank=True,
        help_text="Color principal extraído del HTML (hex)")
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo', 'orden', 'titulo']
        verbose_name = "Recurso interactivo"
        verbose_name_plural = "Recursos interactivos"

    def __str__(self):
        return self.titulo

    def get_url(self):
        from urllib.parse import quote
        return "/media/apps/lengua-castellana/" + quote(self.archivo_html)

    @property
    def tags_lista(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def tiene_info(self):
        """¿Tiene información enriquecida?"""
        return bool(self.subtitulo or self.descripcion)


# ============================================================
# FASE 3: Inscripciones a cursos
# ============================================================

class Inscripcion(models.Model):
    """Relaciona un estudiante con un curso."""
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscripciones'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='inscritos')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('estudiante', 'curso')
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"

    def __str__(self):
        return f"{self.estudiante.username} → {self.curso.titulo}"

    @property
    def progreso_pct(self):
        total = self.curso.lecciones.count()
        if not total:
            return 0
        completadas = ProgresoEstudiante.objects.filter(
            estudiante=self.estudiante,
            leccion__curso=self.curso,
            completada=True
        ).count()
        return int(completadas * 100 / total)


# ============================================================
# FASE 4: Certificaciones
# ============================================================
import uuid
from django.utils import timezone


class Certificado(models.Model):
    """Certificado emitido a un estudiante por completar un curso."""
    ESTADOS = [
        ('emitido', 'Emitido'),
        ('revocado', 'Revocado'),
    ]

    codigo = models.CharField(max_length=20, unique=True, db_index=True)
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificados'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='certificados')
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='emitido')
    puntos_obtenidos = models.IntegerField(default=0)
    calificacion = models.CharField(max_length=50, blank=True, default="Aprobado")

    class Meta:
        unique_together = ('estudiante', 'curso')
        ordering = ['-fecha_emision']
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"

    def __str__(self):
        return f"{self.codigo} - {self.estudiante.username} - {self.curso.titulo}"

    def save(self, *args, **kwargs):
        if not self.codigo:
            # Generar código único tipo "PD-2026-A3F8K9"
            anio = timezone.now().year
            sufijo = uuid.uuid4().hex[:6].upper()
            self.codigo = f"PD-{anio}-{sufijo}"
        super().save(*args, **kwargs)

    @property
    def url_publica(self):
        return f"/certificado/{self.codigo}/"


def emitir_certificado(estudiante, curso):
    """Emite un certificado si no existe. Devuelve (certificado, creado)."""
    # Verificar que completó el 100%
    total = curso.lecciones.count()
    if total == 0:
        return None, False

    completadas = ProgresoEstudiante.objects.filter(
        estudiante=estudiante,
        leccion__curso=curso,
        completada=True
    ).count()

    if completadas < total:
        return None, False

    # Calcular puntos obtenidos en este curso
    puntos = completadas * 10

    cert, creado = Certificado.objects.get_or_create(
        estudiante=estudiante,
        curso=curso,
        defaults={
            'puntos_obtenidos': puntos,
            'calificacion': 'Sobresaliente' if completadas >= total else 'Aprobado',
        }
    )
    return cert, creado


# ============================================================
# Campos extra para RecursoInteractivo (enriquecimiento)
# ============================================================


# ============================================================
# FASE 5: Tareas y Entregas
# ============================================================

class Tarea(models.Model):
    """Tarea asignada por el profesor dentro de un curso."""
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    ]

    TIPOS = [
        ('texto', 'Respuesta escrita'),
        ('archivo', 'Subir archivo'),
        ('enlace', 'Enlace'),
        ('codigo', 'Código'),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(help_text="Instrucciones para el estudiante")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='texto')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='publicada')
    fecha_limite = models.DateTimeField(null=True, blank=True)
    puntaje_maximo = models.IntegerField(default=100)
    orden = models.IntegerField(default=0)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', '-creada']
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"

    def __str__(self):
        return f"{self.curso.titulo} → {self.titulo}"

    @property
    def total_entregas(self):
        return self.entregas.count()

    @property
    def entregas_pendientes(self):
        return self.entregas.filter(calificada=False).count()

    @property
    def entregas_calificadas(self):
        return self.entregas.filter(calificada=True).count()


class Entrega(models.Model):
    """Entrega de un estudiante para una tarea."""
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('entregada', 'Entregada'),
        ('calificada', 'Calificada'),
        ('devuelta', 'Devuelta para revisión'),
    ]

    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas')
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entregas'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='entregada')
    contenido = models.TextField(blank=True, help_text="Respuesta escrita o comentario")
    archivo = models.FileField(upload_to='entregas/', null=True, blank=True)
    enlace = models.URLField(blank=True)
    calificacion = models.IntegerField(null=True, blank=True)
    retroalimentacion = models.TextField(blank=True, help_text="Comentarios del profesor")
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    fecha_calificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tarea', 'estudiante')
        ordering = ['-fecha_entrega']
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"

    def __str__(self):
        return f"{self.estudiante.username} → {self.tarea.titulo}"

    @property
    def calificada(self):
        return self.estado == 'calificada' and self.calificacion is not None

    @property
    def color_estado(self):
        return {
            'borrador': '#8b949e',
            'entregada': '#f1c40f',
            'calificada': '#4ade80',
            'devuelta': '#ff9999',
        }.get(self.estado, '#8b949e')


# ============================================================
# FASE 6: Evaluaciones (Quizzes)
# ============================================================

class Evaluacion(models.Model):
    """Evaluación de un curso con múltiples preguntas."""
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('publicada', 'Publicada'),
        ('cerrada', 'Cerrada'),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='evaluaciones')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='publicada')

    # Configuración
    puntaje_maximo = models.IntegerField(default=100, help_text="Puntaje total posible")
    puntaje_aprobacion = models.IntegerField(default=60, help_text="Puntaje mínimo para aprobar")
    intentos_maximos = models.IntegerField(default=3, help_text="Cuántas veces puede intentarlo")
    tiempo_limite_minutos = models.IntegerField(default=30, blank=True, null=True)
    aleatorizar_preguntas = models.BooleanField(default=False)

    # Timestamps
    creada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['curso', 'titulo']
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"

    def __str__(self):
        return f"{self.curso.titulo} → {self.titulo}"

    @property
    def total_preguntas(self):
        return self.preguntas.count()

    @property
    def total_intentos(self):
        return self.intentos.count()

    @property
    def promedio_puntaje(self):
        from django.db.models import Avg
        r = self.intentos.filter(completado=True).aggregate(avg=Avg('puntaje'))['avg']
        return round(r, 1) if r else 0

    @property
    def tasa_aprobacion(self):
        total = self.intentos.filter(completado=True).count()
        if not total:
            return 0
        aprobados = self.intentos.filter(completado=True, aprobado=True).count()
        return int(aprobados * 100 / total)


class PreguntaEvaluacion(models.Model):
    """Una pregunta dentro de una evaluación."""
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='preguntas')
    texto = models.TextField(help_text="Enunciado de la pregunta")
    explicacion = models.TextField(blank=True, help_text="Explicación de la respuesta correcta")
    puntaje = models.IntegerField(default=10, help_text="Puntos que vale esta pregunta")
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['evaluacion', 'orden']
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"

    def __str__(self):
        return self.texto[:80]

    @property
    def opcion_correcta(self):
        return self.opciones.filter(es_correcta=True).first()


class OpcionRespuesta(models.Model):
    """Una opción de respuesta para una pregunta."""
    pregunta = models.ForeignKey(PreguntaEvaluacion, on_delete=models.CASCADE, related_name='opciones')
    texto = models.CharField(max_length=500)
    es_correcta = models.BooleanField(default=False)
    orden = models.IntegerField(default=0)

    class Meta:
        ordering = ['pregunta', 'orden']
        verbose_name = "Opción de respuesta"
        verbose_name_plural = "Opciones de respuesta"

    def __str__(self):
        return f"{'✓' if self.es_correcta else ' '} {self.texto[:60]}"


class IntentoEvaluacion(models.Model):
    """Intento de un estudiante en una evaluación."""
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='intentos')
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='intentos_evaluacion'
    )
    puntaje = models.IntegerField(default=0)
    aprobado = models.BooleanField(default=False)
    completado = models.BooleanField(default=False)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = "Intento de evaluación"
        verbose_name_plural = "Intentos de evaluación"

    def __str__(self):
        return f"{self.estudiante.username} → {self.evaluacion.titulo} ({self.puntaje})"

    @property
    def duracion_segundos(self):
        if self.fecha_fin and self.fecha_inicio:
            return (self.fecha_fin - self.fecha_inicio).total_seconds()
        return None


class RespuestaIntento(models.Model):
    """Respuesta específica de un estudiante a una pregunta en un intento."""
    intento = models.ForeignKey(IntentoEvaluacion, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(PreguntaEvaluacion, on_delete=models.CASCADE)
    opcion_elegida = models.ForeignKey(OpcionRespuesta, on_delete=models.CASCADE)
    es_correcta = models.BooleanField(default=False)

    class Meta:
        unique_together = ('intento', 'pregunta')
        verbose_name = "Respuesta del intento"
        verbose_name_plural = "Respuestas del intento"

    def save(self, *args, **kwargs):
        # Auto-marcar si es correcta
        self.es_correcta = self.opcion_elegida.es_correcta
        super().save(*args, **kwargs)
