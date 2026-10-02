from django.shortcuts import render, get_object_or_404
from .models import Ejercicio

def detalle_ejercicio(request, pk):
    # Traemos el ejercicio de la base de datos o damos error 404 si no existe
    ejercicio = get_object_or_404(Ejercicio, pk=pk)
    return render(request, 'contents/ejercicio_vocal.html', {'ejercicio': ejercicio})
