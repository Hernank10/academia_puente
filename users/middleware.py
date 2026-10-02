from django.utils import translation

class IdiomaPerfilMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Verificamos si el usuario entró con su cuenta
        if request.user.is_authenticated:
            try:
                # 2. Sacamos el idioma de su perfil
                idioma = request.user.perfil.idioma_nativo
                if idioma:
                    # 3. ¡Activamos el idioma para esta sesión!
                    translation.activate(idioma)
                    request.LANGUAGE_CODE = translation.get_language()
            except Exception:
                pass
        
        response = self.get_response(request)
        # 4. Limpiamos al terminar la petición
        translation.deactivate()
        return response
