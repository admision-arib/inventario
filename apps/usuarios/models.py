from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
#from apps.bienes.models.area import Area

# ===============================
# MODELO ROL
# ===============================
class Rol(models.Model):
    ADMIN = 'ADMIN'
    CONTROL_PATRIMONIAL = 'CONTROL_PATRIMONIAL'
    RESPONSABLE_BIEN = 'RESPONSABLE_BIEN'
    INVENTARIADOR = 'INVENTARIADOR'
    AUDITOR = 'AUDITOR'
    CONSULTA = 'CONSULTA'

    CODIGOS = [
        (ADMIN, 'Administrador del Sistema'),
        (CONTROL_PATRIMONIAL, 'Control Patrimonial'),
        (RESPONSABLE_BIEN, 'Responsable de Bien'),
        (INVENTARIADOR, 'Miembro de Comisión de Inventario'),
        (AUDITOR, 'Auditor / OCI'),
        (CONSULTA, 'Solo Lectura'),
    ]

    codigo = models.CharField(
        max_length=25,
        unique=True,
        choices=CODIGOS,
        verbose_name='Código'
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')

    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['codigo']

    def __str__(self):
        return self.get_codigo_display()


# ===============================
# GESTOR DE USUARIOS PERSONALIZADO
# ===============================
class UsuarioManager(BaseUserManager):

    def create_user(self, dni, email, password=None, **extra_fields):
        if not dni:
            raise ValueError("El DNI es obligatorio")
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(dni=dni, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, dni, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        user = self.create_user(dni, email, password, **extra_fields)
        # Asignar automáticamente el rol ADMIN
        rol_admin, _ = Rol.objects.get_or_create(
            codigo=Rol.ADMIN,
            defaults={'nombre': 'Administrador del Sistema'}
        )
        user.roles.add(rol_admin)
        return user


# ===============================
# MODELO USUARIO
# ===============================
class Usuario(AbstractUser):
    username = None

    dni = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        validators=[RegexValidator(r'^\d{8}$', 'DNI debe tener 8 dígitos')],
        verbose_name='DNI'
    )
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    roles = models.ManyToManyField(
        Rol,
        related_name='usuarios',
        blank=True,
        verbose_name='Roles del sistema'
    )

    telefono = models.CharField(
        max_length=9,
        blank=True,
        validators=[RegexValidator(r'^\d{9}$', 'Teléfono debe tener 9 dígitos')],
        verbose_name='Teléfono'
    )
    area = models.ForeignKey(
        'bienes.Area',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
        verbose_name='Área / Oficina'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name='Última modificación')

    objects = UsuarioManager()

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.dni})"

    @property
    def nombre_completo(self):
        return f"{self.first_name} {self.last_name}"

    # ===========================
    # MÉTODOS AUXILIARES
    # ===========================
    def tiene_rol(self, codigo_rol):
        return self.roles.filter(codigo=codigo_rol).exists()

    # ===========================
    # VERIFICACIONES DE ROLES
    # ===========================
    def es_admin(self):
        return self.tiene_rol(Rol.ADMIN)

    def es_control_patrimonial(self):
        return self.tiene_rol(Rol.CONTROL_PATRIMONIAL)

    def es_responsable_bien(self):
        return self.tiene_rol(Rol.RESPONSABLE_BIEN)

    def es_inventariador(self):
        return self.tiene_rol(Rol.INVENTARIADOR)

    def es_auditor(self):
        return self.tiene_rol(Rol.AUDITOR)

    def es_consulta(self):
        return self.tiene_rol(Rol.CONSULTA)

    # ===========================
    # MÉTODOS DE PERMISOS COMPUESTOS
    # ===========================
    def puede_editar(self):
        return self.es_admin() or self.es_control_patrimonial()

    def puede_gestionar_bienes(self):
        return self.es_admin() or self.es_control_patrimonial()

    def puede_gestionar_usuarios(self):
        return self.es_admin()

    def puede_gestionar_comisiones(self):
        return self.es_admin() or self.es_control_patrimonial()

    def puede_escanear_inventario(self):
        return self.es_admin() or self.es_control_patrimonial() or self.es_inventariador()

    def puede_ver_reportes(self):
        return self.es_admin() or self.es_control_patrimonial() or self.es_auditor()