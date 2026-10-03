# -*- coding: utf-8 -*-
"""Context processors del proyecto."""


def notificaciones(request):
    """Anade notif_count y notif_recientes al contexto."""
    if not request.user.is_authenticated:
        return {'notif_count': 0, 'notif_recientes': []}
    try:
        qs = request.user.notificaciones.filter(leida=False)
        return {
            'notif_count': qs.count(),
            'notif_recientes': list(qs[:5]),
        }
    except Exception:
        return {'notif_count': 0, 'notif_recientes': []}
