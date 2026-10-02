from django.db import models

class AreaLinguistica(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Áreas Lingüísticas"

    def __str__(self):
        return self.nombre

class Ejercicio(models.Model):
    area = models.ForeignKey(AreaLinguistica, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    
    # Aquí es donde pegaremos los 30 ejercicios en formato JSON
    configuracion = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.area.nombre} - {self.titulo}"
