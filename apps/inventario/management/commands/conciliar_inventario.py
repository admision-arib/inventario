import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.inventario.models import ComisionInventario, TomaInventario
from apps.bienes.models.bien import Bien
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Ejecuta conciliación de inventario desde un CSV'

    def add_arguments(self, parser):
        parser.add_argument('comision_id', type=int)
        parser.add_argument('ruta_csv', type=str)
        parser.add_argument('--verificado_por_id', type=int, default=1)

    def handle(self, *args, **options):

        try:
            comision = ComisionInventario.objects.get(pk=options['comision_id'])
        except ComisionInventario.DoesNotExist:
            self.stderr.write("❌ Comisión no existe")
            return

        try:
            usuario = Usuario.objects.get(pk=options['verificado_por_id'])
        except Usuario.DoesNotExist:
            self.stderr.write("❌ Usuario no existe")
            return

        df = pd.read_csv(options['ruta_csv'], dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]

        columnas_requeridas = ['codigo_patrimonial', 'ubicacion_real', 'estado_real']

        if not all(col in df.columns for col in columnas_requeridas):
            self.stderr.write(f"❌ Columnas requeridas: {columnas_requeridas}")
            return

        # 🔥 LIMPIAR TOMA ANTERIOR (IMPORTANTE)
        TomaInventario.objects.filter(comision=comision).delete()

        sobrantes = 0
        faltantes = 0
        encontrados = 0
        errores = 0

        codigos_escaneados = set()

        with transaction.atomic():

            for idx, row in df.iterrows():
                try:
                    codigo = str(row['codigo_patrimonial']).strip()
                    ubicacion = str(row['ubicacion_real']).strip()

                    estado = str(row['estado_real']).strip().upper()

                    if estado not in ['B', 'R', 'M', 'I']:
                        estado = ''

                    codigos_escaneados.add(codigo)

                    bien = Bien.objects.filter(
                        codigo_patrimonial=codigo,
                        activo=True
                    ).first()

                    if not bien:
                        # 🟡 SOBRANTE
                        TomaInventario.objects.create(
                            comision=comision,
                            codigo_verificado=codigo,
                            estado_verificacion='SOBRANTE',
                            ubicacion_encontrada=ubicacion,
                            estado_conservacion_verificado=estado,
                            verificado_por=usuario
                        )
                        sobrantes += 1
                        continue

                    # ✅ ENCONTRADO
                    bien.ubicacion_especifica = ubicacion

                    if estado:
                        bien.estado_conservacion = estado

                    bien.save()

                    TomaInventario.objects.create(
                        comision=comision,
                        codigo_verificado=codigo,
                        bien=bien,
                        estado_verificacion='ENCONTRADO',
                        ubicacion_encontrada=ubicacion,
                        estado_conservacion_verificado=estado,
                        verificado_por=usuario
                    )

                    encontrados += 1

                except Exception as e:
                    errores += 1
                    self.stderr.write(f"⚠️ Error fila {idx}: {e}")

            # 🔴 FALTANTES
            bienes_no_escaneados = Bien.objects.filter(
                activo=True
            ).exclude(
                codigo_patrimonial__in=codigos_escaneados
            )

            for bien in bienes_no_escaneados:
                TomaInventario.objects.create(
                    comision=comision,
                    codigo_verificado=bien.codigo_patrimonial,
                    bien=bien,
                    estado_verificacion='NO_ENCONTRADO',
                    observaciones='No escaneado',
                    verificado_por=usuario
                )
                faltantes += 1

        self.stdout.write(self.style.SUCCESS(
            f"""
✅ CONCILIACIÓN TERMINADA
✔ Encontrados: {encontrados}
✔ Sobrantes: {sobrantes}
✔ Faltantes: {faltantes}
⚠️ Errores: {errores}
"""
        ))