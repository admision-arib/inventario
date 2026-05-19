from django.db import models

class Siga(models.Model):
    codigo_siga = models.CharField(max_length=20, unique=True, verbose_name="Código SIGA")
    denominacion = models.TextField(verbose_name="Denominación")
    clasificador = models.CharField(max_length=50, blank=True, null=True)
    # Ya no necesitamos el campo 'tipo', porque solo serán bienes
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'siga_items'
        verbose_name = 'Ítem SIGA (Bienes)'
        verbose_name_plural = 'Ítems SIGA (Bienes)'
        ordering = ['codigo_siga']

    def __str__(self):
        return f"{self.codigo_siga} - {self.denominacion[:80]}"