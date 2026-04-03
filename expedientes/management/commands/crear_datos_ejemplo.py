"""
Comando de gestión: crear_datos_ejemplo
Uso: python manage.py crear_datos_ejemplo

Crea 20 historias clínicas de muestra realistas para demostración y pruebas.
También crea dos usuarios de prueba: demo_admin y demo_cap.

Es seguro ejecutarlo varias veces — omite los folios DEMO-XXX que ya existen.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date, timedelta

from expedientes.models import (
    HistoriaClinica,
    HistoriaClinicaTratamiento,
    CatSexo,
    CatSeveridad,
    CatEvolucion,
    CatTipoFrecuencia,
    CatTipoContacto,
    CatMotivoConsulta,
    CatSubtipoPresencial,
    CatCategoriaInterlocutor,
    CatCircunstanciaNivel1,
    CatCircunstanciaNivel2,
    CatUbicacionEvento,
    CatTipoExposicion,
    CatTipoAgente,
    CatViaIngreso,
    CatTratamiento,
)


class Command(BaseCommand):
    help = 'Crea datos de muestra para demostración y pruebas'

    def add_arguments(self, parser):
        # Permite usar el comando tanto para una demo pequeña (`20`) como
        # para poblar la base con cientos de registros para probar filtros,
        # paginación y gráficas sin editar código.
        parser.add_argument(
            '--cantidad',
            type=int,
            default=20,
            help='Cantidad total de historias demo a asegurar en la base de datos.',
        )

    def handle(self, *args, **options):
        # `cantidad` no significa "crear exactamente N nuevas", sino "dejar la
        # base con N historias DEMO-* en total". Si algunas ya existen, se omiten
        # y solo se generan las faltantes.
        cantidad = options['cantidad']
        if cantidad < 1:
            self.stdout.write(
                self.style.ERROR('ERROR: --cantidad debe ser un entero mayor o igual a 1.')
            )
            return

        self.stdout.write('=' * 60)
        self.stdout.write('Iniciando carga de datos de ejemplo...')
        self.stdout.write('=' * 60)

        # Verificar que los catálogos existan antes de continuar
        if not self._verificar_catalogos():
            return

        # Crear usuarios de demostración
        admin_demo = self._crear_usuario_demo()

        # Cargar todos los catálogos en variables locales para construir los casos
        cats = self._cargar_catalogos()

        # A partir de aquí el comando ya tiene todo lo necesario:
        # usuarios, catálogos y la meta de registros a asegurar.
        self._crear_historias(admin_demo, cats, cantidad)

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('¡Proceso completado!'))

    # ─────────────────────────────────────────────────────────────────────
    # Verificación inicial
    # ─────────────────────────────────────────────────────────────────────

    def _verificar_catalogos(self):
        """
        Comprueba que los catálogos esenciales existan en la base de datos.
        Si no existen, indica al usuario que ejecute cargar_catalogos primero.
        """
        faltantes = []

        if not CatSexo.objects.exists():
            faltantes.append('CatSexo')
        if not CatTipoContacto.objects.exists():
            faltantes.append('CatTipoContacto')
        if not CatMotivoConsulta.objects.exists():
            faltantes.append('CatMotivoConsulta')
        if not CatTipoAgente.objects.exists():
            faltantes.append('CatTipoAgente')
        if not CatSeveridad.objects.exists():
            faltantes.append('CatSeveridad')

        if faltantes:
            self.stdout.write(
                self.style.ERROR(
                    '\nERROR: Los siguientes catálogos están vacíos:\n'
                    + '\n'.join(f'  - {c}' for c in faltantes)
                    + '\n\nEjecuta primero:\n  python manage.py cargar_catalogos'
                )
            )
            return False

        self.stdout.write(self.style.SUCCESS('  Catálogos verificados OK'))
        return True

    # ─────────────────────────────────────────────────────────────────────
    # Creación de usuarios de demostración
    # ─────────────────────────────────────────────────────────────────────

    def _crear_usuario_demo(self):
        """
        Crea dos usuarios de prueba si no existen:
        - demo_admin: administrador con acceso completo
        - demo_cap:   capturista con acceso limitado
        Contraseña para ambos: demo1234
        """
        self.stdout.write('\nCreando usuarios de demostración...')
        CONTRASENA = 'demo1234'

        # Obtener grupos si existen (creados por crear_grupos.py)
        grupo_admin = Group.objects.filter(name='Administradores').first()
        grupo_cap   = Group.objects.filter(name='Capturistas').first()

        # Usuario administrador de demo
        admin_demo, creado = User.objects.get_or_create(
            username='demo_admin',
            defaults={
                'first_name': 'Admin',
                'last_name': 'Demo',
                'email': 'demo_admin@ciat.local',
                'is_staff': True,
            }
        )
        if creado:
            admin_demo.set_password(CONTRASENA)
            admin_demo.save()
            if grupo_admin:
                admin_demo.groups.add(grupo_admin)
            self.stdout.write(f'  Usuario demo_admin creado (contraseña: {CONTRASENA})')
        else:
            self.stdout.write('  Usuario demo_admin ya existía — sin cambios')

        # Usuario capturista de demo
        cap_demo, creado = User.objects.get_or_create(
            username='demo_cap',
            defaults={
                'first_name': 'Capturista',
                'last_name': 'Demo',
                'email': 'demo_cap@ciat.local',
                'is_staff': False,
            }
        )
        if creado:
            cap_demo.set_password(CONTRASENA)
            cap_demo.save()
            if grupo_cap:
                cap_demo.groups.add(grupo_cap)
            self.stdout.write(f'  Usuario demo_cap creado (contraseña: {CONTRASENA})')
        else:
            self.stdout.write('  Usuario demo_cap ya existía — sin cambios')

        return admin_demo

    # ─────────────────────────────────────────────────────────────────────
    # Carga de catálogos en variables locales
    # ─────────────────────────────────────────────────────────────────────

    def _cargar_catalogos(self):
        """
        Lee todos los catálogos de la BD y los guarda en un diccionario.
        Usa .filter(activo=True).first() con fallback a None para no romper
        si algún catálogo está desactivado o no fue cargado.
        """

        def primero(modelo, **kwargs):
            """Devuelve el primer registro activo que coincida, o None si no existe."""
            return modelo.objects.filter(activo=True, **kwargs).first()

        def por_nombre(modelo, nombre):
            """Busca por nombre exacto, activo=True, devuelve None si no existe."""
            return modelo.objects.filter(activo=True, nombre=nombre).first()

        # ── Sexo ──────────────────────────────────────────────────────────
        masc  = por_nombre(CatSexo, 'Masculino')
        fem   = por_nombre(CatSexo, 'Femenino')

        # ── Tipo de contacto ──────────────────────────────────────────────
        presencial   = por_nombre(CatTipoContacto, 'Exposición (presencial)')
        telefonico   = por_nombre(CatTipoContacto, 'Telefónico')

        # ── Motivo de consulta ────────────────────────────────────────────
        intoxicacion = por_nombre(CatMotivoConsulta, 'Intoxicación')
        descarte     = por_nombre(CatMotivoConsulta, 'Descartar Intoxicación')
        asesoramiento = por_nombre(CatMotivoConsulta, 'Asesoramiento')

        # ── Subtipo presencial ────────────────────────────────────────────
        urgencias    = por_nombre(CatSubtipoPresencial, 'Urgencias')
        internacion  = por_nombre(CatSubtipoPresencial, 'Internación')

        # ── Tipo de frecuencia ────────────────────────────────────────────
        primera_vez  = por_nombre(CatTipoFrecuencia, 'Por 1ª vez')
        ulterior     = por_nombre(CatTipoFrecuencia, 'Ulterior')

        # ── Circunstancias nivel 1 ────────────────────────────────────────
        no_intencional  = por_nombre(CatCircunstanciaNivel1, 'No Intencional')
        intencional_n1  = por_nombre(CatCircunstanciaNivel1, 'Intencional')
        reaccion_adv    = por_nombre(CatCircunstanciaNivel1, 'Reacción Adversa')
        desconocido_n1  = por_nombre(CatCircunstanciaNivel1, 'Desconocido')

        # ── Circunstancias nivel 2 (dependen del nivel 1) ─────────────────
        # No intencional → nivel 2
        accidental      = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Accidental', nivel1=no_intencional).first()
        ocupacional     = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Ocupacional', nivel1=no_intencional).first()
        error_terapeut  = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Error terapéutico', nivel1=no_intencional).first()
        mal_uso         = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Mal uso', nivel1=no_intencional).first()
        med_tradicional = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Medicina tradicional', nivel1=no_intencional).first()
        alimentaria     = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Alimentaria', nivel1=no_intencional).first()

        # Intencional → nivel 2
        tentativa       = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Tentativa suicida', nivel1=intencional_n1).first()
        abuso           = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Abuso', nivel1=intencional_n1).first()
        automedicacion  = CatCircunstanciaNivel2.objects.filter(
            activo=True, nombre='Automedicación', nivel1=intencional_n1).first()

        # ── Ubicación del evento ──────────────────────────────────────────
        hogar           = por_nombre(CatUbicacionEvento, 'Hogar y alrededores')
        trabajo         = por_nombre(CatUbicacionEvento, 'Lugar de Trabajo')
        inst_salud      = por_nombre(CatUbicacionEvento, 'Institución de salud')
        espacio_pub     = por_nombre(CatUbicacionEvento, 'Espacio Público')

        # ── Tipo de exposición ────────────────────────────────────────────
        aguda           = por_nombre(CatTipoExposicion, 'Aguda')
        cronica         = por_nombre(CatTipoExposicion, 'Crónica')
        aguda_cronica   = por_nombre(CatTipoExposicion, 'Aguda sobre crónica')

        # ── Tipo de agente ────────────────────────────────────────────────
        medicamento     = por_nombre(CatTipoAgente, 'Medicamento')
        plaguicida_dom  = por_nombre(CatTipoAgente, 'Plaguicida de Uso Doméstico')
        plaguicida_agr  = por_nombre(CatTipoAgente, 'Plaguicida de Uso Agrícola')
        droga_abuso     = por_nombre(CatTipoAgente, 'Droga de Abuso')
        animal          = por_nombre(CatTipoAgente, 'Animales')
        planta          = por_nombre(CatTipoAgente, 'Plantas')
        prod_industrial = por_nombre(CatTipoAgente, 'Producto Industrial / Comercial')
        prod_domestico  = por_nombre(CatTipoAgente, 'Producto Doméstico / Entretenimiento')
        alimento        = por_nombre(CatTipoAgente, 'Alimento / Bebida')
        prod_veterinario = por_nombre(CatTipoAgente, 'Producto veterinario')

        # ── Vías de ingreso ───────────────────────────────────────────────
        oral            = por_nombre(CatViaIngreso, 'Oral')
        inhalatoria     = por_nombre(CatViaIngreso, 'Inhalatoria')
        cutanea         = por_nombre(CatViaIngreso, 'Cutánea / Mucosa')
        ocular          = por_nombre(CatViaIngreso, 'Ocular')
        mordedura       = por_nombre(CatViaIngreso, 'Mordedura / Picadura')
        parenteral      = por_nombre(CatViaIngreso, 'Parenteral')

        # ── Severidad ─────────────────────────────────────────────────────
        asintomatico    = por_nombre(CatSeveridad, 'Asintomático')
        leve            = por_nombre(CatSeveridad, 'Leve')
        moderada        = por_nombre(CatSeveridad, 'Moderada')
        severa          = por_nombre(CatSeveridad, 'Severa')
        fatal           = por_nombre(CatSeveridad, 'Fatal')

        # ── Evolución ─────────────────────────────────────────────────────
        recuperacion    = por_nombre(CatEvolucion, 'Recuperación')
        rec_retardada   = por_nombre(CatEvolucion, 'Recuperación retardada')
        muerte          = por_nombre(CatEvolucion, 'Muerte')
        desconocida_ev  = por_nombre(CatEvolucion, 'Desconocida')

        # ── Tratamientos más usados ───────────────────────────────────────
        trat_ninguno        = por_nombre(CatTratamiento, 'Ninguno')
        trat_lavado_g       = por_nombre(CatTratamiento, 'Lavado gástrico')
        trat_carbon         = por_nombre(CatTratamiento, 'Carbón Activado')
        trat_oxigeno        = por_nombre(CatTratamiento, 'Oxígeno normobárico')
        trat_control_clin   = por_nombre(CatTratamiento, 'Control clínico / Observación')
        trat_liquidos_ev    = por_nombre(CatTratamiento, 'Líquidos / electrolitos endovenoso')
        trat_liquidos_oral  = por_nombre(CatTratamiento, 'Líquidos / electrolitos vía oral')
        trat_antidoto       = por_nombre(CatTratamiento, 'Antídoto / Quelante / Faboterápico')
        trat_descontam      = por_nombre(CatTratamiento, 'Descontaminación Externa')
        trat_derivacion     = por_nombre(CatTratamiento, 'Derivación a Institución Médica')
        trat_intubacion     = por_nombre(CatTratamiento, 'Intubación')
        trat_vomito         = por_nombre(CatTratamiento, 'Vómito provocado')
        trat_otro_farm      = por_nombre(CatTratamiento, 'Otro fármaco')
        trat_nebulizaciones = por_nombre(CatTratamiento, 'Nebulizaciones')

        # Devolver todo en un diccionario para usar en los casos
        return {
            # sexo
            'masc': masc, 'fem': fem,
            # contacto
            'presencial': presencial, 'telefonico': telefonico,
            # motivo
            'intoxicacion': intoxicacion, 'descarte': descarte,
            'asesoramiento': asesoramiento,
            # subtipo presencial
            'urgencias': urgencias, 'internacion': internacion,
            # frecuencia
            'primera_vez': primera_vez, 'ulterior': ulterior,
            # circunstancias n1
            'no_intencional': no_intencional, 'intencional_n1': intencional_n1,
            'reaccion_adv': reaccion_adv, 'desconocido_n1': desconocido_n1,
            # circunstancias n2
            'accidental': accidental, 'ocupacional': ocupacional,
            'error_terapeut': error_terapeut, 'mal_uso': mal_uso,
            'med_tradicional': med_tradicional, 'alimentaria': alimentaria,
            'tentativa': tentativa, 'abuso': abuso, 'automedicacion': automedicacion,
            # ubicación
            'hogar': hogar, 'trabajo': trabajo, 'inst_salud': inst_salud,
            'espacio_pub': espacio_pub,
            # tipo exposición
            'aguda': aguda, 'cronica': cronica, 'aguda_cronica': aguda_cronica,
            # tipo agente
            'medicamento': medicamento, 'plaguicida_dom': plaguicida_dom,
            'plaguicida_agr': plaguicida_agr, 'droga_abuso': droga_abuso,
            'animal': animal, 'planta': planta, 'prod_industrial': prod_industrial,
            'prod_domestico': prod_domestico, 'alimento': alimento,
            'prod_veterinario': prod_veterinario,
            # vías
            'oral': oral, 'inhalatoria': inhalatoria, 'cutanea': cutanea,
            'ocular': ocular, 'mordedura': mordedura, 'parenteral': parenteral,
            # severidad
            'asintomatico': asintomatico, 'leve': leve, 'moderada': moderada,
            'severa': severa, 'fatal': fatal,
            # evolución
            'recuperacion': recuperacion, 'rec_retardada': rec_retardada,
            'muerte': muerte, 'desconocida_ev': desconocida_ev,
            # tratamientos
            'trat_ninguno': trat_ninguno, 'trat_lavado_g': trat_lavado_g,
            'trat_carbon': trat_carbon, 'trat_oxigeno': trat_oxigeno,
            'trat_control_clin': trat_control_clin, 'trat_liquidos_ev': trat_liquidos_ev,
            'trat_liquidos_oral': trat_liquidos_oral, 'trat_antidoto': trat_antidoto,
            'trat_descontam': trat_descontam, 'trat_derivacion': trat_derivacion,
            'trat_intubacion': trat_intubacion, 'trat_vomito': trat_vomito,
            'trat_otro_farm': trat_otro_farm, 'trat_nebulizaciones': trat_nebulizaciones,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Creación de las 20 historias clínicas
    # ─────────────────────────────────────────────────────────────────────

    def _crear_historias(self, usuario, c, cantidad):
        """
        Crea historias clínicas realistas para el contexto del CIAT,
        distribuidas en los últimos 12 meses.
        'c' es el diccionario de catálogos cargado por _cargar_catalogos().
        """
        self.stdout.write('\nCreando historias clínicas de muestra...')

        ahora = timezone.now()
        creadas = 0
        omitidas = 0

        # Cada caso es una tupla:
        # (folio, datos_base_dict, vias_ingreso_list, tratamientos_A_list, tratamientos_B_list)
        # dias_atras: cuántos días antes de hoy ocurrió la consulta
        # latencia_horas: horas entre exposición y consulta/ingreso

        casos_base = [
            # ─── CASO 1 ───────────────────────────────────────────────────────
            # Niño de 2 años que ingirió medicamento de adulto (paracetamol)
            # Muy común en el CIAT: accidente doméstico infantil
            {
                'folio': 'DEMO-001',
                'nombre': 'Emiliano', 'apellido': 'Reyes Martínez',
                'fecha_nacimiento': date(2022, 6, 15),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 340,
                'latencia_horas': 1,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['medicamento'],
                'agente': 'Paracetamol (acetaminofén) 500 mg',
                'agente_cantidad': '2 tabletas',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Vómito, náuseas. Sin otros síntomas.',
                'fc': 110, 'fr': 24, 'temp': '37.2', 'sat': 98,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [(c['trat_carbon'], ''), (c['trat_control_clin'], '')],
                'comentario': 'Menor de 2 años ingirió medicamento de adulto dejado al alcance.',
            },

            # ─── CASO 2 ───────────────────────────────────────────────────────
            # Picadura de alacrán en adulto — muy frecuente en SLP
            {
                'folio': 'DEMO-002',
                'nombre': 'Rosa María', 'apellido': 'Hernández Gutiérrez',
                'fecha_nacimiento': date(1985, 3, 22),
                'sexo': c['fem'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 300,
                'latencia_horas': 2,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['animal'],
                'agente': 'Centruroides limpidus (alacrán)',
                'agente_cantidad': '1 picadura en mano derecha',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Dolor local intenso, parestesias, sialorrea, náuseas, agitación.',
                'fc': 92, 'fr': 20, 'temp': '36.8', 'sat': 97,
                'vias': [c['mordedura']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Faboterápico antialacrán (Alacramyn)'),
                    (c['trat_control_clin'], ''),
                ],
                'comentario': 'Picadura ocurrió al mover calzado en la madrugada. Se administró faboterápico.',
            },

            # ─── CASO 3 ───────────────────────────────────────────────────────
            # Intoxicación por organofosforado agrícola (uso ocupacional)
            {
                'folio': 'DEMO-003',
                'nombre': 'Gilberto', 'apellido': 'Domínguez Peña',
                'fecha_nacimiento': date(1970, 11, 5),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 260,
                'latencia_horas': 3,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['ocupacional'],
                'ubicacion_evento': c['trabajo'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['plaguicida_agr'],
                'agente': 'Clorpirifos (Lorsban 480 EC)',
                'agente_cantidad': 'Exposición dérmica e inhalatoria durante aspersión',
                'severidad': c['severa'],
                'evolucion': c['rec_retardada'],
                'signos': (
                    'Miosis bilateral, broncorrea, bradicardia, salivación excesiva, '
                    'fasciculaciones musculares, alteración del estado de alerta.'
                ),
                'fc': 48, 'fr': 28, 'temp': '36.5', 'sat': 91,
                'vias': [c['cutanea'], c['inhalatoria']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Atropina + Pralidoxima (2-PAM)'),
                    (c['trat_intubacion'], ''),
                    (c['trat_liquidos_ev'], ''),
                ],
                'hospitalizacion_sala': False,
                'hospitalizacion_uci': True,
                'hospitalizacion_dias': 5,
                'comentario': 'Jornalero agrícola sin equipo de protección. Ingresó inconsciente.',
            },

            # ─── CASO 4 ───────────────────────────────────────────────────────
            # Tentativa suicida con benzodiacepinas en adulto joven
            {
                'folio': 'DEMO-004',
                'nombre': 'Valeria', 'apellido': 'Torres Sandoval',
                'fecha_nacimiento': date(2000, 8, 14),
                'sexo': c['fem'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 220,
                'latencia_horas': 4,
                'circunstancia_nivel1': c['intencional_n1'],
                'circunstancia_nivel2': c['tentativa'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['medicamento'],
                'agente': 'Clonazepam 2 mg',
                'agente_cantidad': '10-15 tabletas',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Somnolencia intensa, habla disártrica, ataxia. GCS 12.',
                'fc': 76, 'fr': 14, 'temp': '36.3', 'sat': 95,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_control_clin'], ''),
                    (c['trat_liquidos_ev'], ''),
                    (c['trat_otro_farm'], 'Flumazenil 0.2 mg IV'),
                ],
                'hospitalizacion_sala': True,
                'hospitalizacion_uci': False,
                'hospitalizacion_dias': 2,
                'comentario': 'Se activó protocolo de salud mental. Valoración por psiquiatría.',
            },

            # ─── CASO 5 ───────────────────────────────────────────────────────
            # Consulta telefónica por ingesta de blanqueador en niño
            {
                'folio': 'DEMO-005',
                'nombre': 'Sebastián', 'apellido': 'Flores Ramos',
                'fecha_nacimiento': date(2021, 1, 30),
                'sexo': c['masc'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 180,
                'latencia_horas': 0,  # llamada inmediata
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['prod_domestico'],
                'agente': 'Hipoclorito de sodio al 5% (blanqueador doméstico)',
                'agente_cantidad': 'Sorbo pequeño (~5 mL)',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Sin síntomas al momento de la llamada. Olor a cloro.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [(c['trat_liquidos_oral'], '')],
                'comentario': 'Se orientó a madre: dilución con agua o leche, NO provocar vómito.',
                'interlocutor_nombre': 'Sra. Lucía Ramos',
                'interlocutor_cat': c.get('cat_interlocutor_familiar'),
            },

            # ─── CASO 6 ───────────────────────────────────────────────────────
            # Intoxicación por metanol (alcohol de farmacia adulterado)
            {
                'folio': 'DEMO-006',
                'nombre': 'Jesús Eduardo', 'apellido': 'Vargas López',
                'fecha_nacimiento': date(1975, 5, 20),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 150,
                'latencia_horas': 18,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['mal_uso'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['droga_abuso'],
                'agente': 'Metanol (alcohol adulterado)',
                'agente_cantidad': 'Aprox. 200 mL',
                'severidad': c['severa'],
                'evolucion': c['rec_retardada'],
                'signos': (
                    'Visión borrosa, cefalea intensa, náuseas, vómito, '
                    'acidosis metabólica severa (pH 7.10), Glasgow 14.'
                ),
                'fc': 100, 'fr': 26, 'temp': '37.0', 'sat': 96,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Etanol 10% IV (antídoto competitivo)'),
                    (c['trat_liquidos_ev'], ''),
                ],
                'hospitalizacion_sala': False,
                'hospitalizacion_uci': True,
                'hospitalizacion_dias': 7,
                'comentario': 'Consumió junto con vecinos. Dos más en situación similar en urgencias.',
            },

            # ─── CASO 7 ───────────────────────────────────────────────────────
            # Reacción adversa a antibiótico (amoxicilina)
            {
                'folio': 'DEMO-007',
                'nombre': 'Carmen', 'apellido': 'Aguirre Medina',
                'fecha_nacimiento': date(1992, 9, 3),
                'sexo': c['fem'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['descarte'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 130,
                'latencia_horas': 1,
                'circunstancia_nivel1': c['reaccion_adv'],
                'circunstancia_nivel2': None,
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['medicamento'],
                'agente': 'Amoxicilina 500 mg',
                'agente_cantidad': '1 cápsula (dosis prescrita)',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Urticaria generalizada, prurito. Sin angioedema ni disnea.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_derivacion'], ''),
                    (c['trat_otro_farm'], 'Difenhidramina 25 mg VO'),
                ],
                'comentario': 'Se recomendó suspender antibiótico y acudir a urgencias si progresa.',
                'interlocutor_nombre': 'Paciente directamente',
            },

            # ─── CASO 8 ───────────────────────────────────────────────────────
            # Inhalación de plaguicida doméstico (aerosol insecticida) en adulto mayor
            {
                'folio': 'DEMO-008',
                'nombre': 'Ernesto', 'apellido': 'Castillo Núñez',
                'fecha_nacimiento': date(1945, 12, 10),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 110,
                'latencia_horas': 2,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['mal_uso'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['plaguicida_dom'],
                'agente': 'Piretrina + Butóxido de piperonilo (aerosol mata-insectos)',
                'agente_cantidad': 'Inhalación en habitación cerrada ~15 min',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Tos, irritación de vías respiratorias altas, lagrimeo.',
                'fc': 80, 'fr': 18, 'temp': '36.6', 'sat': 96,
                'vias': [c['inhalatoria']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_oxigeno'], ''),
                    (c['trat_control_clin'], ''),
                ],
                'comentario': 'Fumigó cuarto sin ventilar. Se le instruyó sobre uso seguro.',
            },

            # ─── CASO 9 ───────────────────────────────────────────────────────
            # Mordedura de víbora de cascabel (Crotalus) en adulto rural
            {
                'folio': 'DEMO-009',
                'nombre': 'Aurelio', 'apellido': 'Jiménez Torres',
                'fecha_nacimiento': date(1963, 4, 18),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 95,
                'latencia_horas': 4,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['trabajo'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['animal'],
                'agente': 'Crotalus scutulatus (víbora de cascabel)',
                'agente_cantidad': 'Mordedura única en tobillo izquierdo',
                'severidad': c['severa'],
                'evolucion': c['rec_retardada'],
                'signos': (
                    'Edema progresivo hasta rodilla, dolor intenso, equimosis local, '
                    'sangrado en encías, TP prolongado.'
                ),
                'fc': 105, 'fr': 22, 'temp': '37.4', 'sat': 95,
                'vias': [c['mordedura']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Faboterápico antivipérino (Bioclon)'),
                    (c['trat_liquidos_ev'], ''),
                ],
                'hospitalizacion_sala': True,
                'hospitalizacion_uci': False,
                'hospitalizacion_dias': 4,
                'comentario': 'Campesino trabajando en milpa. Traslado en 4 horas desde comunidad rural.',
            },

            # ─── CASO 10 ──────────────────────────────────────────────────────
            # Ingesta de raticida (warfarina / brodifacoum) en adulto
            {
                'folio': 'DEMO-010',
                'nombre': 'Patricia', 'apellido': 'Solís Campos',
                'fecha_nacimiento': date(1978, 7, 7),
                'sexo': c['fem'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 80,
                'latencia_horas': 72,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['plaguicida_dom'],
                'agente': 'Brodifacoum (raticida superwarfarínico)',
                'agente_cantidad': 'Desconocida — confundido con otro producto',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Sangrado gingival, hematomas espontáneos, TP >120 seg.',
                'fc': 88, 'fr': 17, 'temp': '36.7', 'sat': 98,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Vitamina K1 (fitomenadiona) 10 mg IV'),
                    (c['trat_control_clin'], ''),
                ],
                'hospitalizacion_sala': True,
                'hospitalizacion_uci': False,
                'hospitalizacion_dias': 3,
                'comentario': 'Latencia de 3 días porque los anticoagulantes de 2ª gen. retardan efectos.',
            },

            # ─── CASO 11 ──────────────────────────────────────────────────────
            # Asesoramiento — médico pregunta sobre dosis tóxica de digoxina
            {
                'folio': 'DEMO-011',
                'nombre': 'Ramón', 'apellido': 'Cruz Velázquez',
                'fecha_nacimiento': date(1950, 2, 28),
                'sexo': c['masc'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['asesoramiento'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 70,
                'latencia_horas': 0,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['error_terapeut'],
                'ubicacion_evento': c['inst_salud'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['medicamento'],
                'agente': 'Digoxina 0.25 mg',
                'agente_cantidad': 'Dosis doble por error de enfermería',
                'severidad': c['asintomatico'],
                'evolucion': c['recuperacion'],
                'signos': 'Asintomático al momento de la consulta.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [(c['trat_control_clin'], '')],
                'comentario': 'Llamó la jefe de enfermería del servicio de cardiología para orientación.',
                'interlocutor_nombre': 'Enf. Jefe Marisela Ortega',
            },

            # ─── CASO 12 ──────────────────────────────────────────────────────
            # Intoxicación por monóxido de carbono (calentador de agua en baño)
            {
                'folio': 'DEMO-012',
                'nombre': 'Andrea', 'apellido': 'Morales Becerra',
                'fecha_nacimiento': date(1998, 10, 25),
                'sexo': c['fem'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 60,
                'latencia_horas': 1,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['prod_industrial'],
                'agente': 'Monóxido de carbono (CO) — calentador de gas en baño sin ventilación',
                'agente_cantidad': 'Exposición 45-60 minutos',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Cefalea intensa, náuseas, mareo, CarboxiHb 28%.',
                'fc': 95, 'fr': 20, 'temp': '36.9', 'sat': 82,
                'vias': [c['inhalatoria']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_oxigeno'], ''),
                    (c['trat_control_clin'], ''),
                ],
                'comentario': 'CarboxiHb medida en urgencias. Oxígeno al 100% con mascarilla de no-reinhalación.',
            },

            # ─── CASO 13 ──────────────────────────────────────────────────────
            # Adolescente que ingirió champiñones silvestres
            {
                'folio': 'DEMO-013',
                'nombre': 'Diego Alejandro', 'apellido': 'Mendoza Ruiz',
                'fecha_nacimiento': date(2009, 3, 12),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 50,
                'latencia_horas': 6,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['alimentaria'],
                'ubicacion_evento': c['espacio_pub'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['alimento'],
                'agente': 'Hongos silvestres no identificados (posible Amanita sp.)',
                'agente_cantidad': '3-4 piezas cocinadas',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Dolor abdominal cólico, diarrea abundante, vómito. Sin datos de insuficiencia hepática.',
                'fc': 98, 'fr': 18, 'temp': '37.1', 'sat': 99,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_liquidos_ev'], ''),
                    (c['trat_control_clin'], ''),
                ],
                'hospitalizacion_sala': True,
                'hospitalizacion_uci': False,
                'hospitalizacion_dias': 2,
                'comentario': 'Recolectados en campo durante excursión escolar. Transaminasas normales.',
            },

            # ─── CASO 14 ──────────────────────────────────────────────────────
            # Exposición ocular a cal viva (trabajador de construcción)
            {
                'folio': 'DEMO-014',
                'nombre': 'Iván', 'apellido': 'Ramírez Estrada',
                'fecha_nacimiento': date(1988, 6, 3),
                'sexo': c['masc'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 40,
                'latencia_horas': 0,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['ocupacional'],
                'ubicacion_evento': c['trabajo'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['prod_industrial'],
                'agente': 'Óxido de calcio (cal viva)',
                'agente_cantidad': 'Salpicadura en ojo derecho',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Dolor ocular, fotofobia, lagrimeo. Sin disminución de agudeza visual.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['ocular']],
                'tratos_A': [(c['trat_descontam'], '')],
                'tratos_B': [(c['trat_derivacion'], '')],
                'comentario': 'Se indicó lavado ocular con agua corriente por 20 minutos. Derivado a oftalmología.',
                'interlocutor_nombre': 'Ing. Roberto Medina (supervisor de obra)',
            },

            # ─── CASO 15 ──────────────────────────────────────────────────────
            # Intoxicación por plantas — adelfa (Nerium oleander)
            {
                'folio': 'DEMO-015',
                'nombre': 'Sofía', 'apellido': 'Guerrero Paz',
                'fecha_nacimiento': date(2015, 9, 19),
                'sexo': c['fem'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 30,
                'latencia_horas': 3,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['accidental'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['planta'],
                'agente': 'Nerium oleander (adelfa/laurel rosa) — hojas',
                'agente_cantidad': '2-3 hojas masticadas',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Náuseas, vómito, bradicardia (FC 52 lpm), mareo.',
                'fc': 52, 'fr': 16, 'temp': '36.4', 'sat': 97,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_carbon'], ''),
                    (c['trat_control_clin'], ''),
                    (c['trat_liquidos_ev'], ''),
                ],
                'hospitalizacion_sala': True,
                'hospitalizacion_uci': False,
                'hospitalizacion_dias': 1,
                'comentario': 'Niña de jardín ingirió hojas de planta ornamental del patio.',
            },

            # ─── CASO 16 ──────────────────────────────────────────────────────
            # Automedicación con sobredosis de ibuprofeno
            {
                'folio': 'DEMO-016',
                'nombre': 'Marco Antonio', 'apellido': 'Leal Contreras',
                'fecha_nacimiento': date(1990, 1, 14),
                'sexo': c['masc'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 20,
                'latencia_horas': 2,
                'circunstancia_nivel1': c['intencional_n1'],
                'circunstancia_nivel2': c['automedicacion'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda_cronica'],
                'tipo_agente': c['medicamento'],
                'agente': 'Ibuprofeno 400 mg',
                'agente_cantidad': '8 tabletas en 6 horas (3200 mg)',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Dolor epigástrico, náuseas. Sin hematemesis.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_liquidos_oral'], ''),
                    (c['trat_otro_farm'], 'Omeprazol 20 mg VO'),
                ],
                'comentario': 'Tomó dosis excesiva para dolor crónico de espalda sin indicación médica.',
                'interlocutor_nombre': 'Paciente directamente',
            },

            # ─── CASO 17 ──────────────────────────────────────────────────────
            # Abuso de sustancias: intoxicación etílica aguda en joven
            {
                'folio': 'DEMO-017',
                'nombre': 'Luis Fernando', 'apellido': 'Soto Rivas',
                'fecha_nacimiento': date(2003, 5, 6),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 15,
                'latencia_horas': 3,
                'circunstancia_nivel1': c['intencional_n1'],
                'circunstancia_nivel2': c['abuso'],
                'ubicacion_evento': c['espacio_pub'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['droga_abuso'],
                'agente': 'Etanol (bebidas alcohólicas mixtas)',
                'agente_cantidad': 'Aprox. 400-500 mL etanol puro',
                'severidad': c['moderada'],
                'evolucion': c['recuperacion'],
                'signos': 'Estupor, vómito en proyectil, halitosis alcohólica. GCS 11.',
                'fc': 88, 'fr': 16, 'temp': '36.1', 'sat': 96,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_control_clin'], ''),
                    (c['trat_liquidos_ev'], ''),
                ],
                'comentario': 'Encontrado inconsciente en vía pública por policía municipal.',
            },

            # ─── CASO 18 ──────────────────────────────────────────────────────
            # Medicina tradicional: té de estafiate en bebé lactante
            {
                'folio': 'DEMO-018',
                'nombre': 'Ximena', 'apellido': 'Alvarado Reyes',
                'fecha_nacimiento': date(2025, 10, 5),
                'sexo': c['fem'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 8,
                'latencia_horas': 1,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['med_tradicional'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['planta'],
                'agente': 'Artemisia ludoviciana (estafiate) — infusión concentrada',
                'agente_cantidad': '30 mL de té concentrado',
                'severidad': c['leve'],
                'evolucion': c['recuperacion'],
                'signos': 'Irritabilidad, llanto, ligera somnolencia.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [(c['trat_control_clin'], '')],
                'comentario': 'Abuela administró té por "cólico". Se orientó sobre riesgos en lactantes.',
                'interlocutor_nombre': 'Sra. Elena Reyes (abuela)',
            },

            # ─── CASO 19 ──────────────────────────────────────────────────────
            # Intoxicación fatal: adolescente con tentativa suicida por carbamato
            {
                'folio': 'DEMO-019',
                'nombre': 'Óscar', 'apellido': 'Pedraza Vázquez',
                'fecha_nacimiento': date(2007, 8, 20),
                'sexo': c['masc'],
                'tipo_contacto': c['presencial'],
                'subtipo_presencial': c['urgencias'],
                'motivo_consulta': c['intoxicacion'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 5,
                'latencia_horas': 5,
                'circunstancia_nivel1': c['intencional_n1'],
                'circunstancia_nivel2': c['tentativa'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['plaguicida_agr'],
                'agente': 'Carbofurán (plaguicida agrícola carbamato)',
                'agente_cantidad': 'Desconocida — ingestión intencional',
                'severidad': c['fatal'],
                'evolucion': c['muerte'],
                'signos': (
                    'Paro cardiorrespiratorio al ingreso. Miosis máxima, broncorrea severa, '
                    'convulsiones. Maniobras de RCP prolongadas sin éxito.'
                ),
                'fc': 0, 'fr': 0, 'temp': '35.0', 'sat': None,
                'vias': [c['oral']],
                'tratos_A': [(c['trat_ninguno'], '')],
                'tratos_B': [
                    (c['trat_antidoto'], 'Atropina dosis altas + RCP'),
                    (c['trat_intubacion'], ''),
                ],
                'hospitalizacion_sala': False,
                'hospitalizacion_uci': True,
                'hospitalizacion_dias': 0,
                'comentario': 'Caso fatal. Se realizó aviso al MP. Revisión de factores de riesgo suicida en hogar.',
            },

            # ─── CASO 20 ──────────────────────────────────────────────────────
            # Dermatitis por contacto con producto veterinario (ivermectina tópica)
            {
                'folio': 'DEMO-020',
                'nombre': 'Graciela', 'apellido': 'Ibáñez Montes',
                'fecha_nacimiento': date(1955, 4, 30),
                'sexo': c['fem'],
                'tipo_contacto': c['telefonico'],
                'subtipo_presencial': None,
                'motivo_consulta': c['descarte'],
                'tipo_frecuencia': c['primera_vez'],
                'dias_atras': 2,
                'latencia_horas': 12,
                'circunstancia_nivel1': c['no_intencional'],
                'circunstancia_nivel2': c['mal_uso'],
                'ubicacion_evento': c['hogar'],
                'tipo_exposicion': c['aguda'],
                'tipo_agente': c['prod_veterinario'],
                'agente': 'Ivermectina al 1% (pour-on veterinaria)',
                'agente_cantidad': 'Aplicación en piel de brazos y cuello',
                'severidad': c['asintomatico'],
                'evolucion': c['recuperacion'],
                'signos': 'Eritema leve en zona de aplicación. Sin síntomas sistémicos.',
                'fc': None, 'fr': None, 'temp': None, 'sat': None,
                'vias': [c['cutanea']],
                'tratos_A': [(c['trat_descontam'], '')],
                'tratos_B': [(c['trat_control_clin'], '')],
                'comentario': 'Aplicó producto destinado a ganado creyendo que era ivermectina humana.',
                'interlocutor_nombre': 'Sra. Graciela Ibáñez (paciente)',
            },
        ]

        # `casos_base` contiene 20 escenarios clínicos curados a mano.
        # Si el usuario pide más de 20 registros, `_expandir_casos()` fabrica
        # variantes manteniendo la misma estructura clínica, pero con folios,
        # fechas y etiquetas distintas para que el dataset crezca sin colisiones.
        casos = self._expandir_casos(casos_base, cantidad)

        for i, caso in enumerate(casos):
            folio = caso['folio']

            # Verificar si ya existe — si sí, omitir
            if HistoriaClinica.objects.filter(folio_expediente=folio).exists():
                self.stdout.write(f'  {folio} — ya existe, omitido')
                omitidas += 1
                continue

            try:
                # Primero se crea la historia principal. Después se agregan
                # relaciones ManyToMany (vías y tratamientos), porque esas
                # relaciones solo pueden asociarse una vez que la historia
                # ya fue guardada y tiene PK.
                historia = self._construir_historia(caso, usuario, i)
                self._agregar_vias(historia, caso)
                self._agregar_tratamientos(historia, caso)
                self.stdout.write(f'  {folio} — creado: {caso["nombre"]} {caso["apellido"]}')
                creadas += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  {folio} — ERROR: {e}')
                )

        # Resumen final
        self.stdout.write('\n--- Resumen ---')
        self.stdout.write(self.style.SUCCESS(f'  Historias creadas:  {creadas}'))
        if omitidas:
            self.stdout.write(f'  Historias omitidas: {omitidas} (ya existían)')

    def _expandir_casos(self, casos_base, cantidad):
        """
        Devuelve exactamente `cantidad` casos. Si se piden más de los casos base,
        genera variantes con folios únicos para poder poblar la BD con más datos.
        """
        if cantidad <= len(casos_base):
            return casos_base[:cantidad]

        # Se parte de una copia superficial para no mutar la lista original.
        # Eso permite que los 20 casos base sigan siendo el "molde" canónico
        # del cual se derivan las variantes posteriores.
        casos = [dict(caso) for caso in casos_base]
        etiquetas_extra = [
            'Variante norte', 'Variante centro', 'Variante sur', 'Seguimiento local',
            'Consulta ampliada', 'Caso comunitario', 'Referencia externa', 'Revaloración',
        ]

        for indice in range(len(casos_base), cantidad):
            # Se recicla uno de los casos base usando aritmética modular:
            # 20 -> vuelve al caso 1, 21 -> caso 2, etc.
            base = casos_base[indice % len(casos_base)]
            variante_num = indice + 1
            caso = dict(base)
            dias_base = base.get('dias_atras', (indice % len(casos_base)) * 18)

            # El folio nuevo evita choques por unicidad. Los ajustes de fecha y
            # latencia distribuyen las variantes a lo largo del año para que
            # las estadísticas temporales no queden totalmente concentradas.
            caso['folio'] = f'DEMO-{variante_num:03d}'
            caso['dias_atras'] = max(0, (dias_base + (indice * 11)) % 365)
            caso['latencia_horas'] = max(0, ((base.get('latencia_horas', 2) + indice) % 24))
            caso['comentario'] = (
                f'{base.get("comentario", "")} '
                f'[{etiquetas_extra[indice % len(etiquetas_extra)]} #{variante_num}]'
            ).strip()
            casos.append(caso)

        return casos

    # ─────────────────────────────────────────────────────────────────────
    # Método auxiliar: construir y guardar la historia principal
    # ─────────────────────────────────────────────────────────────────────

    def _construir_historia(self, caso, usuario, indice):
        """
        Crea y guarda el objeto HistoriaClinica con los datos del caso.
        Los campos ManyToMany (vias, tratamientos) se agregan después del save().
        """
        ahora = timezone.now()

        # Calcular fecha de la consulta: distribuida en los últimos 12 meses
        dias_atras = caso.get('dias_atras', indice * 18)
        fecha_consulta = ahora - timedelta(days=dias_atras)

        # Calcular fecha del evento de exposición (antes de la consulta)
        latencia_horas = caso.get('latencia_horas', 2)
        fecha_exposicion = fecha_consulta - timedelta(hours=latencia_horas)

        # Para consultas presenciales, fecha_hora_ingreso = fecha_consulta
        es_presencial = caso['tipo_contacto'] and 'presencial' in caso['tipo_contacto'].nombre.lower()
        fecha_ingreso = fecha_consulta if es_presencial else None

        # `consulta_numero`, edad y latencia se calculan dentro del `save()`
        # del modelo. Aquí solo alimentamos los datos crudos mínimos y dejamos
        # que la lógica del modelo centralice esos cálculos.

        historia = HistoriaClinica(
            # Datos del paciente
            folio_expediente = caso['folio'],
            nombre           = caso['nombre'],
            apellido         = caso['apellido'],
            fecha_nacimiento = caso.get('fecha_nacimiento'),
            sexo             = caso.get('sexo'),

            # Datos de la consulta
            tipo_frecuencia      = caso.get('tipo_frecuencia'),
            tipo_contacto        = caso.get('tipo_contacto'),
            motivo_consulta      = caso.get('motivo_consulta'),
            subtipo_presencial   = caso.get('subtipo_presencial'),

            # Fechas — el modelo calculará edad y latencia en save()
            fecha_hora_consulta          = fecha_consulta,
            fecha_hora_ingreso           = fecha_ingreso,
            fecha_hora_evento_exposicion = fecha_exposicion,

            # Circunstancias
            circunstancia_nivel1 = caso.get('circunstancia_nivel1'),
            circunstancia_nivel2 = caso.get('circunstancia_nivel2'),

            # Exposición
            ubicacion_evento = caso.get('ubicacion_evento'),
            tipo_exposicion  = caso.get('tipo_exposicion'),

            # Agente tóxico
            tipo_agente             = caso.get('tipo_agente'),
            agente_principio_activo = caso.get('agente', ''),
            agente_cantidad_informada = caso.get('agente_cantidad', ''),

            # Signos vitales (algunos casos telefónicos no los tienen)
            signos_sintomas = caso.get('signos', ''),
            fc   = caso.get('fc'),
            fr   = caso.get('fr'),
            temp = caso.get('temp'),
            sat  = caso.get('sat'),

            # Severidad y evolución
            severidad = caso.get('severidad'),
            evolucion = caso.get('evolucion'),

            # Hospitalización (solo algunos casos)
            hospitalizacion_sala_general = caso.get('hospitalizacion_sala', False),
            hospitalizacion_uci_uti      = caso.get('hospitalizacion_uci', False),
            hospitalizacion_urgencias    = False,
            hospitalizacion_dias         = caso.get('hospitalizacion_dias'),

            # Interlocutor (solo telefónico — si el caso lo especifica)
            interlocutor_nombre = caso.get('interlocutor_nombre', ''),

            # Comentario y auditoría
            comentario      = caso.get('comentario', ''),
            usuario_captura = usuario,
        )

        # save() calcula automáticamente: consulta_numero, edad, latencia
        historia.save()
        return historia

    # ─────────────────────────────────────────────────────────────────────
    # Método auxiliar: agregar vías de ingreso (ManyToMany)
    # ─────────────────────────────────────────────────────────────────────

    def _agregar_vias(self, historia, caso):
        """
        Asigna las vías de ingreso al ManyToMany.
        Filtra los None (por si algún catálogo no existe en la BD).
        """
        # El filtrado evita intentar asociar valores nulos cuando un catálogo
        # opcional no esté cargado o el caso no lo requiera.
        vias = [v for v in caso.get('vias', []) if v is not None]
        if vias:
            historia.vias_ingreso.set(vias)

    # ─────────────────────────────────────────────────────────────────────
    # Método auxiliar: agregar tratamientos A y B
    # ─────────────────────────────────────────────────────────────────────

    def _agregar_tratamientos(self, historia, caso):
        """
        Crea los registros HistoriaClinicaTratamiento para columna A y B.
        Cada elemento es (CatTratamiento, especificar_texto).
        Filtra los None para no romper si el catálogo no existe.
        """
        for columna, clave in [('A', 'tratos_A'), ('B', 'tratos_B')]:
            # Columna A = lo que recibió previamente el paciente.
            # Columna B = lo que recomienda el CIAT.
            for trat, especificar in caso.get(clave, []):
                if trat is None:
                    continue
                # `get_or_create` vuelve el comando idempotente: si el mismo
                # tratamiento ya estaba asociado en esa columna, no lo duplica.
                HistoriaClinicaTratamiento.objects.get_or_create(
                    historia    = historia,
                    tratamiento = trat,
                    columna     = columna,
                    defaults    = {'especificar': especificar or ''},
                )
