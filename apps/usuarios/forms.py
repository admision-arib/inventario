from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Usuario, Rol
from apps.bienes.models.area import Area



class RegistroUsuarioForm(UserCreationForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Roles del sistema'
    )
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label='Área de trabajo'
    )

    class Meta:
        model = Usuario
        fields = [
            'dni', 'email',
            'first_name', 'last_name',
            'roles', 'telefono', 'area'
        ]

        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-bold tracking-wider focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400',
                'placeholder': 'Ingrese DNI (8 dígitos)',
                'maxlength': '8'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400',
                'placeholder': 'correo@iestparib.edu.pe'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400',
                'placeholder': 'Ej. Juan Carlos'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400',
                'placeholder': 'Ej. Ramos Ramos'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400',
                'placeholder': '999999999',
                'maxlength': '9'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        clase_password = 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-400'

        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({'class': clase_password, 'placeholder': '••••••••'})
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({'class': clase_password, 'placeholder': '••••••••'})
        if 'area' in self.fields:
            self.fields['area'].widget.attrs.update({
                'class': 'w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all'
            })

    # --- Validaciones (sin cambios) ---
    def clean_dni(self):
        dni = self.cleaned_data.get('dni', '').strip()
        if not dni.isdigit() or len(dni) != 8:
            raise ValidationError("El DNI debe constar exactamente de 8 caracteres numéricos.")
        qs = Usuario.objects.filter(dni=dni)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este número de DNI ya se encuentra registrado en el sistema.")
        return dni

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        qs = Usuario.objects.filter(email=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Esta dirección de correo ya está registrada.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            if not telefono.isdigit() or len(telefono) != 9:
                raise ValidationError("El número de teléfono debe constar de 9 dígitos.")
        return telefono

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.debe_cambiar_password = True       # <-- siempre fuerza el cambio
        if usuario.email:
            usuario.username = usuario.email.lower().strip()
        if commit:
            usuario.save()
            self.save_m2m()                         # guarda los roles ManyToMany
        return usuario


class EditarUsuarioForm(UserChangeForm):
    password = None  # Oculta el campo de contraseña en la edición

    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Roles del sistema'
    )
    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label='Área de trabajo'
    )
    debe_cambiar_password = forms.BooleanField(
        required=False,
        initial=False,
        label='Forzar cambio de contraseña en el próximo inicio de sesión'
    )

    class Meta:
        model = Usuario
        fields = [
            'dni', 'email',
            'first_name', 'last_name',
            'roles', 'telefono', 'area',
            'is_active', 'debe_cambiar_password'   # agregado
        ]

        widgets = {
            'dni': forms.TextInput(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'telefono': forms.TextInput(attrs={'class': 'w-full border rounded-lg px-3 py-2'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded text-blue-600'}),
            # 'debe_cambiar_password' no requiere clase especial; usa el estilo por defecto
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilos adicionales para el campo area (opcional)
        if 'area' in self.fields:
            self.fields['area'].widget.attrs.update({
                'class': 'w-full border rounded-lg px-3 py-2'
            })

    # --- Validaciones (sin cambios) ---
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Usuario.objects.filter(dni=dni).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este DNI ya está registrado")
        return dni

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Este correo ya está registrado")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if commit:
            usuario.save()
            self.save_m2m()
        return usuario



# El LoginForm no necesita cambios porque solo usa 'username' (DNI) y 'password'
class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'DNI'
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Ingrese su DNI',
            'autofocus': True,
        })