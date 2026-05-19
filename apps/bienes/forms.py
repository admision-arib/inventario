from apps.bienes.models.sede import Sede
from apps.usuarios.models import Usuario
from apps.bienes.models.movimientos import MovimientoBien
from django import forms
from .models import Bien

class BienForm(forms.ModelForm):

    class Meta:
        model = Bien
        fields = [
            # ✅ IDENTIDAD
            'catalogo',
            'denominacion',

            # ✅ ADQUISICIÓN
            'tipo_doc_adquisicion',
            'tipo_movimiento',
            'tipo_transferencia',

            # ✅ DOCUMENTO
            'numero_documento',
            'valor_documento',
            'fecha_documento',

            # ✅ PECOSA (ALTA)
            'tipo_documento_alta',
            'nro_pecosa',
            'fecha_salida_pecosa',

            # ✅ UBICACIÓN
            'sede',
            'area',

            # ✅ RESPONSABLES
            'usuario_responsable',
            'usuario_asignado',

            # ✅ CARACTERÍSTICAS
            'marca',
            'modelo',
            'numero_serie',

            # ✅ ESTADO
            'estado_conservacion',

            # ✅ OBS
            'observaciones',
        ]

        widgets = {
            'tipo_doc_adquisicion': forms.Select(),
            'tipo_movimiento': forms.Select(attrs={'readonly': 'readonly'}),
            'tipo_transferencia': forms.Select(),
            'fecha_documento': forms.DateInput(attrs={'type': 'date'}),
            'fecha_salida_pecosa': forms.DateInput(attrs={'type': 'date'}),
            'tipo_documento_alta': forms.HiddenInput(),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    # ================= INIT =================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estilo base coherente con la UI moderna (Slate + Indigo)
        base_class = (
            "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm "
            "focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 "
            "transition-colors"
        )

        # Aplicar estilos a todos los campos, excepto al catálogo oculto
        for name, field in self.fields.items():
            if name == 'catalogo':
                continue  # no necesita estilo pues se oculta en el template
            field.widget.attrs.update({'class': base_class})

        # Placeholders informativos
        self.fields['numero_documento'].widget.attrs.update({
            'placeholder': 'OC-001 / NEA-045'
        })
        self.fields['nro_pecosa'].widget.attrs.update({
            'placeholder': 'Ej: 12345'
        })

        # tipo_movimiento se muestra como solo lectura; el valor se fijará en clean()
        self.fields['tipo_movimiento'].widget.attrs['readonly'] = True
        # Eliminamos 'disabled' que impedía el envío del valor

        # Si tipo_documento_alta debe tener un valor fijo, lo establecemos aquí
        self.fields['tipo_documento_alta'].initial = '046'  # descomentado

    # ================= VALIDACIÓN UX =================
    def clean(self):
        cleaned = super().clean()

        tipo = cleaned.get('tipo_doc_adquisicion')
        numero = cleaned.get('numero_documento')
        valor = cleaned.get('valor_documento')
        fecha = cleaned.get('fecha_documento')
        transferencia = cleaned.get('tipo_transferencia')
        movimiento = cleaned.get('tipo_movimiento')

        # Asignar tipo_movimiento según el documento (respaldo si el frontend no lo envió)
        if tipo == '031':
            if movimiento and movimiento != 'COMPRA':
                self.add_error('tipo_movimiento', 'Para compra, el movimiento debe ser COMPRA')
            cleaned['tipo_movimiento'] = 'COMPRA'

            if not numero:
                self.add_error('numero_documento', 'Ingrese número de orden de compra')
            if not valor:
                self.add_error('valor_documento', 'Ingrese valor de compra')
            if not fecha:
                self.add_error('fecha_documento', 'Ingrese fecha de compra')
            if transferencia:
                self.add_error('tipo_transferencia', 'No aplica para compra')

        elif tipo == '045':
            if movimiento and movimiento != 'NEA':
                self.add_error('tipo_movimiento', 'Para NEA, el movimiento debe ser NEA')
            cleaned['tipo_movimiento'] = 'NEA'

            if not numero:
                self.add_error('numero_documento', 'Ingrese número NEA')
            if not valor:
                self.add_error('valor_documento', 'Ingrese valor NEA')
            if not fecha:
                self.add_error('fecha_documento', 'Ingrese fecha NEA')
            if not transferencia:
                self.add_error('tipo_transferencia', 'Seleccione tipo de transferencia')

        else:
            # Tipo de documento no soportado
            self.add_error('tipo_doc_adquisicion', 'Tipo de documento no reconocido (solo 031 o 045)')
            cleaned['tipo_movimiento'] = None  # o dejar sin asignar

        return cleaned



class SedeForm(forms.ModelForm):
    class Meta:
        model = Sede
        fields = ['codigo', 'nombre', 'direccion', 'activo']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Ej: SEDE-01'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm',
                'placeholder': 'Nombre de la sede'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-textarea w-full rounded-md border-gray-300 shadow-sm',
                'rows': 3,
                'placeholder': 'Dirección completa'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-checkbox rounded text-blue-600'
            }),
        }



class MovimientoBienForm(forms.ModelForm):

    class Meta:
        model = MovimientoBien
        fields = [
            'bien',
            'tipo_movimiento',
            'sede_origen',
            'sede_destino',
            'usuario_origen',
            'usuario_destino',
            'documento_autorizacion',
            'observaciones'
        ]

        widgets = {
            'bien': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'tipo_movimiento': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'sede_origen': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'sede_destino': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'usuario_origen': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'usuario_destino': forms.Select(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'documento_autorizacion': forms.TextInput(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'Ej: Memo N° 001-2026'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 3,
                'placeholder': 'Detalle adicional...'
            }),
        }

    # ================= INIT =================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estilo base centralizado (por si en un futuro no se define en Meta)
        base_class = "w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"

        # Aplicar estilos a todos los campos que no tengan ya una clase definida
        for name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = base_class

        # Querysets
        self.fields['bien'].queryset = Bien.objects.all().order_by('denominacion')
        self.fields['sede_origen'].queryset = Sede.objects.all().order_by('nombre')
        self.fields['sede_destino'].queryset = Sede.objects.all().order_by('nombre')

        usuarios = Usuario.objects.filter(is_active=True).order_by('last_name', 'first_name')
        self.fields['usuario_origen'].queryset = usuarios
        self.fields['usuario_destino'].queryset = usuarios

        # Etiquetas personalizadas
        self.fields['bien'].label = "Bien patrimonial"
        self.fields['tipo_movimiento'].label = "Tipo de movimiento"

        # Asegurar que el campo 'bien' no tenga opción vacía (el buscador asigna un ID válido)
        self.fields['bien'].empty_label = None

    # ================= VALIDACIONES =================
    def clean(self):
        cleaned_data = super().clean()

        bien = cleaned_data.get('bien')
        tipo = cleaned_data.get('tipo_movimiento')
        sede_origen = cleaned_data.get('sede_origen')
        sede_destino = cleaned_data.get('sede_destino')
        usuario_destino = cleaned_data.get('usuario_destino')

        # ✅ Validar que se haya seleccionado un bien
        if not bien:
            self.add_error('bien', 'Debe seleccionar un bien patrimonial')

        # ✅ TRANSFERENCIA
        if tipo == 'TRANSFERENCIA':
            if not sede_origen:
                self.add_error('sede_origen', 'Seleccione sede origen')
            if not sede_destino:
                self.add_error('sede_destino', 'Seleccione sede destino')
            if sede_origen and sede_destino and sede_origen == sede_destino:
                self.add_error('sede_destino', 'La sede destino debe ser diferente a la sede origen')

        # ✅ ASIGNACIÓN
        elif tipo == 'ASIGNACION':
            if not usuario_destino:
                self.add_error('usuario_destino', 'Seleccione usuario destino')

        # ✅ PRÉSTAMO
        elif tipo == 'PRESTAMO':
            if not usuario_destino:
                self.add_error('usuario_destino', 'Seleccione usuario')

        # ✅ DEVOLUCIÓN
        elif tipo == 'DEVOLUCION':
            if not sede_destino:
                self.add_error('sede_destino', 'Seleccione sede destino')

        return cleaned_data


