"""
Comando de gestión: cargar_catalogos
Uso: python manage.py cargar_catalogos

Carga todos los valores iniciales de los catálogos basados en la ficha CIAT/REDARTOX.
Es seguro ejecutarlo varias veces — usa get_or_create para no duplicar registros.
"""

from django.core.management.base import BaseCommand
from expedientes.models import (
    CatSexo, CatSeveridad, CatEvolucion,
    CatTipoFrecuencia, CatTipoContacto, CatMotivoConsulta, CatSubtipoPresencial,
    CatCategoriaInterlocutor, CatUbicacionInterlocutor, CatSector,
    CatCircunstanciaNivel1, CatCircunstanciaNivel2,
    CatUbicacionEvento, CatTipoExposicion, CatTipoAgente,
    CatViaIngreso, CatTratamiento,
)


class Command(BaseCommand):
    help = 'Carga los catálogos iniciales de la ficha CIAT/REDARTOX'

    def handle(self, *args, **options):
        self.stdout.write('Cargando catálogos...\n')

        self._cargar_sexo()
        self._cargar_severidad()
        self._cargar_evolucion()
        self._cargar_tipo_frecuencia()
        self._cargar_tipo_contacto()
        self._cargar_motivo_consulta()
        self._cargar_subtipo_presencial()
        self._cargar_categoria_interlocutor()
        self._cargar_ubicacion_interlocutor()
        self._cargar_sector()
        self._cargar_circunstancias()
        self._cargar_ubicacion_evento()
        self._cargar_tipo_exposicion()
        self._cargar_tipo_agente()
        self._cargar_via_ingreso()
        self._cargar_tratamiento()

        self.stdout.write(self.style.SUCCESS('\n¡Catálogos cargados correctamente!'))

    # ─────────────────────────────────────────────────────────────────────
    # Métodos privados — uno por catálogo
    # ─────────────────────────────────────────────────────────────────────

    def _cargar(self, modelo, datos, campo_extra=None):
        """
        Método auxiliar: crea registros si no existen.
        datos: lista de tuplas (codigo, nombre) o (codigo, nombre, extra)
        """
        creados = 0
        for fila in datos:
            codigo, nombre = fila[0], fila[1]
            defaults = {'codigo': codigo}
            if campo_extra and len(fila) > 2:
                defaults[campo_extra] = fila[2]
            _, nuevo = modelo.objects.get_or_create(nombre=nombre, defaults=defaults)
            if nuevo:
                creados += 1
        nombre_modelo = modelo._meta.verbose_name_plural
        self.stdout.write(f'  {nombre_modelo}: {creados} nuevos registros')

    def _cargar_sexo(self):
        self._cargar(CatSexo, [
            (1, 'Masculino'),
            (0, 'Femenino'),
        ])

    def _cargar_severidad(self):
        self._cargar(CatSeveridad, [
            (0, 'Asintomático'),
            (1, 'Leve'),
            (2, 'Moderada'),
            (3, 'Severa'),
            (4, 'Fatal'),
            (5, 'Sin Relación'),
        ])

    def _cargar_evolucion(self):
        self._cargar(CatEvolucion, [
            (1, 'Recuperación'),
            (2, 'Recuperación retardada'),
            (3, 'Muerte'),
            (4, 'Secuela'),
            (5, 'Desconocida'),
        ])

    def _cargar_tipo_frecuencia(self):
        self._cargar(CatTipoFrecuencia, [
            (1, 'Por 1ª vez'),
            (2, 'Ulterior'),
        ])

    def _cargar_tipo_contacto(self):
        self._cargar(CatTipoContacto, [
            (1, 'Exposición (presencial)'),
            (2, 'Telefónico'),
        ])

    def _cargar_motivo_consulta(self):
        self._cargar(CatMotivoConsulta, [
            (1, 'Intoxicación'),
            (2, 'Descartar Intoxicación'),
            (3, 'Asesoramiento'),
        ])

    def _cargar_subtipo_presencial(self):
        self._cargar(CatSubtipoPresencial, [
            (1, 'Urgencias'),
            (2, 'Internación'),
            (3, 'Consultorio Externo'),
            (4, 'Vía electrónico'),
        ])

    def _cargar_categoria_interlocutor(self):
        self._cargar(CatCategoriaInterlocutor, [
            (1, 'Personal de salud'),
            (2, 'Familiar'),
            (3, 'Paciente'),
            (4, 'Otro'),
        ])

    def _cargar_ubicacion_interlocutor(self):
        self._cargar(CatUbicacionInterlocutor, [
            (1, 'Establecimiento de Salud con Internamiento'),
            (2, 'Establecimiento de Salud sin Internamiento'),
            (3, 'Hogar'),
            (4, 'Trabajo'),
            (5, 'Institución educativa'),
            (6, 'Espacio Público'),
            (7, 'Otro'),
        ])

    def _cargar_sector(self):
        self._cargar(CatSector, [
            (1, 'Público'),
            (2, 'Privado'),
        ])

    def _cargar_circunstancias(self):
        """
        Los catálogos de circunstancias tienen dos niveles.
        Primero se crean los nivel1, luego los nivel2 con su FK al nivel1.
        """
        # Nivel 1
        nivel1_datos = [
            (1, 'No Intencional'),
            (2, 'Intencional'),
            (3, 'Reacción Adversa'),
            (4, 'Desconocido'),
        ]
        creados = 0
        for codigo, nombre in nivel1_datos:
            _, nuevo = CatCircunstanciaNivel1.objects.get_or_create(
                nombre=nombre, defaults={'codigo': codigo}
            )
            if nuevo:
                creados += 1
        self.stdout.write(f'  Circunstancias (Nivel 1): {creados} nuevos registros')

        # Nivel 2 — agrupados por su nivel1
        no_intencional = CatCircunstanciaNivel1.objects.get(nombre='No Intencional')
        intencional    = CatCircunstanciaNivel1.objects.get(nombre='Intencional')

        nivel2_datos = [
            # (nivel1, codigo, nombre)
            (no_intencional,  1, 'Accidental'),
            (no_intencional,  2, 'Ocupacional'),
            (no_intencional,  3, 'Ambiental'),
            (no_intencional,  4, 'Alimentaria'),
            (no_intencional,  5, 'Error terapéutico'),
            (no_intencional,  6, 'Mal uso'),
            (no_intencional,  7, 'Medicina tradicional'),
            (no_intencional,  8, 'Accidente químico'),
            (no_intencional,  9, 'Otro'),
            (intencional,    10, 'Tentativa suicida'),
            (intencional,    11, 'Abuso'),
            (intencional,    12, 'Automedicación'),
            (intencional,    13, 'Aborto'),
            (intencional,    14, 'Homicidio / Malicioso'),
            (intencional,    15, 'Otro'),
        ]
        creados = 0
        for nivel1, codigo, nombre in nivel2_datos:
            _, nuevo = CatCircunstanciaNivel2.objects.get_or_create(
                nombre=nombre,
                nivel1=nivel1,
                defaults={'codigo': codigo}
            )
            if nuevo:
                creados += 1
        self.stdout.write(f'  Circunstancias (Nivel 2): {creados} nuevos registros')

    def _cargar_ubicacion_evento(self):
        self._cargar(CatUbicacionEvento, [
            (1, 'Hogar y alrededores'),
            (2, 'Lugar de Trabajo'),
            (3, 'Institución de salud'),
            (4, 'Institución educativa'),
            (5, 'Espacio Público'),
            (6, 'Otro'),
        ])

    def _cargar_tipo_exposicion(self):
        self._cargar(CatTipoExposicion, [
            (1, 'Aguda'),
            (2, 'Crónica'),
            (3, 'Aguda sobre crónica'),
            (4, 'Desconocida'),
        ])

    def _cargar_tipo_agente(self):
        self._cargar(CatTipoAgente, [
            ( 1, 'Medicamento'),
            ( 2, 'Producto veterinario'),
            ( 3, 'Producto Industrial / Comercial'),
            ( 4, 'Producto Doméstico / Entretenimiento'),
            ( 5, 'Cosmético / Higiene personal'),
            ( 6, 'Plaguicida de Uso Doméstico'),
            ( 7, 'Plaguicida de Uso Agrícola'),
            ( 8, 'Plaguicida de Uso Veterinario'),
            ( 9, 'Plaguicida de Uso en Salud Pública'),
            (10, 'Droga de Abuso'),
            (11, 'Alimento / Bebida'),
            (12, 'Contaminante ambiental'),
            (13, 'Armas Químicas'),
            (14, 'Plantas'),
            (15, 'Hongos'),
            (16, 'Animales'),
            (17, 'Agroquímicos / Armas'),
            (18, 'Desconocido'),
            (19, 'Otro'),
        ])

    def _cargar_via_ingreso(self):
        self._cargar(CatViaIngreso, [
            (1, 'Oral'),
            (2, 'Inhalatoria'),
            (3, 'Cutánea / Mucosa'),
            (4, 'Ocular'),
            (5, 'Parenteral'),
            (6, 'Mordedura / Picadura'),
            (7, 'Desconocida'),
            (8, 'Otra'),
        ])

    def _cargar_tratamiento(self):
        # (codigo, nombre, requiere_especificar)
        datos = [
            ( 1, 'Ninguno',                             False),
            ( 2, 'Derivación a Institución Médica',     False),
            ( 3, 'Dilución',                            False),
            ( 4, 'Aspiración Gástrica',                 False),
            ( 5, 'Lavado gástrico',                     False),
            ( 6, 'Vómito provocado',                    False),
            ( 7, 'Carbón Activado',                     False),
            ( 8, 'Lavado intestinal y endoscopía',       False),
            ( 9, 'Catárticos',                          False),
            (10, 'Descontaminación Externa',            False),
            (11, 'Control clínico / Observación',       False),
            (12, 'Líquidos / electrolitos vía oral',    False),
            (13, 'Líquidos / electrolitos endovenoso',  False),
            (14, 'Nebulizaciones',                      False),
            (15, 'Oxígeno normobárico',                 False),
            (16, 'Oxígeno hiperbárico',                 False),
            (17, 'Demulcentes',                         False),
            (18, 'Intubación',                          False),
            (19, 'Asistencia Respiratoria Mecánica',    False),
            (20, 'Alcalinización (plasma)',              False),
            (21, 'Carbón Activado seriado',             False),
            (22, 'Modificación del pH urinario',        False),
            (23, 'Métodos Extracorpóreos',              False),
            (24, 'Antídoto / Quelante / Faboterápico',  True),   # especificar cuál
            (25, 'Otro fármaco',                        True),   # especificar cuál
            (26, 'Consulta especialista',               True),   # especificar quién
            (27, 'Desconocido',                         False),
            (28, 'Otro',                                True),   # especificar
        ]
        creados = 0
        for codigo, nombre, requiere in datos:
            _, nuevo = CatTratamiento.objects.get_or_create(
                nombre=nombre,
                defaults={'codigo': codigo, 'requiere_especificar': requiere}
            )
            if nuevo:
                creados += 1
        self.stdout.write(f'  Tratamientos: {creados} nuevos registros')
