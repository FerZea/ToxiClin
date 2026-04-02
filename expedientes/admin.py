from django.contrib import admin
from expedientes.models import (
    CatSexo, CatSeveridad, CatEvolucion,
    CatTipoFrecuencia, CatTipoContacto, CatMotivoConsulta, CatSubtipoPresencial,
    CatCategoriaInterlocutor, CatUbicacionInterlocutor, CatSector,
    CatCircunstanciaNivel1, CatCircunstanciaNivel2,
    CatUbicacionEvento, CatTipoExposicion, CatTipoAgente,
    CatViaIngreso, CatTratamiento,
    HistoriaClinica, HistoriaClinicaTratamiento,
)


class CatalogoAdmin(admin.ModelAdmin):
    """Configuración base para todos los catálogos simples."""
    list_display = ('nombre', 'codigo', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)
    list_editable = ('activo',)


@admin.register(CatCircunstanciaNivel2)
class CatCircunstanciaNivel2Admin(admin.ModelAdmin):
    """
    Circunstancia nivel 2 tiene columna extra: su nivel 1 padre.
    list_select_related=True evita una consulta SQL extra por cada fila.
    """
    list_display = ('nivel1', 'nombre', 'codigo', 'activo')
    list_filter = ('activo', 'nivel1')
    search_fields = ('nombre',)
    list_editable = ('activo',)
    list_select_related = True


@admin.register(CatTratamiento)
class CatTratamientoAdmin(admin.ModelAdmin):
    """Tratamiento tiene campo extra: requiere_especificar."""
    list_display = ('nombre', 'codigo', 'requiere_especificar', 'activo')
    list_filter = ('activo', 'requiere_especificar')
    search_fields = ('nombre',)
    list_editable = ('activo',)


# Registrar todos los catálogos simples con la configuración base
admin.site.register(CatSexo, CatalogoAdmin)
admin.site.register(CatSeveridad, CatalogoAdmin)
admin.site.register(CatEvolucion, CatalogoAdmin)
admin.site.register(CatTipoFrecuencia, CatalogoAdmin)
admin.site.register(CatTipoContacto, CatalogoAdmin)
admin.site.register(CatMotivoConsulta, CatalogoAdmin)
admin.site.register(CatSubtipoPresencial, CatalogoAdmin)
admin.site.register(CatCategoriaInterlocutor, CatalogoAdmin)
admin.site.register(CatUbicacionInterlocutor, CatalogoAdmin)
admin.site.register(CatSector, CatalogoAdmin)
admin.site.register(CatCircunstanciaNivel1, CatalogoAdmin)
admin.site.register(CatUbicacionEvento, CatalogoAdmin)
admin.site.register(CatTipoExposicion, CatalogoAdmin)
admin.site.register(CatTipoAgente, CatalogoAdmin)
admin.site.register(CatViaIngreso, CatalogoAdmin)

class TratamientoInline(admin.TabularInline):
    """
    Inline: muestra los tratamientos A y B directamente dentro del formulario
    de la historia clínica en el admin, sin tener que ir a otra pantalla.
    TabularInline los muestra en formato de tabla (una fila por tratamiento).
    """
    model = HistoriaClinicaTratamiento
    extra = 0  # No mostrar filas vacías por defecto
    fields = ('tratamiento', 'columna', 'especificar')


@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = (
        'consulta_numero', 'folio_expediente',
        'apellido', 'nombre', 'sexo',
        'tipo_agente', 'severidad', 'fecha_captura'
    )
    list_filter = ('sexo', 'tipo_agente', 'severidad', 'evolucion', 'tipo_contacto')
    search_fields = ('folio_expediente', 'nombre', 'apellido', 'agente_principio_activo')
    list_select_related = True
    readonly_fields = ('consulta_numero', 'edad_valor', 'edad_unidad',
                       'latencia_valor', 'latencia_unidad',
                       'usuario_captura', 'fecha_captura')
    inlines = [TratamientoInline]

    fieldsets = (
        ('Datos del paciente', {
            'fields': (
                'folio_expediente', 'nombre', 'apellido',
                'direccion', 'localidad', 'telefono', 'curp',
                'sexo', 'fecha_nacimiento',
                ('edad_valor', 'edad_unidad'),
                'embarazo_lactancia', 'escolaridad',
                'antecedentes_patologicos', 'medico',
            )
        }),
        ('Datos de la consulta', {
            'fields': (
                'consulta_numero', 'tipo_frecuencia',
                'tipo_contacto', 'motivo_consulta', 'subtipo_presencial',
                'fecha_hora_ingreso', 'fecha_hora_evento_exposicion', 'fecha_hora_consulta',
                ('latencia_valor', 'latencia_unidad'),
            )
        }),
        ('Datos del interlocutor (solo telefónico)', {
            'classes': ('collapse',),  # Colapsado por defecto
            'fields': (
                'interlocutor_nombre', 'interlocutor_categoria',
                'interlocutor_categoria_especificar',
                'interlocutor_ubicacion_nombre', 'interlocutor_ubicacion_tipo',
                'interlocutor_ubicacion_sector',
                'interlocutor_localidad', 'interlocutor_telefono',
            )
        }),
        ('Intoxicación', {
            'fields': (
                'circunstancia_nivel1', 'circunstancia_nivel2', 'circunstancia_otro_texto',
                'ubicacion_evento', 'ubicacion_evento_otro',
                'tipo_exposicion',
                ('duracion_exposicion_valor', 'duracion_exposicion_unidad'),
                'tipo_agente', 'agente_principio_activo', 'agente_cantidad_informada',
                'vias_ingreso', 'via_ingreso_otra_especificar',
            )
        }),
        ('Clínica', {
            'fields': (
                'signos_sintomas',
                ('fc', 'fr', 'temp', 'sat', 'ta'),
                'severidad', 'estudios_solicitados',
            )
        }),
        ('Tratamiento', {
            'fields': ('tratamiento_notas',)
        }),
        ('Evolución', {
            'fields': (
                'evolucion',
                ('hospitalizacion_sala_general', 'hospitalizacion_uci_uti', 'hospitalizacion_urgencias'),
                ('hospitalizacion_dias', 'hospitalizacion_responsable'),
                'comentario', 'firma_responsable',
            )
        }),
        ('Auditoría', {
            'fields': ('usuario_captura', 'fecha_captura')
        }),
    )


# Personalizar títulos del admin
admin.site.site_header = 'ToxiClin — Administración'
admin.site.site_title = 'ToxiClin'
admin.site.index_title = 'Panel de Administración'
