from django import forms
from django.core.exceptions import ValidationError
from .models import ComisionInventario


# ========================================
# FORM: COMISIÓN DE INVENTARIO
# ========================================
class ComisionInventarioForm(forms.ModelForm):

    class Meta:
        model = ComisionInventario
        fields = [
            'nombre',
            'resolucion_designacion',
            'fecha_inicio',
            'fecha_fin',
            'presidente',
            'vocales',
            'veedor'
        ]

        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2',
                'placeholder': 'Ej: Comisión Inventario 2026'
            }),

            'resolucion_designacion': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2',
                'placeholder': 'Ej: R.D. N° 012-2026'
            }),

            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2'
            }),

            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded-lg px-3 py-2'
            }),

            'presidente': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2'
            }),

            'vocales': forms.SelectMultiple(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 h-32 overflow-y-auto'
            }),

            'veedor': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2'
            }),
        }

    # ========================================
    # VALIDACIONES PRO
    # ========================================
    def clean(self):
        cleaned_data = super().clean()

        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        presidente = cleaned_data.get('presidente')
        vocales = cleaned_data.get('vocales')

        # ✅ Validar fechas
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError("La fecha fin no puede ser menor que la fecha inicio.")

        # ✅ Validar vocales mínimos
        if vocales and len(vocales) < 2:
            raise ValidationError("Debe seleccionar al menos 2 vocales.")

        # ✅ Presidente no debe repetirse como vocal
        if presidente and vocales:
            if presidente in vocales:
                raise ValidationError("El presidente no puede ser parte de los vocales.")

        return cleaned_data

    # ========================================
    # FILTROS DINÁMICOS
    # ========================================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from apps.usuarios.models import Usuario

        # ✅ Solo usuarios activos ordenados correctamente
        queryset_usuarios = Usuario.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')

        self.fields['presidente'].queryset = queryset_usuarios
        self.fields['vocales'].queryset = queryset_usuarios
        self.fields['veedor'].queryset = queryset_usuarios

        # ✅ Mejora UX
        self.fields['vocales'].help_text = "Seleccione al menos 2 vocales"

# ========================================
# FORM: CARGA CSV INVENTARIO
# ========================================
class CargaCSVForm(forms.Form):

    archivo = forms.FileField(
        label='Subir archivo CSV',
        widget=forms.FileInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2',
            'accept': '.csv'  # ✅ restringe desde navegador
        })
    )

    # ========================================
    # VALIDACIÓN DE ARCHIVO
    # ========================================
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')

        if archivo:
            # ✅ Validar extensión
            if not archivo.name.endswith('.csv'):
                raise ValidationError("El archivo debe ser formato CSV.")

            # ✅ Validar tamaño (máx 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise ValidationError("El archivo no debe superar los 5MB.")

        return archivo
