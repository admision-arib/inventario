import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.bienes.models.siga import Siga


class Command(BaseCommand):
    help = "Carga el Catálogo de Bienes SIGA desde Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            '--ruta',
            type=str,
            help='Ruta al archivo Excel'
        )

    def handle(self, *args, **options):

        # =========================
        # 📁 RUTA DEL ARCHIVO
        # =========================
        ruta = options.get('ruta')

        if not ruta:
            ruta = Path(__file__).resolve().parent.parent.parent / "data" / "CATALOGO_BIENES_SERVICIOS.xlsx"
        else:
            ruta = Path(ruta)

        if not ruta.exists():
            self.stderr.write(self.style.ERROR(f"❌ No existe el archivo: {ruta}"))
            return

        self.stdout.write("📖 Leyendo archivo Excel...")

        # =========================
        # 📊 LEER EXCEL
        # =========================
        try:
            df = pd.read_excel(ruta, sheet_name='BIENES', dtype=str)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error al leer Excel: {e}"))
            return

        # =========================
        # 🧹 LIMPIEZA
        # =========================
        df = df.dropna(how='all')

        # Normalizar nombres de columnas
        df.columns = df.columns.astype(str).str.strip().str.upper()

        self.stdout.write(f"✅ Columnas detectadas: {list(df.columns)}")

        # =========================
        # ✅ VALIDAR COLUMNAS
        # =========================
        if 'CODIGO' not in df.columns or 'DESCRIPCION DEL ITEM' not in df.columns:
            self.stderr.write(self.style.ERROR(
                "❌ No se encontraron columnas necesarias (CODIGO, DESCRIPCION DEL ITEM)"
            ))
            return

        col_codigo = 'CODIGO'
        col_descripcion = 'DESCRIPCION DEL ITEM'
        col_clasificador = 'CLASIFICADOR' if 'CLASIFICADOR' in df.columns else None

        # =========================
        # 🧹 LIMPIAR DATOS
        # =========================
        df = df[df[col_codigo].notna()]
        df[col_codigo] = df[col_codigo].astype(str).str.strip()
        df[col_descripcion] = df[col_descripcion].astype(str).str.strip()

        self.stdout.write(f"📊 Filas válidas: {len(df)}")

        # =========================
        # ⚡ OPTIMIZACIÓN DB
        # =========================
        codigos_existentes = set(
            Siga.objects.values_list('codigo_siga', flat=True)
        )

        items_crear = []
        creados = 0
        existentes = 0
        errores = []

        # =========================
        # 🚀 PROCESAMIENTO
        # =========================
        for _, row in df.iterrows():

            codigo = row[col_codigo]
            descripcion = row[col_descripcion]

            clasificador = ''
            if col_clasificador and pd.notna(row.get(col_clasificador)):
                clasificador = str(row[col_clasificador]).strip()

            # ✅ Solo bienes (SIGA inicia con B)
            if not codigo.startswith('B'):
                continue

            # ✅ Evitar duplicados
            if codigo in codigos_existentes:
                existentes += 1
                continue

            items_crear.append(
                Siga(
                    codigo_siga=codigo,
                    denominacion=descripcion,
                    clasificador=clasificador,
                    activo=True
                )
            )

            creados += 1

        # =========================
        # 💾 GUARDADO MASIVO
        # =========================
        try:
            with transaction.atomic():
                Siga.objects.bulk_create(items_crear, batch_size=1000)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Error en inserción: {e}"))
            return

        # =========================
        # ✅ RESULTADO FINAL
        # =========================
        self.stdout.write(self.style.SUCCESS(
            f"✅ Carga completada → {creados} nuevos | {existentes} existentes"
        ))

        if errores:
            self.stdout.write(self.style.WARNING(f"⚠️ {len(errores)} errores"))
            for err in errores[:5]:
                self.stdout.write(f" - {err}")
