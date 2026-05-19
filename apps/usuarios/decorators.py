from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


# ------------------------------------------------------------
# Decoradores genéricos
# ------------------------------------------------------------
def permiso_requerido(metodo_permiso, mensaje="No tiene permisos para acceder a esta página"):
    """
    Decorador que verifica un método de permiso del usuario.
    Ej: @permiso_requerido('puede_gestionar_bienes')
    """

    def check(user):
        if not hasattr(user, metodo_permiso):
            raise AttributeError(f"El método '{metodo_permiso}' no existe en el modelo Usuario.")
        return getattr(user, metodo_permiso)()

    return user_passes_test(check, login_url='login', redirect_field_name=None)


# ------------------------------------------------------------
# Decoradores específicos (más semánticos)
# ------------------------------------------------------------
gestionar_bienes_requerido = permiso_requerido('puede_gestionar_bienes')
escanear_inventario_requerido = permiso_requerido('puede_escanear_inventario')
gestionar_usuarios_requerido = permiso_requerido('puede_gestionar_usuarios')
gestionar_comisiones_requerido = permiso_requerido('puede_gestionar_comisiones')
ver_reportes_requerido = permiso_requerido('puede_ver_reportes')