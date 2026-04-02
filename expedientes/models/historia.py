"""
Modelo principal: HistoriaClinica
Replica la ficha CIAT/REDARTOX completa.
"""

from django.db import models
from django.contrib.auth.models import User
from expedientes.models.catalogos import (
    CatSexo, CatSeveridad, CatEvolucion,
    CatTipoFrecuencia, CatTipoContacto, CatMotivoConsulta, CatSubtipoPresencial,
    CatCategoriaInterlocutor, CatUbicacionInterlocutor, CatSector,
    CatCircunstanciaNivel1, CatCircunstanciaNivel2,
    CatUbicacionEvento, CatTipoExposicion, CatTipoAgente,
    CatViaIngreso, CatTratamiento,
)


# Opciones para campos de unidad (edad, latencia, duración)
UNIDAD_EDAD = [
    ('d', 'Días'),
    ('m', 'Meses'),
    ('a', 'Años'),
]

UNIDAD_TIEMPO = [
    ('mi',   'Minutos'),
    ('hr',   'Horas'),
    ('di',   'Días'),
    ('ms',   'Meses'),
    ('a',    'Años'),
    ('desc', 'Desconocida'),
]

COLUMNA_TRATAMIENTO = [
    ('A', 'Previo (A)'),
    ('B', 'Recomendado (B)'),
]


# ─────────────────────────────────────────────────────────────────────────────
# Tabla intermedia para tratamiento A/B
# ─────────────────────────────────────────────────────────────────────────────

class HistoriaClinicaTratamiento(models.Model):
    """
    Tabla intermedia entre HistoriaClinica y CatTratamiento.
    Necesaria porque la relación no es un simple ManyToMany:
    cada tratamiento tiene además una columna (A=previo, B=recomendado)
    y opcionalmente un texto de especificación (ej: "Antídoto → Naloxona").

    Se usa 'through' en el ManyToManyField de HistoriaClinica para indicar
    que Django debe usar esta tabla en lugar de crear una automáticamente.
    """
    historia = models.ForeignKey(
        'HistoriaClinica',
        on_delete=models.CASCADE,
        related_name='tratamientos_detalle'
    )
    tratamiento = models.ForeignKey(
        CatTratamiento,
        on_delete=models.PROTECT,
        verbose_name='Tratamiento'
    )
    # Columna A = lo que ya le hicieron antes de llegar al CIAT
    # Columna B = lo que el CIAT recomienda
    columna = models.CharField(
        max_length=1,
        choices=COLUMNA_TRATAMIENTO,
        verbose_name='Columna'
    )
    # Solo para tratamientos que requieren especificar (antídoto, fármaco, etc.)
    especificar = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Especificar'
    )

    class Meta:
        verbose_name = 'Tratamiento de historia'
        verbose_name_plural = 'Tratamientos de historia'
        # Un mismo tratamiento no puede repetirse en la misma columna
        unique_together = ('historia', 'tratamiento', 'columna')

    def __str__(self):
        return f'{self.get_columna_display()} — {self.tratamiento.nombre}'


# ─────────────────────────────────────────────────────────────────────────────
# Modelo principal
# ─────────────────────────────────────────────────────────────────────────────

class HistoriaClinica(models.Model):
    """
    Historia clínica toxicológica — replica la ficha CIAT/REDARTOX completa.
    Una historia = una consulta al CIAT por una exposición/intoxicación.
    """

    # ── Datos del paciente ────────────────────────────────────────────────

    # Obligatorio — vincula con el expediente físico del hospital
    folio_expediente = models.CharField(
        max_length=50,
        verbose_name='Folio / N° Expediente',
        db_index=True  # Índice para búsqueda rápida por folio
    )
    nombre = models.CharField(max_length=100, verbose_name='Nombre(s)')
    apellido = models.CharField(max_length=100, verbose_name='Apellidos')
    direccion = models.CharField(
        max_length=300, blank=True,
        verbose_name='Dirección'
    )
    localidad = models.CharField(
        max_length=150, blank=True,
        verbose_name='Localidad'
    )
    telefono = models.CharField(
        max_length=20, blank=True,
        verbose_name='Teléfono'
    )
    curp = models.CharField(
        max_length=18, blank=True,
        verbose_name='CURP'
    )

    # ForeignKey: enlaza con el catálogo CatSexo.
    # on_delete=PROTECT evita borrar un sexo que tenga historias asociadas.
    # null/blank=True permite guardar sin sexo (aunque el formulario lo pedirá).
    sexo = models.ForeignKey(
        CatSexo,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Sexo'
    )

    # DateField: solo fecha (sin hora). El sistema calcula la edad desde aquí.
    fecha_nacimiento = models.DateField(
        null=True, blank=True,
        verbose_name='Fecha de nacimiento'
    )

    # Edad calculada automáticamente — se llena al guardar, no en el formulario
    edad_valor = models.IntegerField(
        null=True, blank=True,
        verbose_name='Edad (valor)'
    )
    edad_unidad = models.CharField(
        max_length=1,
        choices=UNIDAD_EDAD,
        blank=True,
        verbose_name='Edad (unidad)'
    )

    # Solo habilitado en formulario si sexo = Femenino
    embarazo_lactancia = models.BooleanField(
        null=True, blank=True,
        verbose_name='Embarazo / Lactancia'
    )

    escolaridad = models.CharField(
        max_length=100, blank=True,
        verbose_name='Escolaridad'
    )
    antecedentes_patologicos = models.TextField(
        blank=True,
        verbose_name='Antecedentes patológicos personales'
    )
    medico = models.CharField(
        max_length=150, blank=True,
        verbose_name='Médico que atiende'
    )

    # ── Datos de la consulta ──────────────────────────────────────────────

    # AutoField automático — no se captura en el formulario
    consulta_numero = models.PositiveIntegerField(
        unique=True,
        verbose_name='Consulta N°'
    )

    tipo_frecuencia = models.ForeignKey(
        CatTipoFrecuencia,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Tipo de frecuencia'
    )
    tipo_contacto = models.ForeignKey(
        CatTipoContacto,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Tipo de contacto'
    )
    motivo_consulta = models.ForeignKey(
        CatMotivoConsulta,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Motivo de consulta'
    )
    # Solo aplica si tipo_contacto = presencial
    subtipo_presencial = models.ForeignKey(
        CatSubtipoPresencial,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Subtipo presencial'
    )

    # DateTimeField: fecha + hora
    fecha_hora_ingreso = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha y hora de ingreso'
    )
    fecha_hora_evento_exposicion = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha y hora del evento/exposición'
    )
    fecha_hora_consulta = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha y hora de consulta'
    )

    # Latencia calculada automáticamente (exposición → ingreso/consulta)
    latencia_valor = models.IntegerField(
        null=True, blank=True,
        verbose_name='Latencia (valor)'
    )
    latencia_unidad = models.CharField(
        max_length=4,
        choices=UNIDAD_TIEMPO,
        blank=True,
        verbose_name='Latencia (unidad)'
    )

    # ── Datos del interlocutor (solo consulta telefónica) ─────────────────

    interlocutor_nombre = models.CharField(
        max_length=150, blank=True,
        verbose_name='Nombre del interlocutor'
    )
    interlocutor_categoria = models.ForeignKey(
        CatCategoriaInterlocutor,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Categoría del interlocutor'
    )
    interlocutor_categoria_especificar = models.CharField(
        max_length=200, blank=True,
        verbose_name='Categoría interlocutor (especificar)'
    )
    interlocutor_ubicacion_nombre = models.CharField(
        max_length=200, blank=True,
        verbose_name='Establecimiento del interlocutor'
    )
    interlocutor_ubicacion_tipo = models.ForeignKey(
        CatUbicacionInterlocutor,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Tipo de establecimiento'
    )
    interlocutor_ubicacion_sector = models.ForeignKey(
        CatSector,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Sector'
    )
    interlocutor_localidad = models.CharField(
        max_length=150, blank=True,
        verbose_name='Localidad del interlocutor'
    )
    interlocutor_telefono = models.CharField(
        max_length=20, blank=True,
        verbose_name='Teléfono del interlocutor'
    )

    # ── Circunstancias de la exposición ───────────────────────────────────

    circunstancia_nivel1 = models.ForeignKey(
        CatCircunstanciaNivel1,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Circunstancia (Nivel 1)'
    )
    circunstancia_nivel2 = models.ForeignKey(
        CatCircunstanciaNivel2,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Circunstancia (Nivel 2)'
    )
    circunstancia_otro_texto = models.CharField(
        max_length=300, blank=True,
        verbose_name='Circunstancia (especificar)'
    )

    # ── Ubicación y tipo de exposición ────────────────────────────────────

    ubicacion_evento = models.ForeignKey(
        CatUbicacionEvento,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Ubicación del evento'
    )
    ubicacion_evento_otro = models.CharField(
        max_length=200, blank=True,
        verbose_name='Ubicación del evento (especificar)'
    )
    tipo_exposicion = models.ForeignKey(
        CatTipoExposicion,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Tipo de exposición'
    )
    duracion_exposicion_valor = models.IntegerField(
        null=True, blank=True,
        verbose_name='Duración de exposición (valor)'
    )
    duracion_exposicion_unidad = models.CharField(
        max_length=4,
        choices=UNIDAD_TIEMPO,
        blank=True,
        verbose_name='Duración de exposición (unidad)'
    )

    # ── Agente tóxico ─────────────────────────────────────────────────────

    tipo_agente = models.ForeignKey(
        CatTipoAgente,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Tipo de agente'
    )
    # Texto libre: principio activo, nombre comercial, nombre científico
    agente_principio_activo = models.CharField(
        max_length=300, blank=True,
        verbose_name='Agente (principio activo / nombre comercial)',
        db_index=True  # Índice para búsqueda por agente
    )
    agente_cantidad_informada = models.CharField(
        max_length=200, blank=True,
        verbose_name='Cantidad informada'
    )

    # ── Vía de ingreso (selección MÚLTIPLE) ───────────────────────────────
    # ManyToManyField: una historia puede tener oral + inhalatoria + ocular, etc.
    vias_ingreso = models.ManyToManyField(
        CatViaIngreso,
        blank=True,
        verbose_name='Vías de ingreso'
    )
    via_ingreso_otra_especificar = models.CharField(
        max_length=200, blank=True,
        verbose_name='Vía de ingreso (especificar)'
    )

    # ── Signos y síntomas ─────────────────────────────────────────────────

    signos_sintomas = models.TextField(
        blank=True,
        verbose_name='Signos y síntomas'
    )

    # Signos vitales — todos opcionales (puede no estar disponibles en telefónico)
    fc   = models.IntegerField(null=True, blank=True, verbose_name='FC (lpm)')
    fr   = models.IntegerField(null=True, blank=True, verbose_name='FR (rpm)')
    
    # DecimalField: número con decimales (ej: 37.5 °C)
    temp = models.DecimalField(
        max_digits=4, decimal_places=1,
        null=True, blank=True,
        verbose_name='Temperatura (°C)'
    )
    sat  = models.IntegerField(null=True, blank=True, verbose_name='SatO2 (%)')
    ta   = models.CharField(
        max_length=20, blank=True,
        verbose_name='TA (mmHg)',
        help_text='Formato: sistólica/diastólica (ej: 120/80)'
    )

    severidad = models.ForeignKey(
        CatSeveridad,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Severidad'
    )
    estudios_solicitados = models.TextField(
        blank=True,
        verbose_name='Estudios solicitados'
    )

    # ── Tratamiento A y B (ManyToMany con tabla intermedia) ───────────────
    # 'through' le dice a Django que use HistoriaClinicaTratamiento
    # en lugar de crear una tabla automática simple.
    tratamientos = models.ManyToManyField(
        CatTratamiento,
        through=HistoriaClinicaTratamiento,
        blank=True,
        verbose_name='Tratamientos'
    )
    tratamiento_notas = models.TextField(
        blank=True,
        verbose_name='Notas de tratamiento'
    )

    # ── Evolución y hospitalización ───────────────────────────────────────

    evolucion = models.ForeignKey(
        CatEvolucion,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Evolución'
    )
    # Hospitalización: selección múltiple con 3 checkboxes independientes
    hospitalizacion_sala_general = models.BooleanField(
        default=False,
        verbose_name='Hospitalización: Sala General'
    )
    hospitalizacion_uci_uti = models.BooleanField(
        default=False,
        verbose_name='Hospitalización: UCI / UTI'
    )
    hospitalizacion_urgencias = models.BooleanField(
        default=False,
        verbose_name='Hospitalización: Urgencias'
    )
    hospitalizacion_dias = models.IntegerField(
        null=True, blank=True,
        verbose_name='Días de hospitalización'
    )
    hospitalizacion_responsable = models.CharField(
        max_length=150, blank=True,
        verbose_name='Responsable de hospitalización'
    )

    comentario = models.TextField(
        blank=True,
        verbose_name='Comentario'
    )
    firma_responsable = models.CharField(
        max_length=150, blank=True,
        verbose_name='Firma del responsable'
    )

    # ── Auditoría (automáticos — no aparecen en el formulario) ───────────

    # ForeignKey a User de Django — se llena con request.user al guardar
    usuario_captura = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True, blank=True,
        verbose_name='Capturado por',
        related_name='historias_capturadas'
    )
    # auto_now_add=True: se pone la fecha/hora actual solo al crear, nunca al editar
    fecha_captura = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de captura'
    )

    class Meta:
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'
        ordering = ['-fecha_captura']  # Las más recientes primero

    def __str__(self):
        return f'#{self.consulta_numero} — {self.apellido}, {self.nombre} ({self.folio_expediente})'

    def save(self, *args, **kwargs):
        # Asignar número de consulta automáticamente si es nueva
        if not self.pk and not self.consulta_numero:
            ultimo = HistoriaClinica.objects.order_by('-consulta_numero').first()
            self.consulta_numero = (ultimo.consulta_numero + 1) if ultimo else 1

        # Calcular edad desde fecha_nacimiento y fecha del evento
        if self.fecha_nacimiento and self.fecha_hora_consulta:
            self._calcular_edad()

        # Calcular latencia desde exposición hasta consulta/ingreso
        self._calcular_latencia()

        super().save(*args, **kwargs)

    def _calcular_edad(self):
        """
        Calcula la edad en días, meses o años según la fecha de nacimiento
        y la fecha de la consulta. Sigue las reglas REDARTOX:
        - < 1 mes  → días
        - < 1 año  → meses
        - >= 1 año → años
        """
        from datetime import date

        # fecha_hora_consulta es datetime; tomamos solo la fecha
        fecha_evento = self.fecha_hora_consulta.date()
        nacimiento   = self.fecha_nacimiento

        delta_dias = (fecha_evento - nacimiento).days

        if delta_dias < 30:
            self.edad_valor = delta_dias
            self.edad_unidad = 'd'
        elif delta_dias < 365:
            self.edad_valor = delta_dias // 30
            self.edad_unidad = 'm'
        else:
            # Cálculo exacto de años cumplidos
            anios = fecha_evento.year - nacimiento.year
            if (fecha_evento.month, fecha_evento.day) < (nacimiento.month, nacimiento.day):
                anios -= 1
            self.edad_valor = anios
            self.edad_unidad = 'a'

    def _calcular_latencia(self):
        """
        Calcula la diferencia entre la exposición y el primer contacto con el CIAT.
        - Presencial: desde exposición hasta ingreso al hospital
        - Telefónico:  desde exposición hasta la consulta
        Si no hay fecha de exposición, latencia = desconocida.
        """
        if not self.fecha_hora_evento_exposicion:
            self.latencia_unidad = 'desc'
            return

        # Determinar el momento de referencia según tipo de contacto
        referencia = self.fecha_hora_ingreso or self.fecha_hora_consulta
        if not referencia:
            return

        delta = referencia - self.fecha_hora_evento_exposicion
        minutos_totales = int(delta.total_seconds() / 60)

        if minutos_totales < 60:
            self.latencia_valor = minutos_totales
            self.latencia_unidad = 'mi'
        elif minutos_totales < 1440:       # < 24 horas
            self.latencia_valor = minutos_totales // 60
            self.latencia_unidad = 'hr'
        elif minutos_totales < 43200:      # < 30 días
            self.latencia_valor = minutos_totales // 1440
            self.latencia_unidad = 'di'
        elif minutos_totales < 525600:     # < 365 días
            self.latencia_valor = minutos_totales // 43200
            self.latencia_unidad = 'ms'
        else:
            self.latencia_valor = minutos_totales // 525600
            self.latencia_unidad = 'a'
