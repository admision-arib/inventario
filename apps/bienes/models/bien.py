import qrcode
from io import BytesIO
from django.core.files import File
from django.db import models
from .sede import Sede
from apps.usuarios.models import Usuario
from .siga import Siga
from .area import Area
from django.core.exceptions import ValidationError
import uuid


def generar_codigo():
    return f"BN-{uuid.uuid4().hex[:8]}"


class Bien(models.Model):

    # ================= CATÁLOGO =================
    catalogo = models.ForeignKey(
        Siga,
        on_delete=models.PROTECT,
        verbose_name="Catálogo SIGA"
    )

    denominacion = models.CharField(max_length=500)

    # ================= DOCUMENTO ADQUISICIÓN =================
    TIPO_DOC_ADQUISICION = [
        ('031', 'Orden de Compra'),
        ('045', 'NEA'),
    ]

    tipo_doc_adquisicion = models.CharField(max_length=3, choices=TIPO_DOC_ADQUISICION)

    # ================= MOVIMIENTO =================
    TIPO_MOVIMIENTO = [
        ('COMPRA', 'Orden de Compra'),
        ('NEA', 'Nota Entrada'),
    ]

    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, blank=True)

    # ================= TRANSFERENCIA =================
    TIPO_TRANSFERENCIA = [
        ('3', 'Ingreso Producción'),
        ('4', 'Donación'),
        ('5', 'Transferencia Externa'),
        ('8', 'Diferencia Inventario'),
        ('9', 'Otros'),
    ]

    tipo_transferencia = models.CharField(max_length=2, choices=TIPO_TRANSFERENCIA, blank=True, null=True)

    # ================= DOCUMENTO =================
    numero_documento = models.CharField(max_length=50, blank=True)
    valor_documento = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_documento = models.DateField(null=True, blank=True)

    # ================= PECOSA (ALTA) =================
    tipo_documento_alta = models.CharField(max_length=3, default='046')

    nro_pecosa = models.CharField(max_length=10, blank=True)
    fecha_salida_pecosa = models.DateField(null=True, blank=True)

    # ================= UBICACIÓN =================
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT)
    area = models.ForeignKey(Area, on_delete=models.PROTECT)

    # ================= RESPONSABLES =================
    usuario_responsable = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="responsable"
    )

    usuario_asignado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name="asignado"
    )

    # ================= CARACTERÍSTICAS =================
    marca = models.CharField(max_length=200, blank=True)
    modelo = models.CharField(max_length=200, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)

    # ================= ESTADO =================
    ESTADO = [
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('I', 'Inservible'),
        ('N', 'Nuevo')
    ]

    estado_conservacion = models.CharField(max_length=1, choices=ESTADO)

    # ================= VALOR =================
    valor_inicial = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    depreciable = models.BooleanField(default=True)

    # ================= QR =================
    qr_imagen = models.ImageField(upload_to='qr/', null=True, blank=True)

    # ================= OBS =================
    observaciones = models.TextField(blank=True)

    # ================= CODIGO =================

    codigo_patrimonial = models.CharField(max_length=20,unique=True,blank=True,null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    # ================= VALIDACIONES =================

    def clean(self):

        errors = {}

        if self.tipo_doc_adquisicion == '031':

            if not self.numero_documento:
                errors['numero_documento'] = "Número de orden requerido"

            if not self.valor_documento:
                errors['valor_documento'] = "Valor requerido"

            if not self.fecha_documento:
                errors['fecha_documento'] = "Fecha requerida"

            if self.tipo_transferencia:
                errors['tipo_transferencia'] = "No aplica en compra"

        elif self.tipo_doc_adquisicion == '045':

            if not self.numero_documento:
                errors['numero_documento'] = "Número NEA requerido"

            if not self.valor_documento:
                errors['valor_documento'] = "Valor NEA requerido"

            if not self.fecha_documento:
                errors['fecha_documento'] = "Fecha NEA requerida"

            if not self.tipo_transferencia:
                errors['tipo_transferencia'] = "Seleccione transferencia"

        # 🔥 PECOSA
        if not self.nro_pecosa:
            errors['nro_pecosa'] = "PECOSA obligatoria"

        if not self.fecha_salida_pecosa:
            errors['fecha_salida_pecosa'] = "Fecha PECOSA obligatoria"

        # 🔥 VALIDACIÓN FECHAS
        if self.fecha_documento and self.fecha_salida_pecosa:
            if self.fecha_salida_pecosa <= self.fecha_documento:
                errors['fecha_salida_pecosa'] = "Debe ser posterior a compra"

        if errors:
            raise ValidationError(errors)

    def generar_qr(self):

        data = f"""
        Código: {self.codigo_patrimonial}
        Bien: {self.denominacion}
        Sede: {self.sede}
        Área: {self.area}
        """

        qr = qrcode.make(data)

        buffer = BytesIO()
        qr.save(buffer, format='PNG')

        nombre_archivo = f'qr_{self.codigo_patrimonial}.png'

        self.qr_imagen.save(nombre_archivo, File(buffer), save=False)

    # ================= SAVE =================

    def save(self, *args, **kwargs):

        creando = self.pk is None  # ✅ saber si es nuevo

        # ================= LOGICA NORMAL =================
        self.tipo_documento_alta = '046'

        if self.tipo_doc_adquisicion == '031':
            self.tipo_movimiento = 'COMPRA'
        else:
            self.tipo_movimiento = 'NEA'

        self.valor_inicial = self.valor_documento

        if self.valor_documento:
            if self.valor_documento < 5500 / 4:
                self.depreciable = False

        if not self.codigo_patrimonial:
            self.codigo_patrimonial = generar_codigo()

        # ✅ PRIMER GUARDADO
        super().save(*args, **kwargs)

        # 🔥 GENERAR QR DESPUÉS (CORRECTO)
        if creando or not self.qr_imagen:
            self.generar_qr()
            super().save(update_fields=['qr_imagen'])









