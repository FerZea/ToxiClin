import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from expedientes.models import (
    HistoriaClinica, HistoriaClinicaTratamiento,
    CatSexo, CatSeveridad, CatEvolucion,
    CatTipoFrecuencia, CatTipoContacto, CatMotivoConsulta, CatSubtipoPresencial,
    CatCategoriaInterlocutor, CatUbicacionInterlocutor, CatSector,
    CatCircunstanciaNivel1, CatCircunstanciaNivel2,
    CatUbicacionEvento, CatTipoExposicion, CatTipoAgente,
    CatViaIngreso, CatTratamiento
)

class Command(BaseCommand):
    help = 'Genera 500 registros de prueba aleatorios para HistoriaClinica'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=500,
            help='Número de registros a generar'
        )
        parser.add_argument(
            '--borrar',
            action='store_true',
            help='Borrar registros existentes antes de generar nuevos'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        borrar = options['borrar']

        if borrar:
            self.stdout.write(self.style.WARNING(f'Borrando registros existentes...'))
            HistoriaClinica.objects.all().delete()

        # Verificar que existan catálogos
        if not CatSexo.objects.exists():
            self.stdout.write(self.style.ERROR('No hay catálogos cargados. Ejecuta primero: python manage.py cargar_catalogos'))
            return

        # Obtener un usuario para auditoría
        user = User.objects.filter(username='sebas').first() or User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No hay usuarios en el sistema. Crea uno con createsuperuser.'))
            return

        nombres = ['Juan', 'María', 'José', 'Ana', 'Luis', 'Guadalupe', 'Francisco', 'Rosa', 'Antonio', 'Leticia', 'Roberto', 'Adriana', 'Miguel', 'Brenda', 'Alejandro', 'Mónica', 'Fernando', 'Silvia', 'Ricardo', 'Graciela']
        apellidos = ['García', 'Hernández', 'Martínez', 'López', 'González', 'Pérez', 'Rodríguez', 'Sánchez', 'Ramírez', 'Cruz', 'Flores', 'Gómez', 'Morales', 'Vázquez', 'Jiménez', 'Reyes', 'Díaz', 'Torres', 'Gutiérrez', 'Ruiz']
        localidades = ['San Luis Potosí', 'Soledad de Graciano Sánchez', 'Ciudad Valles', 'Matehuala', 'Rioverde', 'Tamazunchale', 'Xilitla', 'Santa María del Río']
        agentes = ['Paracetamol', 'Cloro', 'Veneno de Alacrán', 'Aspirina', 'Metformina', 'Insecticida (Organofosforado)', 'Detergente líquido', 'Alcohol etílico', 'Gasolina', 'Mordedura de Serpiente (Ophidicus)']

        # Cache de catálogos para velocidad
        sexos = list(CatSexo.objects.all())
        severidades = list(CatSeveridad.objects.all())
        evoluciones = list(CatEvolucion.objects.all())
        frecuencias = list(CatTipoFrecuencia.objects.all())
        contactos = list(CatTipoContacto.objects.all())
        motivos = list(CatMotivoConsulta.objects.all())
        subtipos_p = list(CatSubtipoPresencial.objects.all())
        cat_interlocutores = list(CatCategoriaInterlocutor.objects.all())
        ub_interlocutores = list(CatUbicacionInterlocutor.objects.all())
        sectores = list(CatSector.objects.all())
        circ_n1 = list(CatCircunstanciaNivel1.objects.all())
        ub_eventos = list(CatUbicacionEvento.objects.all())
        tipos_exp = list(CatTipoExposicion.objects.all())
        tipos_agente = list(CatTipoAgente.objects.all())
        vias = list(CatViaIngreso.objects.all())
        tratamientos = list(CatTratamiento.objects.all())

        self.stdout.write(f'Generando {cantidad} registros...')

        for i in range(cantidad):
            # Generar datos básicos
            nombre = random.choice(nombres)
            apellido = f"{random.choice(apellidos)} {random.choice(apellidos)}"
            sexo = random.choice(sexos)
            
            # Fechas coherentes
            hoy = timezone.now()
            # Fecha de nacimiento (entre 0 y 85 años atrás)
            fecha_nac = (hoy - timedelta(days=random.randint(0, 31000))).date()
            # Fecha de consulta (en el último año)
            fecha_consulta = hoy - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
            # Fecha de exposición (entre 30 min y 2 días antes de la consulta)
            fecha_exposicion = fecha_consulta - timedelta(minutes=random.randint(30, 2880))
            # Fecha de ingreso (si es presencial, 10-60 min después de consulta o exposición)
            fecha_ingreso = fecha_consulta + timedelta(minutes=random.randint(5, 120))

            contacto = random.choice(contactos)
            motivo = random.choice(motivos)
            
            # Crear instancia
            historia = HistoriaClinica(
                folio_expediente=f"TEST-{2026}{i:04d}",
                nombre=nombre,
                apellido=apellido,
                direccion="Calle Falsa 123",
                localidad=random.choice(localidades),
                telefono=f"444{random.randint(1000000, 9999999)}",
                sexo=sexo,
                fecha_nacimiento=fecha_nac,
                escolaridad="Preparatoria",
                tipo_frecuencia=random.choice(frecuencias),
                tipo_contacto=contacto,
                motivo_consulta=motivo,
                fecha_hora_evento_exposicion=fecha_exposicion,
                fecha_hora_consulta=fecha_consulta,
                fecha_hora_ingreso=fecha_ingreso if contacto.nombre.lower() == 'exposición (presencial)' else None,
                subtipo_presencial=random.choice(subtipos_p) if contacto.nombre.lower() == 'exposición (presencial)' else None,
                circunstancia_nivel1=random.choice(circ_n1),
                ubicacion_evento=random.choice(ub_eventos),
                tipo_exposicion=random.choice(tipos_exp),
                tipo_agente=random.choice(tipos_agente),
                agente_principio_activo=random.choice(agentes),
                agente_cantidad_informada="Un poco",
                signos_sintomas="Náuseas, mareos, dolor abdominal.",
                fc=random.randint(60, 120),
                fr=random.randint(12, 25),
                temp=random.uniform(36.0, 39.5),
                sat=random.randint(90, 100),
                ta="120/80",
                severidad=random.choice(severidades),
                evolucion=random.choice(evoluciones),
                hospitalizacion_sala_general=random.choice([True, False]),
                usuario_captura=user,
                firma_responsable="Dr. Prueba Aleatoria"
            )

            # Seleccionar circunstancia nivel 2 coherente con nivel 1
            circ_n2_opciones = list(historia.circunstancia_nivel1.nivel2_opciones.all())
            if circ_n2_opciones:
                historia.circunstancia_nivel2 = random.choice(circ_n2_opciones)

            historia.save() # Llama al save() para calcular edad y latencia

            # ManyToMany: Vías de ingreso
            num_vias = random.randint(1, 2)
            historia.vias_ingreso.set(random.sample(vias, k=min(num_vias, len(vias))))

            # ManyToMany: Tratamientos (Tabla intermedia)
            # Tratamientos previos (A)
            num_t_a = random.randint(1, 3)
            ts_a = random.sample(tratamientos, k=min(num_t_a, len(tratamientos)))
            for t in ts_a:
                HistoriaClinicaTratamiento.objects.create(
                    historia=historia,
                    tratamiento=t,
                    columna='A',
                    especificar="Simulación de prueba" if t.requiere_especificar else ""
                )

            # Tratamientos recomendados (B)
            num_t_b = random.randint(1, 3)
            ts_b = random.sample(tratamientos, k=min(num_t_b, len(tratamientos)))
            for t in ts_b:
                if not HistoriaClinicaTratamiento.objects.filter(historia=historia, tratamiento=t, columna='B').exists():
                    HistoriaClinicaTratamiento.objects.create(
                        historia=historia,
                        tratamiento=t,
                        columna='B',
                        especificar="Recomendación automatizada" if t.requiere_especificar else ""
                    )

            if (i + 1) % 50 == 0:
                self.stdout.write(f'Creados {i + 1} registros...')

        self.stdout.write(self.style.SUCCESS(f'Éxito: Se crearon {cantidad} registros de prueba.'))
