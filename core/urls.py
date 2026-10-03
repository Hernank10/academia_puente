from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

def admin_redirect_panel(request):
    """Redirige a los no-superusers al panel web del profesor."""
    if request.user.is_authenticated and not request.user.is_superuser:
        return redirect('users:panel_home')
    # Superuser -> admin normal
    from django.contrib.admin.sites import site
    return site.index(request)


urlpatterns = [
    path('admin/', admin_redirect_panel, name='admin_redirect_panel'),
    path('i18n/setlang/', set_language, name='set_language'),
]

urlpatterns += i18n_patterns(
    path('cuenta/', include('users.urls')),
    path('', include('courses.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
