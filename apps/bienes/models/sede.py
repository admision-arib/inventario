from django.db import models

class Sede(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=200)
    direccion = models.TextField()
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'sedes'
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"