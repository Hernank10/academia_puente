# -*- coding: utf-8 -*-
"""widgets.py - Widgets personalizados para el panel."""
from django import forms


class QuillWidget(forms.Textarea):
    """Textarea que se convierte en editor Quill via JS (ver form_generico.html)."""

    def __init__(self, attrs=None, rows=8):
        default_attrs = {
            "class": "quill-editor",
            "data-quill": "true",
            "rows": rows,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
