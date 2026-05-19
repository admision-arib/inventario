from django.db import models
from .bien import Bien
from .sede import Sede
from apps.usuarios.models import Usuario

class MovimientoBien(models.Model):
    TIPOS_MOVIMIENTO = [
        ('ASIGNACION', 'Asignación en Uso'),
        ('TRANSFERENCIA', 'Transferencia Interna'),
        ('PRESTAMO', 'Préstamo Temporal'),
        ('DEVOLUCION', 'Devolución'),
    ]

    bien = models.ForeignKey(Bien, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPOS_MOVIMIENTO)
    fecha_movimiento = models.DateTimeField()

    # Origen y destino (opcionales, dependiendo del tipo)
    sede_origen = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='movimientos_origen')
    sede_destino = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='movimientos_destino')
    usuario_origen = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='movimientos_origen')
    usuario_destino = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name='movimientos_destino')

    documento_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True)

    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='movimientos_registrados')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movimientos_bienes'
        verbose_name = 'Movimiento de Bien'
        verbose_name_plural = 'Movimientos de Bienes'
        ordering = ['-fecha_movimiento']