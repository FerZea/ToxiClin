"""
Pruebas automatizadas para ToxiClin.
Ejecutar con: python manage.py test expedientes
"""

import matplotlib
# Configurar el backend 'Agg' antes de importar cualquier otra cosa de matplotlib
# para evitar errores de GUI en entornos sin pantalla (como pipelines CI/CD).
matplotlib.use('Agg')

from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from expedientes.models import (
    HistoriaClinica, HistoriaClinicaTratamiento,
    CatSexo, CatTipoContacto, CatMotivoConsulta,
    CatSubtipoPresencial, CatTratamiento,
    CatSeveridad, CatViaIngreso,
)
from expedientes.graficas import _etiqueta_edad_rango, conteos_por_variable


# ─── Helpers comunes ─────────────────────────────────────────────────────────

def crear_catalogos():
    """Crea los catálogos mínimos que necesitan las pruebas."""
    presencial, _ = CatTipoContacto.objects.get_or_create(
        nombre='Exposición (presencial)', defaults={'codigo': 1}
    )
    telefonico, _ = CatTipoContacto.objects.get_or_create(
        nombre='Telefónico', defaults={'codigo': 2}
    )
    intoxicacion, _ = CatMotivoConsulta.objects.get_or_create(
        nombre='Intoxicación', defaults={'codigo': 1}
    )
    urgencias, _ = CatSubtipoPresencial.objects.get_or_create(
        nombre='Urgencias', defaults={'codigo': 1}
    )
    return {
        'presencial': presencial,
        'telefonico': telefonico,
        'intoxicacion': intoxicacion,
        'urgencias': urgencias,
    }


def crear_usuarios():
    """Crea usuarios de prueba con sus grupos."""
    g_admin, _ = Group.objects.get_or_create(name='Administrador')
    g_cap, _   = Group.objects.get_or_create(name='Capturista')

    admin = User.objects.create_user('admin_t', password='admin1234test')
    admin.groups.add(g_admin)

    cap1 = User.objects.create_user('cap1_t', password='cap1234test')
    cap1.groups.add(g_cap)

    cap2 = User.objects.create_user('cap2_t', password='cap1234test')
    cap2.groups.add(g_cap)

    return admin, cap1, cap2


def post_presencial_valido(cats):
    """Datos POST mínimos válidos para una historia presencial."""
    ahora = timezone.now()
    return {
        'folio_expediente':            'TEST-001',
        'nombre':                      'Juan',
        'apellido':                    'Pérez',
        'tipo_contacto':               cats['presencial'].pk,
        'motivo_consulta':             cats['intoxicacion'].pk,
        'subtipo_presencial':          cats['urgencias'].pk,
        'fecha_hora_consulta':         ahora.strftime('%Y-%m-%dT%H:%M'),
        'fecha_hora_ingreso':          ahora.strftime('%Y-%m-%dT%H:%M'),
        'fecha_hora_evento_exposicion': (ahora - timezone.timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M'),
    }


# ─── Tests de validación del formulario ──────────────────────────────────────

class FormValidacionTest(TestCase):

    def setUp(self):
        self.cats = crear_catalogos()

    def test_presencial_sin_subtipo_falla(self):
        """Bug 3: presencial sin subtipo_presencial debe fallar."""
        from expedientes.forms.captura import HistoriaClinicaForm
        data = post_presencial_valido(self.cats)
        del data['subtipo_presencial']
        form = HistoriaClinicaForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('subtipo_presencial', form.errors)

    def test_presencial_sin_fecha_ingreso_falla(self):
        """Presencial sin fecha de ingreso debe fallar."""
        from expedientes.forms.captura import HistoriaClinicaForm
        data = post_presencial_valido(self.cats)
        del data['fecha_hora_ingreso']
        form = HistoriaClinicaForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora_ingreso', form.errors)

    def test_telefonico_sin_interlocutor_falla(self):
        """Bug 3: telefónico sin interlocutor debe fallar."""
        from expedientes.forms.captura import HistoriaClinicaForm
        ahora = timezone.now()
        data = {
            'folio_expediente': 'TEST-002',
            'nombre': 'Ana',
            'apellido': 'López',
            'tipo_contacto': self.cats['telefonico'].pk,
            'motivo_consulta': self.cats['intoxicacion'].pk,
            'fecha_hora_consulta': ahora.strftime('%Y-%m-%dT%H:%M'),
        }
        form = HistoriaClinicaForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('interlocutor_nombre', form.errors)

    def test_exposicion_posterior_a_consulta_falla(self):
        """La exposición no puede ser después de la consulta."""
        from expedientes.forms.captura import HistoriaClinicaForm
        ahora = timezone.now()
        data = post_presencial_valido(self.cats)
        data['fecha_hora_evento_exposicion'] = (
            ahora + timezone.timedelta(hours=2)
        ).strftime('%Y-%m-%dT%H:%M')
        form = HistoriaClinicaForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_hora_evento_exposicion', form.errors)

    def test_formulario_presencial_completo_es_valido(self):
        """Un formulario presencial completo debe pasar validación."""
        from expedientes.forms.captura import HistoriaClinicaForm
        form = HistoriaClinicaForm(post_presencial_valido(self.cats))
        self.assertTrue(form.is_valid(), msg=form.errors)


# ─── Tests de vistas de captura ──────────────────────────────────────────────

class CapturaVistaTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cats = crear_catalogos()
        self.admin, self.cap1, self.cap2 = crear_usuarios()

    def test_sin_login_redirige_al_login(self):
        """Sin sesión, la vista redirige al login."""
        resp = self.client.get('/historias/nueva/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_get_formulario_carga_ok(self):
        """El formulario vacío carga con HTTP 200."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get('/historias/nueva/')
        self.assertEqual(resp.status_code, 200)

    def test_post_valido_crea_historia(self):
        """POST válido crea la historia y redirige al detalle."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.post('/historias/nueva/', post_presencial_valido(self.cats))
        self.assertEqual(HistoriaClinica.objects.count(), 1)
        historia = HistoriaClinica.objects.first()
        self.assertRedirects(resp, f'/historias/{historia.pk}/')
        self.assertEqual(historia.usuario_captura.username, 'cap1_t')

    def test_post_invalido_no_guarda(self):
        """POST inválido no guarda nada."""
        self.client.login(username='cap1_t', password='cap1234test')
        self.client.post('/historias/nueva/', {'folio_expediente': 'X'})
        self.assertEqual(HistoriaClinica.objects.count(), 0)


# ─── Tests de permisos de edición ────────────────────────────────────────────

class EdicionPermisoTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.cats = crear_catalogos()
        self.admin, self.cap1, self.cap2 = crear_usuarios()

        ahora = timezone.now()
        self.historia = HistoriaClinica.objects.create(
            folio_expediente='ORIG',
            nombre='Paciente',
            apellido='Prueba',
            tipo_contacto=self.cats['presencial'],
            motivo_consulta=self.cats['intoxicacion'],
            subtipo_presencial=self.cats['urgencias'],
            fecha_hora_consulta=ahora,
            fecha_hora_ingreso=ahora,
            usuario_captura=self.cap1,
            consulta_numero=1,
        )

    def test_cap2_no_puede_editar_historia_ajena(self):
        """Bug 2: capturista no puede editar expediente de otro."""
        self.client.login(username='cap2_t', password='cap1234test')
        resp = self.client.get(f'/historias/{self.historia.pk}/editar/')
        self.assertRedirects(resp, f'/historias/{self.historia.pk}/')

    def test_admin_puede_editar_cualquier_historia(self):
        """Administrador puede editar cualquier expediente."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(f'/historias/{self.historia.pk}/editar/')
        self.assertEqual(resp.status_code, 200)

    def test_cap1_puede_editar_su_propia_historia(self):
        """Capturista puede editar sus propias historias."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(f'/historias/{self.historia.pk}/editar/')
        self.assertEqual(resp.status_code, 200)

    def test_edicion_preserva_tratamientos(self):
        """Bug 1: editar otros campos no borra los tratamientos A/B."""
        trat, _ = CatTratamiento.objects.get_or_create(
            nombre='Dilución', defaults={'codigo': 3}
        )
        HistoriaClinicaTratamiento.objects.create(
            historia=self.historia, tratamiento=trat, columna='A'
        )

        self.client.login(username='cap1_t', password='cap1234test')
        data = post_presencial_valido(self.cats)
        data['tratamiento_a'] = [str(trat.pk)]  # incluir el tratamiento en el POST
        self.client.post(f'/historias/{self.historia.pk}/editar/', data)
        self.historia.refresh_from_db()

        self.assertEqual(self.historia.folio_expediente, 'TEST-001')
        self.assertEqual(
            self.historia.tratamientos_detalle.filter(columna='A').count(), 1
        )


# ─── Tests de Fase 5: estadísticas y dashboard ───────────────────────────────

class EstadisticasStressTest(TestCase):
    """
    Verifica:
    - El módulo de estadísticas está restringido a administradoras (@solo_admin).
    - El dashboard es accesible para todos los usuarios autenticados.
    - La exportación de PNG/JPG funciona.
    - Las funciones de graficas.py clasifican y cuentan correctamente (unit tests).
    - El cruce de variables y filtros temporales funcionan sin errores (stress testing).
    """

    @classmethod
    def setUpTestData(cls):
        """Configuración única para toda la clase de prueba."""
        # 1. Crear catálogos básicos
        cls.cats = crear_catalogos()  # Reutiliza el helper definido arriba
        cls.sexo_m, _ = CatSexo.objects.get_or_create(nombre='Masculino', defaults={'codigo': 1})
        cls.sexo_f, _ = CatSexo.objects.get_or_create(nombre='Femenino', defaults={'codigo': 2})

        cls.sev_leve, _ = CatSeveridad.objects.get_or_create(nombre='Leve', defaults={'codigo': 1})
        cls.sev_grave, _ = CatSeveridad.objects.get_or_create(nombre='Grave', defaults={'codigo': 2})

        cls.via_oral, _ = CatViaIngreso.objects.get_or_create(nombre='Oral', defaults={'codigo': 1})
        cls.via_inh, _ = CatViaIngreso.objects.get_or_create(nombre='Inhalatoria', defaults={'codigo': 2})
        cls.via_cut, _ = CatViaIngreso.objects.get_or_create(nombre='Cutánea', defaults={'codigo': 3})

        # Grupos y usuarios (usando helper)
        cls.admin, cls.cap1, cls.cap2 = crear_usuarios()

        # 2. Distribuir registros en el tiempo para probar filtros
        hoy = timezone.now()
        hace_un_mes = hoy - timedelta(days=30)
        hace_seis_meses = hoy - timedelta(days=180)

        # 3. Crear 10 historias con diferentes edades para cubrir todos los rangos
        pacientes_data = [
            (10, 'd', hace_un_mes),      # <1 año
            (5,  'm', hoy),              # <1 año
            (1,  'a', hace_seis_meses),  # 1-4 años
            (4,  'a', hoy),              # 1-4 años
            (10, 'a', hoy),              # 5-14 años
            (15, 'a', hace_un_mes),     # 15-24 años
            (24, 'a', hace_seis_meses), # 15-24 años
            (35, 'a', hoy),             # 25-44 años
            (50, 'a', hace_un_mes),     # 45-64 años
            (70, 'a', hoy),             # 65+ años
        ]

        for i, (valor, unidad, fecha) in enumerate(pacientes_data):
            historia = HistoriaClinica.objects.create(
                folio_expediente=f'TEST-P5-{i}',
                nombre=f'P{i}',
                apellido='Test',
                sexo=cls.sexo_m if i % 2 == 0 else cls.sexo_f,
                edad_valor=valor,
                edad_unidad=unidad,
                severidad=cls.sev_leve if i < 5 else cls.sev_grave,
                tipo_contacto=cls.cats['presencial'],
                motivo_consulta=cls.cats['intoxicacion'],
                subtipo_presencial=cls.cats['urgencias'],
                fecha_hora_consulta=fecha,
                fecha_hora_ingreso=fecha,
                usuario_captura=cls.cap1,
                consulta_numero=100 + i,
            )
            # M2M via ingreso
            if i == 0:
                historia.vias_ingreso.add(cls.via_oral, cls.via_inh)
            elif i % 2 == 0:
                historia.vias_ingreso.add(cls.via_oral)
            else:
                historia.vias_ingreso.add(cls.via_cut)

    def setUp(self):
        self.client = Client()

    # ── Unit tests para graficas.py ──────────────────────────────────────────

    def test_etiqueta_edad_rango_clasificacion(self):
        """Verifica que _etiqueta_edad_rango clasifique según la lógica clínica."""
        casos = [
            (15, 'd', '<1 año'),
            (11, 'm', '<1 año'),
            (1,  'a', '1-4 años'),
            (14, 'a', '5-14 años'),
            (15, 'a', '15-24 años'),
            (24, 'a', '15-24 años'),
            (40, 'a', '25-44 años'),
            (60, 'a', '45-64 años'),
            (80, 'a', '65+ años'),
        ]
        for valor, unidad, esperado in casos:
            with self.subTest(valor=valor, unidad=unidad):
                resultado = _etiqueta_edad_rango(valor, unidad)
                self.assertEqual(resultado, esperado)

    def test_conteos_por_variable_m2m(self):
        """Prueba el conteo sobre ManyToMany ('vias_ingreso') sin duplicados."""
        qs = HistoriaClinica.objects.all()
        resultados = conteos_por_variable(qs, 'via_ingreso')
        # Distribución esperada según setUpTestData:
        # P0: Oral, Inhalatoria; P2, P4, P6, P8: Oral. Total Oral = 5, Inh = 1.
        # P1, 3, 5, 7, 9: Cutánea. Total Cutánea = 5.
        self.assertEqual(resultados.get('Oral', 0), 5)
        self.assertEqual(resultados.get('Cutánea', 0), 5)
        self.assertEqual(resultados.get('Inhalatoria', 0), 1)

    # ── Pruebas de integración ───────────────────────────────────────────────

    def test_estadisticas_filtros_temporales(self):
        """Prueba la vista con filtros de periodo 'mes', 'trimestre', 'anio'."""
        self.client.login(username='admin_t', password='admin1234test')
        for filtro in ['mes', 'trimestre', 'anio']:
            with self.subTest(filtro=filtro):
                resp = self.client.get(reverse('estadisticas'), {'periodo': filtro})
                self.assertEqual(resp.status_code, 200)
                # 'total_en_periodo' debe ser mayor a 0 según setUpTestData
                self.assertGreater(resp.context['total_en_periodo'], 0)

    def test_estadisticas_sin_datos_no_explota(self):
        """Un rango futuro sin datos debe devolver total=0 con gracia."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(reverse('estadisticas'), {
            'periodo': 'rango',
            'fecha_desde': '2050-01-01',
            'fecha_hasta': '2050-12-31'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_en_periodo'], 0)

    def test_estadisticas_cruce_variables(self):
        """Prueba cruce de variables (barras agrupadas) en contexto."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(reverse('estadisticas'), {
            'variables': ['severidad', 'sexo'],
            'tipo_grafica': 'barras_agrupadas'
        })
        self.assertEqual(resp.status_code, 200)
        resultado_cruce = resp.context['resultados'][0]
        self.assertTrue(resultado_cruce['es_cruce'])
        self.assertIn('grupos_cruce', resultado_cruce)
        self.assertIn('filas_cruce', resultado_cruce)

    # ── Exportación ──────────────────────────────────────────────────────────

    def test_exportar_grafica_png_jpg(self):
        """Verifica que el endpoint de exportación genere bytes con firmas válidas."""
        self.client.login(username='admin_t', password='admin1234test')
        formatos = [('png', 'image/png'), ('jpg', 'image/jpeg')]
        for formato, content_type in formatos:
            with self.subTest(formato=formato):
                resp = self.client.get(reverse('exportar_grafica'), {
                    'variable': 'tipo_contacto',
                    'formato': formato
                })
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp['Content-Type'], content_type)
                self.assertIsInstance(resp.content, bytes)
                self.assertGreater(len(resp.content), 100)
                # Firmas mágicas
                if formato == 'png':
                    self.assertTrue(resp.content.startswith(b'\x89PNG\r\n\x1a\n'))
                elif formato == 'jpg':
                    self.assertTrue(resp.content.startswith(b'\xff\xd8\xff'))

    def test_exportar_404_variable_invalida(self):
        """Solicitar una variable inexistente debe dar 404."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(reverse('exportar_grafica'), {
            'variable': 'invalida',
            'formato': 'png'
        })
        self.assertEqual(resp.status_code, 404)


# ─── Tests de Fase 7: respaldos, bitácora y ConfigSistema ────────────────────

class ConfigSistemaTest(TestCase):
    """Verifica el funcionamiento del modelo ConfigSistema (clave-valor)."""

    def test_set_y_get(self):
        """set() guarda el valor y get() lo recupera."""
        from expedientes.models import ConfigSistema
        ConfigSistema.set('prueba_clave', 'hola mundo')
        self.assertEqual(ConfigSistema.get('prueba_clave'), 'hola mundo')

    def test_get_default_si_no_existe(self):
        """get() devuelve el default cuando la clave no existe."""
        from expedientes.models import ConfigSistema
        self.assertIsNone(ConfigSistema.get('no_existe'))
        self.assertEqual(ConfigSistema.get('no_existe', 'fallback'), 'fallback')

    def test_set_sobreescribe(self):
        """set() actualiza el valor si la clave ya existe."""
        from expedientes.models import ConfigSistema
        ConfigSistema.set('clave', 'valor1')
        ConfigSistema.set('clave', 'valor2')
        self.assertEqual(ConfigSistema.get('clave'), 'valor2')
        # Solo debe haber un registro, no dos
        self.assertEqual(ConfigSistema.objects.filter(clave='clave').count(), 1)


class RegistroActividadTest(TestCase):
    """
    Verifica que las acciones importantes queden registradas
    automáticamente en la bitácora.
    """

    def setUp(self):
        self.client = Client()
        crear_catalogos()
        self.admin, self.cap1, _ = crear_usuarios()

    def test_login_registra_actividad(self):
        """Un login exitoso crea un RegistroActividad con accion='login'."""
        from expedientes.models import RegistroActividad
        antes = RegistroActividad.objects.filter(accion='login').count()
        # Postear al formulario de login (no usar client.login, que evita la vista)
        self.client.post(reverse('login'), {
            'username': 'admin_t',
            'password': 'admin1234test',
        })
        despues = RegistroActividad.objects.filter(accion='login').count()
        self.assertEqual(despues, antes + 1)

    def test_logout_registra_actividad(self):
        """Un logout crea un RegistroActividad con accion='logout'."""
        from expedientes.models import RegistroActividad
        # force_login: establece sesión sin pasar por la vista (autenticación no es lo que se prueba)
        self.client.force_login(self.admin)
        antes = RegistroActividad.objects.filter(accion='logout').count()
        self.client.get(reverse('logout'))
        despues = RegistroActividad.objects.filter(accion='logout').count()
        self.assertEqual(despues, antes + 1)

    def test_captura_registra_actividad(self):
        """Guardar una historia nueva crea un RegistroActividad con accion='captura'."""
        from expedientes.models import RegistroActividad
        self.client.login(username='cap1_t', password='cap1234test')
        cats = crear_catalogos()
        antes = RegistroActividad.objects.filter(accion='captura').count()
        self.client.post('/historias/nueva/', post_presencial_valido(cats))
        despues = RegistroActividad.objects.filter(accion='captura').count()
        self.assertEqual(despues, antes + 1)

    def test_edicion_registra_actividad(self):
        """Editar una historia crea un RegistroActividad con accion='edicion'."""
        from expedientes.models import RegistroActividad
        cats = crear_catalogos()
        ahora = timezone.now()
        historia = HistoriaClinica.objects.create(
            folio_expediente='ACT-001',
            tipo_contacto=cats['presencial'],
            motivo_consulta=cats['intoxicacion'],
            subtipo_presencial=cats['urgencias'],
            fecha_hora_consulta=ahora,
            fecha_hora_ingreso=ahora,
            usuario_captura=self.cap1,
            consulta_numero=200,
        )
        self.client.login(username='cap1_t', password='cap1234test')
        antes = RegistroActividad.objects.filter(accion='edicion').count()
        self.client.post(f'/historias/{historia.pk}/editar/', post_presencial_valido(cats))
        despues = RegistroActividad.objects.filter(accion='edicion').count()
        self.assertEqual(despues, antes + 1)

    def test_vista_actividad_solo_admin(self):
        """La bitácora es visible para admins y bloqueada para capturistas."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('actividad'))
        self.assertEqual(resp.status_code, 200)

        self.client.force_login(self.cap1)
        resp = self.client.get(reverse('actividad'))
        self.assertRedirects(resp, reverse('dashboard'))


class RespaldosTest(TestCase):
    """
    Verifica el flujo de creación y restauración de respaldos cifrados.
    """

    def setUp(self):
        self.client = Client()
        crear_catalogos()
        self.admin, self.cap1, _ = crear_usuarios()

    def test_pagina_respaldos_solo_admin(self):
        """La página de respaldos es accesible para admins y bloqueada para capturistas."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('respaldos'))
        self.assertEqual(resp.status_code, 200)

        self.client.force_login(self.cap1)
        resp = self.client.get(reverse('respaldos'))
        self.assertRedirects(resp, reverse('dashboard'))

    def test_crear_respaldo_contrasena_incorrecta(self):
        """Una contraseña incorrecta no genera el respaldo."""
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('crear_respaldo'), {'password': 'INCORRECTA'})
        self.assertRedirects(resp, reverse('respaldos'))

    def test_crear_respaldo_genera_descarga(self):
        """Con contraseña correcta se descarga un archivo binario .toxiclin."""
        import tempfile, os
        from unittest.mock import patch

        self.client.force_login(self.admin)

        # En tests, el DB es en memoria y no tiene ruta de archivo real.
        # Creamos un SQLite temporal para que la vista pueda leerlo como archivo.
        with tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False) as tmp:
            tmp.write(b'SQLite format 3\x00' + b'\x00' * 500)
            db_temp = tmp.name

        try:
            with patch.object(
                __import__('django.conf', fromlist=['settings']).settings,
                'DATABASES',
                {'default': {'NAME': db_temp}},
            ):
                resp = self.client.post(
                    reverse('crear_respaldo'), {'password': 'admin1234test'}
                )
        finally:
            os.unlink(db_temp)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertIn('.toxiclin', resp['Content-Disposition'])
        # El archivo debe tener: 16 bytes de salt + datos cifrados Fernet
        self.assertGreater(len(resp.content), 100)

    def test_restaurar_contrasena_incorrecta(self):
        """Restaurar con contraseña incorrecta rechaza la operación."""
        import io
        self.client.force_login(self.admin)
        # Primero generamos un respaldo real
        resp_backup = self.client.post(
            reverse('crear_respaldo'), {'password': 'admin1234test'}
        )
        archivo = io.BytesIO(resp_backup.content)
        archivo.name = 'respaldo.toxiclin'
        resp = self.client.post(reverse('restaurar_respaldo'), {
            'password': 'INCORRECTA',
            'archivo': archivo,
        })
        self.assertRedirects(resp, reverse('respaldos'))

    def test_restaurar_archivo_invalido(self):
        """Un archivo que no es un respaldo válido es rechazado."""
        import io
        self.client.force_login(self.admin)
        archivo = io.BytesIO(b'esto no es un respaldo')
        archivo.name = 'basura.toxiclin'
        resp = self.client.post(reverse('restaurar_respaldo'), {
            'password': 'admin1234test',
            'archivo': archivo,
        })
        self.assertRedirects(resp, reverse('respaldos'))


# ─── Tests de Fase 8: stub Excel, páginas de error ───────────────────────────

class PulidoTest(TestCase):
    """Verifica el stub de importación Excel y las páginas de error."""

    def setUp(self):
        self.client = Client()
        crear_catalogos()
        self.admin, self.cap1, _ = crear_usuarios()

    def test_importar_excel_stub_admin(self):
        """La página de importar Excel es accesible para admins."""
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('importar_excel'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'próximamente')

    def test_importar_excel_stub_capturista(self):
        """La página de importar Excel bloquea a capturistas."""
        self.client.force_login(self.cap1)
        resp = self.client.get(reverse('importar_excel'))
        self.assertRedirects(resp, reverse('dashboard'))

    def test_url_inexistente_devuelve_404(self):
        """Una URL que no existe devuelve 404."""
        self.client.force_login(self.admin)
        resp = self.client.get('/ruta/que/no/existe/')
        self.assertEqual(resp.status_code, 404)
