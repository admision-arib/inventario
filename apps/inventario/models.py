
from django.db import models
from django.core.exceptions import ValidationError
from apps.usuarios.models import Usuario
from apps.bienes.models.bien import Bien


class ComisionInventario(models.Model):
    nombre = models.CharField(max_length=200)
    resolucion_designacion = models.CharField(max_length=50)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    presidente = models.ForeignKey(
        Usuario, on_delete=models.PROTECT,
        related_name='comisiones_presidente'
    )

    vocales = models.ManyToManyField(
        Usuario,
        related_name='comisiones_vocal'
    )

    veedor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='comisiones_veedor'
    )

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comisiones_inventario'

    def clean(self):
        if self.pk and self.vocales.count() < 2:
            raise ValidationError("La comisión debe tener al menos 2 vocales.")

    def __str__(self):
        return f"{self.nombre} - {self.fecha_inicio.year}"


# 🔥 INVENTARIO REAL (ESCANEO QR)
class TomaInventario(models.Model):

    ESTADOS_VERIFICACION = [
        ('ENCONTRADO', 'Encontrado'),
        ('NO_ENCONTRADO', 'No Encontrado'),
        ('SOBRANTE', 'Sobrante'),
    ]

    ESTADOS_CONSERVACION = [
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('I', 'Inservible'),
    ]

    ESTADO_REVISION = [
        ('P', 'Pendiente'),
        ('R', 'Regularizado'),
        ('D', 'Descartado'),
    ]

    estado_revision = models.CharField(
        max_length=1,
        choices=ESTADO_REVISION,
        default='P'
    )

    comision = models.ForeignKey(
        ComisionInventario,
        on_delete=models.CASCADE,
        related_name='tomas_inventario'
    )

    codigo_verificado = models.CharField(max_length=50)

    bien = models.ForeignKey(
        Bien,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    estado_verificacion = models.CharField(
        max_length=20,
        choices=ESTADOS_VERIFICACION
    )

    ubicacion_encontrada = models.CharField(
        max_length=200,
        blank=True
    )

    estado_conservacion_verificado = models.CharField(
        max_length=1,
        choices=ESTADOS_CONSERVACION,
        blank=True
    )

    observaciones = models.TextField(blank=True)

    verificado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT
    )

    fecha_verificacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tomas_inventario'
        unique_together = ['comision', 'codigo_verificado']

    def save(self, *args, **kwargs):

        # 🔥 DETECCIÓN AUTOMÁTICA POR QR
        if not self.bien:

            bien = Bien.objects.filter(
                codigo_patrimonial=self.codigo_verificado
            ).first()

            self.bien = bien

            if bien:
                self.estado_verificacion = 'ENCONTRADO'
            else:
                self.estado_verificacion = 'SOBRANTE'

        super().save(*args, **kwargs)
