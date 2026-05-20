from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario

class Command(BaseCommand):
    help = 'Obliga a los usuarios activos a cambiar su contraseña en el próximo inicio de sesión'

    def add_arguments(self, parser):
        parser.add_argument(
            '--excluir-superusuarios',
            action='store_true',
            help='No forzar a los superusuarios',
        )

    def handle(self, *args, **options):
        usuarios = Usuario.objects.filter(is_active=True)
        if options['excluir_superusuarios']:
            usuarios = usuarios.filter(is_superuser=False)

        count = usuarios.update(debe_cambiar_password=True)
        self.stdout.write(self.style.SUCCESS(
            f'Se ha forzado el cambio de contraseña para {count} usuarios activos.'
        ))