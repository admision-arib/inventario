from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction

from .models import Usuario
from .forms import RegistroUsuarioForm, EditarUsuarioForm


# ==========================================
# 🔐 DECORADOR PRO (adaptado a roles múltiples)
# ==========================================
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Usa el método del modelo que verifica el rol ADMIN
        if not request.user.es_admin():
            raise PermissionDenied("No tienes permisos para acceder a este módulo")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


# ==========================================
# ✅ LISTA
# ==========================================
@login_required
@admin_required
def lista_usuarios(request):
    # Se eliminó el campo 'rol' del only() y se agregó prefetch_related('roles')
    usuarios = Usuario.objects.only(
        'id', 'dni', 'first_name', 'last_name', 'email', 'is_active'
    ).prefetch_related('roles').order_by('last_name')

    return render(request, 'usuarios/lista.html', {
        'usuarios': usuarios
    })


# ==========================================
# ✅ CREAR
# ==========================================
@login_required
@admin_required
def crear_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(request, '✅ Usuario creado exitosamente.')
                return redirect('lista_usuarios')

            except Exception as e:
                messages.error(request, f'❌ Error al crear usuario: {e}')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'usuarios/form.html', {
        'form': form,
        'accion': 'Crear'
    })


# ==========================================
# ✅ EDITAR
# ==========================================
@login_required
@admin_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(request, '✅ Usuario actualizado correctamente.')
                return redirect('lista_usuarios')

            except Exception as e:
                messages.error(request, f'❌ Error al actualizar: {e}')
    else:
        form = EditarUsuarioForm(instance=usuario)

    return render(request, 'usuarios/form.html', {
        'form': form,
        'accion': 'Editar',
        'usuario': usuario
    })


# ==========================================
# ✅ ACTIVAR / DESACTIVAR
# ==========================================
@login_required
@admin_required
def toggle_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    usuario.is_active = not usuario.is_active
    usuario.save()

    estado = "activado" if usuario.is_active else "desactivado"

    messages.warning(request, f'⚠️ Usuario {usuario.nombre_completo} {estado}.')

    return redirect('lista_usuarios')


from django.http import JsonResponse
@login_required
def obtener_area_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    if usuario.area:
        return JsonResponse({
            'area_id': usuario.area.pk,
            'area_nombre': str(usuario.area)
        })
    return JsonResponse({'area_id': None, 'area_nombre': ''})


from django.contrib.auth.views import LoginView
class CustomLoginView(LoginView):
    def form_valid(self, form):
        super().form_valid(form)
        user = self.request.user
        if user.debe_cambiar_password:
            return redirect('cambiar_password_obligatorio')
        return redirect('lista_bienes')


from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm

@login_required
def cambiar_password_obligatorio(request):
    # Si ya cambió la contraseña, redirige al inicio
    if not request.user.debe_cambiar_password:
        return redirect('lista_bienes')

    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.debe_cambiar_password = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña actualizada correctamente. Bienvenido a SIPAT.')
            return redirect('lista_bienes')
    else:
        form = SetPasswordForm(request.user)

    return render(request, 'usuarios/cambiar_password.html', {'form': form})
