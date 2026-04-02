"""
Formulario de captura de historia clínica.
Replica la ficha CIAT/REDARTOX en el mismo orden visual que el papel.
"""

from django import forms
from expedientes.models import (
    HistoriaClinica,
    CatSexo, CatTipoFrecuencia, CatTipoContacto, CatMotivoConsulta,
    CatSubtipoPresencial, CatCategoriaInterlocutor, CatUbicacionInterlocutor,
    CatSector, CatCircunstanciaNivel1, CatCircunstanciaNivel2,
    CatUbicacionEvento, CatTipoExposicion, CatTipoAgente,
    CatViaIngreso, CatSeveridad, CatTratamiento, CatEvolucion,
)

# Opciones de unidad de tiempo para duración de exposición
UNIDAD_TIEMPO_OPCIONES = [
    ('', '— Unidad —'),
    ('mi', 'Minutos'),
    ('hr', 'Horas'),
    ('di', 'Días'),
    ('ms', 'Meses'),
    ('a',  'Años'),
    ('desc', 'Desconocida'),
]


class HistoriaClinicaForm(forms.ModelForm):
    """
    ModelForm: Django genera automáticamente los campos a partir del modelo.
    Solo sobreescribimos los campos que necesitan configuración especial
    (widgets, etiquetas, validaciones, etc.).
    """

    # ── Campos extra que no están en el modelo directamente ──────────────

    # Tratamientos previos (columna A) — checkboxes múltiples
    tratamiento_a = forms.ModelMultipleChoiceField(
        queryset=CatTratamiento.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Tratamiento previo (A)',
    )
    # Especificaciones de tratamiento A (para los que requieren texto)
    tratamiento_a_especificar = forms.CharField(
        required=False,
        label='Especificar tratamiento A',
        widget=forms.TextInput(attrs={'placeholder': 'Antídoto, fármaco, especialista...'}),
    )

    # Tratamientos recomendados (columna B) — checkboxes múltiples
    tratamiento_b = forms.ModelMultipleChoiceField(
        queryset=CatTratamiento.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Tratamiento recomendado (B)',
    )
    tratamiento_b_especificar = forms.CharField(
        required=False,
        label='Especificar tratamiento B',
        widget=forms.TextInput(attrs={'placeholder': 'Antídoto, fármaco, especialista...'}),
    )

    class Meta:
        model = HistoriaClinica
        # Excluimos los campos calculados y de auditoría — se llenan automáticamente
        exclude = [
            'consulta_numero',
            'edad_valor', 'edad_unidad',
            'latencia_valor', 'latencia_unidad',
            'tratamientos',               # Se maneja con tratamiento_a y tratamiento_b
            'usuario_captura', 'fecha_captura',
        ]
        widgets = {
            # ── Paciente ──
            'folio_expediente': forms.TextInput(attrs={
                'placeholder': 'N° de expediente hospitalario',
                'autofocus': True,
            }),
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre(s)'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Apellidos'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Calle, número, colonia'}),
            'localidad': forms.TextInput(attrs={'placeholder': 'Ciudad o municipio'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono de contacto'}),
            'curp': forms.TextInput(attrs={
                'placeholder': 'CURP (opcional)',
                'maxlength': '18',
                'style': 'text-transform: uppercase',
            }),
            # DateInput: muestra un selector de fecha en el navegador
            'fecha_nacimiento': forms.DateInput(attrs={
                'type': 'date',
            }, format='%Y-%m-%d'),
            'escolaridad': forms.TextInput(attrs={'placeholder': 'Último año aprobado'}),
            'antecedentes_patologicos': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Enfermedades previas relevantes',
            }),
            'medico': forms.TextInput(attrs={'placeholder': 'Nombre del médico tratante'}),

            # ── Consulta ──
            'fecha_hora_ingreso': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'fecha_hora_evento_exposicion': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'fecha_hora_consulta': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),

            # ── Interlocutor ──
            'interlocutor_nombre': forms.TextInput(attrs={'placeholder': 'Nombre completo'}),
            'interlocutor_categoria_especificar': forms.TextInput(attrs={
                'placeholder': 'Especificar categoría',
            }),
            'interlocutor_ubicacion_nombre': forms.TextInput(attrs={
                'placeholder': 'Nombre del hospital, clínica, etc.',
            }),
            'interlocutor_localidad': forms.TextInput(attrs={'placeholder': 'Ciudad o municipio'}),
            'interlocutor_telefono': forms.TextInput(attrs={'placeholder': 'Teléfono'}),

            # ── Circunstancias / intoxicación ──
            'circunstancia_otro_texto': forms.TextInput(attrs={'placeholder': 'Especificar'}),
            'ubicacion_evento_otro': forms.TextInput(attrs={'placeholder': 'Especificar'}),
            'duracion_exposicion_valor': forms.NumberInput(attrs={
                'min': 0, 'placeholder': 'Número',
            }),
            'agente_principio_activo': forms.TextInput(attrs={
                'placeholder': 'Principio activo, nombre comercial o científico',
                'autocomplete': 'off',
            }),
            'agente_cantidad_informada': forms.TextInput(attrs={
                'placeholder': 'ej: 10 comprimidos, 500 ml',
            }),

            # ── Clínica ──
            'signos_sintomas': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Signos y síntomas referidos por el paciente o interlocutor',
            }),
            'fc':   forms.NumberInput(attrs={'min': 0, 'max': 300, 'placeholder': 'lpm'}),
            'fr':   forms.NumberInput(attrs={'min': 0, 'max': 100, 'placeholder': 'rpm'}),
            'temp': forms.NumberInput(attrs={'min': 25, 'max': 45,  'placeholder': '°C', 'step': '0.1'}),
            'sat':  forms.NumberInput(attrs={'min': 0, 'max': 100, 'placeholder': '%'}),
            'ta':   forms.TextInput(attrs={'placeholder': 'ej: 120/80'}),
            'estudios_solicitados': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Laboratorio, radiológicos, etc.',
            }),

            # ── Tratamiento ──
            'tratamiento_notas': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Indicaciones relevantes de tratamiento',
            }),

            # ── Evolución ──
            'hospitalizacion_dias': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Días'}),
            'hospitalizacion_responsable': forms.TextInput(attrs={
                'placeholder': 'Nombre del responsable',
            }),
            'comentario': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Menciones o consideraciones adicionales',
            }),
            'firma_responsable': forms.TextInput(attrs={
                'placeholder': 'Nombre del profesional responsable',
            }),

            # ── Vía de ingreso (selección múltiple con checkboxes) ──
            'vias_ingreso': forms.CheckboxSelectMultiple,
            'via_ingreso_otra_especificar': forms.TextInput(attrs={'placeholder': 'Especificar'}),
        }
        labels = {
            'folio_expediente':        'N° Folio / Expediente *',
            'nombre':                  'Nombre(s)',
            'apellido':                'Apellidos',
            'direccion':               'Dirección',
            'localidad':               'Localidad',
            'telefono':                'Teléfono',
            'curp':                    'CURP',
            'sexo':                    'Sexo',
            'fecha_nacimiento':        'Fecha de nacimiento',
            'embarazo_lactancia':      'Embarazo / Lactancia',
            'escolaridad':             'Escolaridad',
            'antecedentes_patologicos': 'Antecedentes patológicos',
            'medico':                  'Médico que atiende',
            'tipo_frecuencia':         'Tipo de frecuencia',
            'tipo_contacto':           'Tipo de contacto *',
            'motivo_consulta':         'Motivo de consulta *',
            'subtipo_presencial':      'Subtipo (presencial)',
            'fecha_hora_ingreso':      'Fecha y hora de ingreso',
            'fecha_hora_evento_exposicion': 'Fecha y hora del evento/exposición',
            'fecha_hora_consulta':     'Fecha y hora de consulta *',
            'circunstancia_nivel1':    'Circunstancia (Nivel 1)',
            'circunstancia_nivel2':    'Circunstancia (Nivel 2)',
            'circunstancia_otro_texto': 'Especificar circunstancia',
            'ubicacion_evento':        'Ubicación del evento',
            'ubicacion_evento_otro':   'Especificar ubicación',
            'tipo_exposicion':         'Tipo de exposición',
            'duracion_exposicion_valor': 'Duración de exposición',
            'duracion_exposicion_unidad': 'Unidad',
            'tipo_agente':             'Tipo de agente',
            'agente_principio_activo': 'Agente (principio activo / nombre comercial)',
            'agente_cantidad_informada': 'Cantidad informada',
            'vias_ingreso':            'Vía(s) de ingreso',
            'via_ingreso_otra_especificar': 'Especificar vía',
            'signos_sintomas':         'Signos y síntomas',
            'fc':   'FC (lpm)',
            'fr':   'FR (rpm)',
            'temp': 'Temperatura (°C)',
            'sat':  'SatO₂ (%)',
            'ta':   'TA (mmHg)',
            'severidad':               'Severidad inicial / mayor',
            'estudios_solicitados':    'Estudios solicitados',
            'tratamiento_notas':       'Notas de tratamiento',
            'evolucion':               'Evolución',
            'hospitalizacion_sala_general': 'Sala General',
            'hospitalizacion_uci_uti': 'UCI / UTI',
            'hospitalizacion_urgencias': 'Urgencias',
            'hospitalizacion_dias':    'Días de hospitalización',
            'hospitalizacion_responsable': 'Responsable',
            'comentario':              'Comentario',
            'firma_responsable':       'Firma del responsable',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrar solo catálogos activos en todos los dropdowns
        for field_name, field in self.fields.items():
            if hasattr(field, 'queryset'):
                if hasattr(field.queryset.model, 'activo'):
                    field.queryset = field.queryset.filter(activo=True)

        # Agregar opción vacía "— Seleccionar —" a todos los dropdowns
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.empty_label = '— Seleccionar —'

        # Nivel 2 empieza vacío — se llena con JavaScript según nivel 1
        self.fields['circunstancia_nivel2'].queryset = CatCircunstanciaNivel2.objects.none()

        # Si estamos editando un registro existente, cargar el nivel 2 correcto
        if self.instance.pk and self.instance.circunstancia_nivel1:
            self.fields['circunstancia_nivel2'].queryset = (
                CatCircunstanciaNivel2.objects
                .filter(nivel1=self.instance.circunstancia_nivel1, activo=True)
            )
        # Si el formulario fue enviado con nivel1 seleccionado
        elif 'circunstancia_nivel1' in self.data:
            try:
                nivel1_id = int(self.data.get('circunstancia_nivel1'))
                self.fields['circunstancia_nivel2'].queryset = (
                    CatCircunstanciaNivel2.objects
                    .filter(nivel1_id=nivel1_id, activo=True)
                )
            except (ValueError, TypeError):
                pass

        # folio_expediente es obligatorio
        self.fields['folio_expediente'].required = True
        self.fields['fecha_hora_consulta'].required = True
        self.fields['tipo_contacto'].required = True
        self.fields['motivo_consulta'].required = True

    def clean(self):
        """
        Validaciones cruzadas entre campos.
        clean() se ejecuta después de validar cada campo individual.
        """
        cleaned = super().clean()
        tipo_contacto  = cleaned.get('tipo_contacto')
        subtipo        = cleaned.get('subtipo_presencial')
        fecha_ingreso  = cleaned.get('fecha_hora_ingreso')
        fecha_consulta = cleaned.get('fecha_hora_consulta')
        fecha_evento   = cleaned.get('fecha_hora_evento_exposicion')

        # Si es presencial, la fecha de ingreso es obligatoria
        if tipo_contacto and tipo_contacto.nombre == 'Exposición (presencial)':
            if not fecha_ingreso:
                self.add_error(
                    'fecha_hora_ingreso',
                    'La fecha de ingreso es obligatoria para consultas presenciales.'
                )

        # La fecha de exposición no puede ser posterior a la consulta
        if fecha_evento and fecha_consulta:
            if fecha_evento > fecha_consulta:
                self.add_error(
                    'fecha_hora_evento_exposicion',
                    'La fecha de exposición no puede ser posterior a la fecha de consulta.'
                )

        return cleaned
