"""
Modelos de catálogos para ToxiClin.
Cada catálogo es una tabla separada con las opciones válidas para ese campo.
Todos heredan de CatalogoBase para compartir los campos comunes.
"""

from django.db import models


# ─────────────────────────────────────────────────────────────────────────────
# Clase base abstracta — todos los catálogos la heredan
# ─────────────────────────────────────────────────────────────────────────────

class CatalogoBase(models.Model):
    """
    Plantilla compartida por todos los catálogos.
    abstract=True significa que Django NO crea tabla para esta clase;
    solo la usa como molde para los catálogos hijos.
    """
    nombre = models.CharField(max_length=200, verbose_name='Nombre')

    # Código numérico del Excel original — sirve para la migración de datos
    codigo = models.IntegerField(
        null=True, blank=True,
        verbose_name='Código (Excel)',
        help_text='Código numérico usado en el Excel anterior'
    )

    # Permite desactivar una opción sin borrarla (para no romper registros viejos)
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        abstract = True
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos simples (ya creados en paso anterior)
# ─────────────────────────────────────────────────────────────────────────────

class CatSexo(CatalogoBase):
    """Sexo biológico del paciente: Masculino, Femenino."""
    class Meta:
        verbose_name = 'Sexo'
        verbose_name_plural = 'Sexo'
        ordering = ['nombre']


class CatSeveridad(CatalogoBase):
    """
    Severidad de la intoxicación según Poisoning Severity Score (IPCS/OMS).
    Asintomático → Leve → Moderada → Severa → Fatal / Sin Relación.
    """
    class Meta:
        verbose_name = 'Severidad'
        verbose_name_plural = 'Severidades'
        ordering = ['codigo']


class CatEvolucion(CatalogoBase):
    """Estado del paciente al cerrar la consulta: Recuperación, Muerte, Secuela..."""
    class Meta:
        verbose_name = 'Evolución'
        verbose_name_plural = 'Evoluciones'
        ordering = ['codigo']


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos de la consulta
# ─────────────────────────────────────────────────────────────────────────────

class CatTipoFrecuencia(CatalogoBase):
    """
    Si es el primer contacto del paciente por esta intoxicación (Por 1ª vez)
    o una consulta posterior por la misma (Ulterior).
    """
    class Meta:
        verbose_name = 'Tipo de frecuencia'
        verbose_name_plural = 'Tipos de frecuencia'
        ordering = ['codigo']


class CatTipoContacto(CatalogoBase):
    """Cómo llegó la consulta al CIAT: presencial o por teléfono."""
    class Meta:
        verbose_name = 'Tipo de contacto'
        verbose_name_plural = 'Tipos de contacto'
        ordering = ['codigo']


class CatMotivoConsulta(CatalogoBase):
    """
    Por qué se consulta al CIAT:
    - Intoxicación: ya hay intoxicación establecida
    - Descartar intoxicación: se sospecha pero no se confirma
    - Asesoramiento: información general, sin paciente intoxicado
    """
    class Meta:
        verbose_name = 'Motivo de consulta'
        verbose_name_plural = 'Motivos de consulta'
        ordering = ['codigo']


class CatSubtipoPresencial(CatalogoBase):
    """
    Solo aplica si el tipo de contacto es presencial.
    Urgencias, Internación, Consultorio Externo, Vía electrónico.
    """
    class Meta:
        verbose_name = 'Subtipo presencial'
        verbose_name_plural = 'Subtipos presenciales'
        ordering = ['codigo']


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos del interlocutor (solo consulta telefónica)
# ─────────────────────────────────────────────────────────────────────────────

class CatCategoriaInterlocutor(CatalogoBase):
    """
    Quién hizo la llamada: personal de salud, familiar del paciente,
    el propio paciente, u otro.
    """
    class Meta:
        verbose_name = 'Categoría de interlocutor'
        verbose_name_plural = 'Categorías de interlocutor'
        ordering = ['codigo']


class CatUbicacionInterlocutor(CatalogoBase):
    """
    Desde dónde llama el interlocutor: hospital, hogar, trabajo, etc.
    """
    class Meta:
        verbose_name = 'Ubicación del interlocutor'
        verbose_name_plural = 'Ubicaciones del interlocutor'
        ordering = ['codigo']


class CatSector(CatalogoBase):
    """
    Sector del establecimiento de salud desde donde se hace la consulta telefónica.
    Público o Privado.
    """
    class Meta:
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectores'
        ordering = ['nombre']


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos de circunstancias (dropdown dependiente: nivel1 → nivel2)
# ─────────────────────────────────────────────────────────────────────────────

class CatCircunstanciaNivel1(CatalogoBase):
    """
    Primer nivel de circunstancias de exposición.
    Valores: No Intencional, Intencional, Reacción Adversa, Desconocido.
    El nivel 2 depende de lo que se seleccione aquí.
    """
    class Meta:
        verbose_name = 'Circunstancia (Nivel 1)'
        verbose_name_plural = 'Circunstancias (Nivel 1)'
        ordering = ['codigo']


class CatCircunstanciaNivel2(CatalogoBase):
    """
    Segundo nivel de circunstancias. Depende del nivel 1 seleccionado.
    Por ejemplo: si nivel1=No Intencional → opciones: Accidental, Ocupacional,
    Ambiental, Alimentaria, Error terapéutico, Mal uso, etc.

    ForeignKey: enlaza cada opción nivel2 con su nivel1 correspondiente.
    on_delete=PROTECT evita borrar un nivel1 que tenga nivel2 asociados.
    """
    nivel1 = models.ForeignKey(
        CatCircunstanciaNivel1,
        on_delete=models.PROTECT,
        verbose_name='Circunstancia Nivel 1',
        related_name='nivel2_opciones'
    )

    class Meta:
        verbose_name = 'Circunstancia (Nivel 2)'
        verbose_name_plural = 'Circunstancias (Nivel 2)'
        ordering = ['nivel1__codigo', 'codigo']

    def __str__(self):
        return f'{self.nivel1.nombre} → {self.nombre}'


# ─────────────────────────────────────────────────────────────────────────────
# Catálogos de la intoxicación
# ─────────────────────────────────────────────────────────────────────────────

class CatUbicacionEvento(CatalogoBase):
    """Dónde ocurrió la exposición: hogar, trabajo, institución de salud, etc."""
    class Meta:
        verbose_name = 'Ubicación del evento'
        verbose_name_plural = 'Ubicaciones del evento'
        ordering = ['codigo']


class CatTipoExposicion(CatalogoBase):
    """
    Duración/patrón de la exposición al agente tóxico.
    Aguda (<24h), Crónica (>24h), Aguda sobre crónica, Desconocida.
    """
    class Meta:
        verbose_name = 'Tipo de exposición'
        verbose_name_plural = 'Tipos de exposición'
        ordering = ['codigo']


class CatTipoAgente(CatalogoBase):
    """
    Clasificación del agente tóxico por uso/origen.
    Medicamento, Plaguicida, Animal, Planta, Droga de abuso, etc.
    """
    class Meta:
        verbose_name = 'Tipo de agente'
        verbose_name_plural = 'Tipos de agente'
        ordering = ['codigo']


class CatViaIngreso(CatalogoBase):
    """
    Cómo entró el tóxico al cuerpo del paciente.
    SELECCIÓN MÚLTIPLE: un paciente puede tener oral + inhalatoria al mismo tiempo.
    """
    class Meta:
        verbose_name = 'Vía de ingreso'
        verbose_name_plural = 'Vías de ingreso'
        ordering = ['codigo']


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo de tratamiento
# ─────────────────────────────────────────────────────────────────────────────

class CatTratamiento(CatalogoBase):
    """
    Opciones de tratamiento. Se usa en DOS columnas:
    - Columna A: tratamiento previo (lo que ya le hicieron antes de llamar al CIAT)
    - Columna B: tratamiento recomendado por el CIAT

    Un mismo tratamiento puede estar marcado en A, en B, o en ambos.
    """
    # Algunos tratamientos tienen un campo para especificar (ej: "Antídoto → cuál?")
    requiere_especificar = models.BooleanField(
        default=False,
        verbose_name='Requiere especificar',
        help_text='Si está activo, el formulario mostrará un campo de texto adicional'
    )

    class Meta:
        verbose_name = 'Tratamiento'
        verbose_name_plural = 'Tratamientos'
        ordering = ['codigo']
