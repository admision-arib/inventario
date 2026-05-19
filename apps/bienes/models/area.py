from django.db import models
from .sede import Sede
from apps.usuarios.models import Usuario
from django.conf import settings


class Area(models.Model):

    nombre = models.CharField(max_length=100)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='areas')
    activo = models.BooleanField(default=True)
    jefe = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='areas_jefatura',
        verbose_name='Jefe responsable del área'
    )

    class Meta:
        db_table = 'areas'
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        unique_together = ['nombre', 'sede']
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.sede.nombre}"

