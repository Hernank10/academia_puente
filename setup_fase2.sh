#!/bin/bash
# setup_fase2.sh - Configura Fase 2 completa

set -e  # Detener si hay error

cd /workspaces/Academia_Puente_Digital
echo "═══════════════════════════════════════════════"
echo "  SETUP FASE 2: Recursos Interactivos"
echo "═══════════════════════════════════════════════"

# 1. Agregar modelo RecursoInteractivo
echo ""
echo "[1/7] Agregando modelo RecursoInteractivo a courses/models.py..."
cat >> courses/models.py << 'PYEOF'


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
    slug = models.SlugField(max_length=300, unique=True, db_index=True)
    archivo_html = models.CharField(
        max_length=500,
        help_text="Nombre del archivo dentro de templates/ejercicios_completos-lengua-castellana/"
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default='otro')
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tipo', 'orden', 'titulo']
        verbose_name = "Recurso interactivo"
        verbose_name_plural = "Recursos interactivos"

    def __str__(self):
        return self.titulo

    def get_url(self):
        return "/media/apps/lengua-castellana/" + self.archivo_html
PYEOF
echo "  ✓ Modelo agregado"

# 2. Configurar settings.py
echo ""
echo "[2/7] Configurando MEDIA_URL/MEDIA_ROOT en settings.py..."
if ! grep -q "MEDIA_ROOT = BASE_DIR / 'media'" core/settings.py; then
    cat >> core/settings.py << 'PYEOF'


# ============================================================
# FASE 2: Media files (HTMLs interactivos)
# ============================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
PYEOF
    echo "  ✓ Media configurado"
else
    echo "  - Ya estaba configurado"
fi

# 3. Configurar core/urls.py
echo ""
echo "[3/7] Configurando core/urls.py..."
cat > core/urls.py << 'PYEOF'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('courses.urls')),
]

# Servir archivos media (HTMLs interactivos) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
PYEOF
echo "  ✓ core/urls.py configurado"

# 4. Crear symlink media
echo ""
echo "[4/7] Creando symlink para media/apps/lengua-castellana..."
mkdir -p media/apps
ln -sfn "/workspaces/Academia_Puente_Digital/templates/ejercicios_completos-lengua-castellana" \
        "media/apps/lengua-castellana"
ls -la media/apps/
echo "  ✓ Symlink creado"

# 5. Agregar vistas al final de courses/views.py
echo ""
echo "[5/7] Agregando vistas de recursos a courses/views.py..."
cat > courses/views.py << 'PYEOF'
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Curso, Leccion, RecursoInteractivo


def index(request):
    """Vista principal: lista de cursos."""
    cursos = Curso.objects.all()
    return render(request, 'courses/index.html', {'cursos': cursos})


def recursos_lista(request):
    """Catálogo de recursos interactivos con filtro por tipo."""
    tipo = request.GET.get('tipo', '').strip()

    qs = RecursoInteractivo.objects.filter(activo=True)
    if tipo:
        qs = qs.filter(tipo=tipo)

    # Conteo por tipo para los filtros
    conteos = {}
    for row in RecursoInteractivo.objects.filter(activo=True).values('tipo').annotate(n=Count('id')):
        conteos[row['tipo']] = row['n']

    return render(request, 'courses/recursos_lista.html', {
        'recursos': qs,
        'tipos': RecursoInteractivo.TIPOS,
        'tipo_actual': tipo,
        'conteos': conteos,
        'total': RecursoInteractivo.objects.filter(activo=True).count(),
    })


def recurso_detalle(request, slug):
    """Detalle de un recurso con iframe embebido."""
    recurso = get_object_or_404(RecursoInteractivo, slug=slug, activo=True)
    return render(request, 'courses/recurso_detalle.html', {
        'recurso': recurso,
    })
PYEOF
echo "  ✓ Vistas creadas"

# 6. Configurar courses/urls.py
echo ""
echo "[6/7] Configurando courses/urls.py..."
cat > courses/urls.py << 'PYEOF'
from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.index, name='index'),
    path('recursos/', views.recursos_lista, name='recursos_lista'),
    path('recursos/<slug:slug>/', views.recurso_detalle, name='recurso_detalle'),
]
PYEOF
echo "  ✓ URLs configuradas"

# 7. Crear templates
echo ""
echo "[7/7] Creando templates..."
mkdir -p templates/courses

cat > templates/courses/recursos_lista.html << 'HTMLEOF'
{% extends "base.html" %}

{% block content %}
<div style="max-width: 1200px; margin: 2rem auto; padding: 0 1rem;">
    <h1>📚 Recursos interactivos</h1>
    <p style="color: #666;">
        {{ total }} apps HTML interactivas para aprender lengua castellana.
    </p>

    <div style="margin: 1.5rem 0; display: flex; flex-wrap: wrap; gap: 0.5rem;">
        <a href="?tipo="
           style="padding: 0.5rem 1rem; border-radius: 1rem; text-decoration: none;
                  background: {% if not tipo_actual %}#333{% else %}#eee{% endif %};
                  color: {% if not tipo_actual %}#fff{% else %}#333{% endif %};">
            Todos ({{ total }})
        </a>
        {% for codigo, etiqueta in tipos %}
            <a href="?tipo={{ codigo }}"
               style="padding: 0.5rem 1rem; border-radius: 1rem; text-decoration: none;
                      background: {% if tipo_actual == codigo %}#333{% else %}#eee{% endif %};
                      color: {% if tipo_actual == codigo %}#fff{% else %}#333{% endif %};">
                {{ etiqueta }}
            </a>
        {% endfor %}
    </div>

    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem;">
        {% for r in recursos %}
            <a href="{% url 'courses:recurso_detalle' r.slug %}"
               style="display: block; padding: 1rem; background: #fafafa;
                      border: 1px solid #e0e0e0; border-radius: 0.5rem;
                      text-decoration: none; color: inherit;">
                <div style="font-size: 0.75rem; color: #888; text-transform: uppercase;">
                    {{ r.get_tipo_display }}
                </div>
                <div style="font-weight: 600; margin-top: 0.25rem;">
                    {{ r.titulo }}
                </div>
            </a>
        {% empty %}
            <p>No hay recursos con ese filtro.</p>
        {% endfor %}
    </div>
</div>
{% endblock %}
HTMLEOF

cat > templates/courses/recurso_detalle.html << 'HTMLEOF'
{% extends "base.html" %}

{% block content %}
<div style="max-width: 1400px; margin: 1rem auto; padding: 0 1rem;">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
        <div>
            <a href="{% url 'courses:recursos_lista' %}" style="color: #666; text-decoration: none;">
                ← Volver al catálogo
            </a>
            <h1 style="margin: 0.25rem 0;">{{ recurso.titulo }}</h1>
            <span style="font-size: 0.8rem; color: #888; text-transform: uppercase;">
                {{ recurso.get_tipo_display }}
            </span>
        </div>
        <a href="{{ recurso.get_url }}" target="_blank"
           style="padding: 0.75rem 1.5rem; background: #333; color: #fff;
                  text-decoration: none; border-radius: 0.5rem;">
            🚀 Abrir en pestaña nueva
        </a>
    </div>

    <iframe src="{{ recurso.get_url }}"
            style="width: 100%; height: 85vh; border: 1px solid #ddd;
                   border-radius: 0.5rem; margin-top: 1rem;">
    </iframe>
</div>
{% endblock %}
HTMLEOF
echo "  ✓ Templates creados"

# 8. Crear indexar_htmls.py
echo ""
echo "[8/8] Creando indexar_htmls.py..."
cat > indexar_htmls.py << 'PYEOF'
# indexar_htmls.py
import os
import re
import django
import glob

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils.text import slugify
from django.apps import apps

CARPETA = "templates/ejercicios_completos-lengua-castellana"


def extraer_titulo(path):
    try:
        with open(path, encoding="utf-8") as f:
            contenido = f.read(10000)
    except Exception:
        return os.path.basename(path).replace(".html", "")

    m = re.search(r'<title>([^<]+)</title>', contenido, re.IGNORECASE)
    if m:
        titulo = m.group(1).strip()
        titulo = re.sub(r'\s*\|.*$', '', titulo)
        return titulo[:300]
    return os.path.basename(path).replace(".html", "")


def detectar_tipo(nombre):
    n = nombre.lower()
    if n.startswith("flota "):
        return "flota"
    if "flashcard" in n or "tarjeta" in n:
        return "flashcards"
    if "cuaderno" in n or n.startswith("cuaderno-"):
        return "cuaderno"
    if "archivo de vector" in n:
        return "archivo_vector"
    if "app" in n or "play" in n or "mission" in n or "scriptorium" in n:
        return "app"
    if re.search(r'\b\d+\s*t[eé]cnicas?\b', n):
        return "tecnica"
    return "otro"


def slug_unico(base, slug_vistos):
    slug = slugify(base, allow_unicode=False)[:200]
    if not slug:
        slug = "recurso"
    original = slug
    i = 2
    while slug in slug_vistos:
        slug = "%s-%d" % (original[:195], i)
        i += 1
    slug_vistos.add(slug)
    return slug


def main():
    RecursoInteractivo = apps.get_model('courses', 'RecursoInteractivo')

    archivos = sorted(glob.glob(os.path.join(CARPETA, "*.html")))
    print("=" * 70)
    print("INDEXADOR DE HTMLs")
    print("=" * 70)
    print("Encontrados %d archivos HTML" % len(archivos))
    print()

    slug_vistos = set(RecursoInteractivo.objects.values_list('slug', flat=True))
    creados = 0
    saltados = 0
    errores = 0

    for i, path in enumerate(archivos, 1):
        nombre_archivo = os.path.basename(path)

        if RecursoInteractivo.objects.filter(archivo_html=nombre_archivo).exists():
            saltados += 1
            continue

        try:
            titulo = extraer_titulo(path)
            tipo = detectar_tipo(nombre_archivo)
            slug = slug_unico(titulo or nombre_archivo, slug_vistos)

            RecursoInteractivo.objects.create(
                titulo=titulo[:300],
                slug=slug,
                archivo_html=nombre_archivo,
                tipo=tipo,
                orden=i,
            )
            creados += 1

            if creados % 50 == 0:
                print("  ... %d creados" % creados)

        except Exception as e:
            errores += 1
            print("  ERROR en %s: %s" % (nombre_archivo[:50], e))

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print("  Creados:   %3d" % creados)
    print("  Saltados:  %3d" % saltados)
    print("  Errores:   %3d" % errores)
    print("  Total BD:  %3d" % RecursoInteractivo.objects.count())

    from django.db.models import Count
    print()
    print("  Distribución por tipo:")
    for row in RecursoInteractivo.objects.values('tipo').annotate(n=Count('id')).order_by('-n'):
        print("    %-15s %3d" % (row['tipo'], row['n']))


if __name__ == "__main__":
    main()
PYEOF
echo "  ✓ indexar_htmls.py creado"

# 9. Agregar media/ al .gitignore
echo ""
echo "[EXTRA] Actualizando .gitignore..."
if ! grep -q "^media/" .gitignore; then
    echo "" >> .gitignore
    echo "# Fase 2: media (symlink)" >> .gitignore
    echo "media/" >> .gitignore
    echo "  ✓ .gitignore actualizado"
else
    echo "  - media/ ya estaba en .gitignore"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✅ SETUP COMPLETO"
echo "═══════════════════════════════════════════════"
echo ""
echo "Siguiente: ejecutar"
echo "  python manage.py makemigrations courses"
echo "  python manage.py migrate"
echo "  python indexar_htmls.py"
