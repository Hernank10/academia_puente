from django.urls import path
from . import views

urlpatterns = [
    # Esta ruta dice: cuando alguien entre a /contents/ejercicio/1/, 
    # busca el ejercicio con ID 1 y muéstralo.
    path('ejercicio/<int:pk>/', views.detalle_ejercicio, name='detalle_ejercicio'),
]
