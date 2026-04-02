"""
Formulario de filtros para el listado de historias clínicas.
Todos los campos son opcionales — solo filtra por los que se llenen.
"""

from django import forms
from expedientes.models import (
    CatSexo, CatTipoContacto, CatMotivoConsulta,
    CatCircunstanciaNivel1, CatTipoAgente, CatSeveridad, CatEvolucion,
    CatViaIngreso,
)


class FiltroHistoriaForm(forms.Form):
    """
    Formulario de búsqueda y filtrado.
    No hereda de ModelForm porque no guarda datos — solo consulta.
    """

    # ── Búsqueda textual ──────────────────────────────────────────────────
    folio = forms.CharField(
        required=False,
        label='Folio / Expediente',
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por folio...'}),
    )
    paciente = forms.CharField(
        required=False,
        label='Nombre del paciente',
        widget=forms.TextInput(attrs={'placeholder': 'Nombre o apellido...'}),
    )
    agente = forms.CharField(
        required=False,
        label='Agente tóxico',
        widget=forms.TextInput(attrs={'placeholder': 'Principio activo o nombre comercial...'}),
    )

    # ── Filtros por catálogo ──────────────────────────────────────────────
    sexo = forms.ModelChoiceField(
        queryset=CatSexo.objects.filter(activo=True),
        required=False,
        label='Sexo',
        empty_label='— Todos —',
    )
    tipo_contacto = forms.ModelChoiceField(
        queryset=CatTipoContacto.objects.filter(activo=True),
        required=False,
        label='Tipo de contacto',
        empty_label='— Todos —',
    )
    motivo_consulta = forms.ModelChoiceField(
        queryset=CatMotivoConsulta.objects.filter(activo=True),
        required=False,
        label='Motivo de consulta',
        empty_label='— Todos —',
    )
    circunstancia = forms.ModelChoiceField(
        queryset=CatCircunstanciaNivel1.objects.filter(activo=True),
        required=False,
        label='Circunstancia',
        empty_label='— Todas —',
    )
    tipo_agente = forms.ModelChoiceField(
        queryset=CatTipoAgente.objects.filter(activo=True),
        required=False,
        label='Tipo de agente',
        empty_label='— Todos —',
    )
    severidad = forms.ModelChoiceField(
        queryset=CatSeveridad.objects.filter(activo=True),
        required=False,
        label='Severidad',
        empty_label='— Todas —',
    )
    evolucion = forms.ModelChoiceField(
        queryset=CatEvolucion.objects.filter(activo=True),
        required=False,
        label='Evolución',
        empty_label='— Todas —',
    )
    via_ingreso = forms.ModelChoiceField(
        queryset=CatViaIngreso.objects.filter(activo=True),
        required=False,
        label='Vía de ingreso',
        empty_label='— Todas —',
    )

    # ── Rango de fechas ───────────────────────────────────────────────────
    fecha_desde = forms.DateField(
        required=False,
        label='Fecha desde',
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    fecha_hasta = forms.DateField(
        required=False,
        label='Fecha hasta',
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )

    # ── Rango de edad ─────────────────────────────────────────────────────
    # Se filtra sobre edad_valor en años para simplificar.
    # Menores de 1 año aparecen si se pone 0 en alguno de los campos.
    edad_min = forms.IntegerField(
        required=False,
        label='Edad mínima (años)',
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'ej: 5', 'min': 0}),
    )
    edad_max = forms.IntegerField(
        required=False,
        label='Edad máxima (años)',
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'ej: 18', 'min': 0}),
    )
