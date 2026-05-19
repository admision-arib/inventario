from django.core.management.base import BaseCommand
from apps.usuarios.models import Rol


class Command(BaseCommand):
    help = 'Crea los roles iniciales del sistema SIPAT'

    def handle(self, *args, **options):
        roles_iniciales = [
            ('ADMIN', 'Administrador del Sistema', 'Acceso total al sistema'),
            ('CONTROL_PATRIMONIAL', 'Control Patrimonial',
             'Unidad de Control Patrimonial – Gestiona bienes, catálogo, comisiones y reportes'),
            ('RESPONSABLE_BIEN', 'Responsable de Bien',
             'Usuario que recibe y custodia bienes – Ve sus bienes asignados'),
            ('INVENTARIADOR', 'Miembro de Comisión de Inventario',
             'Participa en escaneo de inventario físico'),
            ('AUDITOR', 'Auditor / OCI', 'Acceso de lectura a reportes y bienes'),
            ('CONSULTA', 'Solo Lectura', 'Puede ver bienes sin modificar'),
        ]

        for codigo, nombre, descripcion in roles_iniciales:
            rol, creado = Rol.objects.get_or_create(
                codigo=codigo,
                defaults={'nombre': nombre, 'descripcion': descripcion}
            )
            if creado:
                self.stdout.write(self.style.SUCCESS(f'✓ Rol creado: {nombre} ({codigo})'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Rol ya existente: {nombre} ({codigo})'))

        self.stdout.write(self.style.SUCCESS('\n✅ Todos los roles iniciales están disponibles.'))