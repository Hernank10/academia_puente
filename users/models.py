from django.db import models
from django.contrib.auth.models import User
import pytz

class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')

    # 1. Roles
    ROLES = [
        ('estudiante', 'Estudiante'),
        ('profesor', 'Profesor / Licenciado'),
    ]
    rol_principal = models.CharField(max_length=20, choices=ROLES, default='estudiante')

    # 2. Atributos Académicos
    ESTADOS = [
        ('grado', 'Estudiante de Grado'),
        ('licenciado', 'Licenciado'),
        ('magister', 'Magíster / Investigador'),
    ]
    estado_academico = models.CharField(max_length=20, choices=ESTADOS, default='grado')
    areas_especialidad = models.CharField(max_length=255, default='Lingüística, Didáctica del Castellano')

    # 3. Permisos y Biografía
    puede_publicar_cursos = models.BooleanField(default=False)
    biografia = models.TextField(blank=True, verbose_name="Resumen Profesional")

    # 4. Idiomas y Variantes
    IDIOMAS = [
        ('es', 'Español'), ('en', 'English'), ('zh-hans', '简体中文'),
        ('hi', 'हिन्दी'), ('fr', 'Français'), ('ar', 'العربية'),
        ('bn', 'বাংলা'), ('pt', 'Português'), ('ru', 'Русский'), ('ur', 'اردو'),
    ]
    idioma_nativo = models.CharField(max_length=10, choices=IDIOMAS, default='es')

    VARIANTES = [
        ('rio', 'Rioplatense'),
        ('car', 'Caribeño'),
        ('cast', 'Peninsular'),
        ('lat', 'Latinoamérica Estándar'),
    ]
    variante_interes = models.CharField(max_length=5, choices=VARIANTES, default='lat')

    # 5. Gamificación (Puntos de Sabiduría acumulados)
    puntos = models.PositiveIntegerField(default=0, verbose_name="Puntos de Sabiduría")

    # 6. Configuración Regional
    ZONAS = [(tz, tz) for tz in pytz.common_timezones if '/' in tz]
    zona_horaria = models.CharField(max_length=100, choices=ZONAS, default='UTC')

    @property
    def rango_academico(self):
        if self.puntos < 100:
            return "Aprendiz de Idiomas"
        elif self.puntos < 500:
            return "Intérprete Cultural"
        else:
            return "Sabio Licenciado"

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_principal_display()}"



# ============================================================
# GAMIFICACIÓN: Logros, medallas, insignias
# ============================================================

class Logro(models.Model):
    """Medalla/insignia que un usuario puede ganar."""
    TIPOS = [
        ('puntos', 'Puntos'),
        ('lecciones', 'Lecciones completadas'),
        ('cursos', 'Cursos inscritos'),
        ('racha', 'Racha de días'),
        ('especial', 'Logro especial'),
    ]
    ICONOS = [
        ('🏅', 'Medalla'),
        ('🎖️', 'Condecoración'),
        ('🥇', 'Oro'),
        ('🥈', 'Plata'),
        ('🥉', 'Bronce'),
        ('⭐', 'Estrella'),
        ('🌟', 'Estrella brillante'),
        ('💎', 'Diamante'),
        ('👑', 'Corona'),
        ('🔥', 'Racha'),
        ('📚', 'Libro'),
        ('🎓', 'Graduación'),
        ('🏆', 'Trofeo'),
        ('🧠', 'Cerebro'),
        ('✍️', 'Escritura'),
        ('🎯', 'Objetivo'),
        ('🚀', 'Cohete'),
        ('🌱', 'Brote'),
        ('🌳', 'Árbol'),
    ]

    codigo = models.SlugField(max_length=50, unique=True, help_text="Ej: primer-paso")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=5, choices=ICONOS, default='🏅')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='especial')
    umbral = models.IntegerField(default=1, help_text="Cantidad necesaria para desbloquear")
    puntos_bonus = models.IntegerField(default=0, help_text="Puntos extra al desbloquear")
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tipo', 'umbral']
        verbose_name = "Logro"
        verbose_name_plural = "Logros"

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class LogroUsuario(models.Model):
    """Registra qué logros ha ganado cada usuario."""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logros')
    logro = models.ForeignKey(Logro, on_delete=models.CASCADE)
    fecha_desbloqueo = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'logro')
        ordering = ['-fecha_desbloqueo']
        verbose_name = "Logro de usuario"
        verbose_name_plural = "Logros de usuarios"

    def __str__(self):
        return f"{self.usuario.username} → {self.logro.nombre}"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def calcular_rango(puntos):
    """Devuelve (nombre, icono, siguiente_umbral) según los puntos."""
    RANGOS = [
        (0,      'Novato',       '🌱',  100),
        (100,    'Aprendiz',     '📖',  500),
        (500,    'Estudioso',    '✍️',  1500),
        (1500,   'Intérprete',   '🎯',  3000),
        (3000,   'Erudito',      '🧠',  6000),
        (6000,   'Maestro',      '🎓',  12000),
        (12000,  'Sabio',        '👑',  24000),
        (24000,  'Sabio Mayor',  '💎',  48000),
        (48000,  'Leyenda',      '🏆',  None),
    ]
    rango_actual = RANGOS[0]
    for r in RANGOS:
        if puntos >= r[0]:
            rango_actual = r
    return rango_actual[1], rango_actual[2], rango_actual[3]


def otorgar_logro(usuario, codigo):
    """Otorga un logro a un usuario si aún no lo tiene. Devuelve True si es nuevo."""
    try:
        logro = Logro.objects.get(codigo=codigo, activo=True)
    except Logro.DoesNotExist:
        return False

    obj, creado = LogroUsuario.objects.get_or_create(usuario=usuario, logro=logro)
    if creado and logro.puntos_bonus:
        perfil, _ = Perfil.objects.get_or_create(usuario=usuario)
        perfil.puntos += logro.puntos_bonus
        perfil.save()
    return creado


def verificar_logros(usuario):
    """Revisa el estado del usuario y otorga logros según corresponda."""
    from courses.models import Inscripcion, ProgresoEstudiante

    perfil, _ = Perfil.objects.get_or_create(usuario=usuario)

    # Lecciones completadas
    lecciones = ProgresoEstudiante.objects.filter(estudiante=usuario, completada=True).count()

    # Cursos inscritos
    cursos = Inscripcion.objects.filter(estudiante=usuario, activa=True).count()

    # Reglas automáticas
    reglas = [
        (lecciones >= 1,   'primer-paso'),
        (lecciones >= 10,  'diez-lecciones'),
        (lecciones >= 50,  'cincuenta-lecciones'),
        (lecciones >= 100, 'cien-lecciones'),
        (lecciones >= 500, 'quinientas-lecciones'),
        (cursos >= 1,      'primer-curso'),
        (cursos >= 3,      'tres-cursos'),
        (cursos >= 5,      'cinco-cursos'),
        (perfil.puntos >= 100,  'cien-puntos'),
        (perfil.puntos >= 500,  'quinientos-puntos'),
        (perfil.puntos >= 1000, 'mil-puntos'),
        (perfil.puntos >= 5000, 'cinco-mil-puntos'),
    ]

    nuevos = []
    for condicion, codigo in reglas:
        if condicion and otorgar_logro(usuario, codigo):
            nuevos.append(codigo)
    return nuevos
