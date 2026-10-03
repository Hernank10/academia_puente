# -*- coding: utf-8 -*-
"""forms_profesor.py - Formularios del panel del profesor."""
from django import forms
from .widgets import QuillWidget
from courses.models import (
    Curso, Leccion, Tarea, Entrega,
    Evaluacion, PreguntaEvaluacion, OpcionRespuesta,
)


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["titulo", "materia", "idioma", "nivel"]


class LeccionForm(forms.ModelForm):
    class Meta:
        model = Leccion
        fields = ["titulo", "pais_origen", "explicacion", "ejemplo_uso",
                  "video_explicativo", "ejercicio_datos", "orden"]
        widgets = {
            "explicacion": QuillWidget(rows=10),
            "ejemplo_uso": QuillWidget(rows=5),
            "ejercicio_datos": forms.Textarea(attrs={"rows": 3}),
        }


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ["titulo", "descripcion", "tipo", "estado",
                  "fecha_limite", "puntaje_maximo", "orden"]
        widgets = {
            "descripcion": QuillWidget(rows=8),
            "fecha_limite": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_limite"].input_formats = [
            "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
        ]
        self.fields["fecha_limite"].required = False


class EvaluacionForm(forms.ModelForm):
    class Meta:
        model = Evaluacion
        fields = ["titulo", "descripcion", "estado",
                  "puntaje_maximo", "puntaje_aprobacion",
                  "intentos_maximos", "tiempo_limite_minutos",
                  "aleatorizar_preguntas"]
        widgets = {"descripcion": QuillWidget(rows=6)}


class PreguntaForm(forms.ModelForm):
    class Meta:
        model = PreguntaEvaluacion
        fields = ["texto", "explicacion", "puntaje", "orden"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3}),
            "explicacion": forms.Textarea(attrs={"rows": 2}),
        }


class OpcionForm(forms.ModelForm):
    class Meta:
        model = OpcionRespuesta
        fields = ["texto", "es_correcta", "orden"]


class CalificarEntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ["calificacion", "retroalimentacion", "estado"]
        widgets = {"retroalimentacion": forms.Textarea(attrs={"rows": 4})}
