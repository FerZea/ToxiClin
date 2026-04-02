"""
Pruebas automatizadas para ToxiClin.
Ejecutar con: python manage.py test expedientes
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from expedientes.models import (
    HistoriaClinica, HistoriaClinicaTratamiento,
    CatSexo, CatTipoContacto, CatMotivoConsulta,
    CatSubtipoPresencial, CatTratamiento,
)


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
        data['folio_expediente'] = 'EDITADO'
        data['tratamiento_a'] = [str(trat.pk)]  # incluir el tratamiento

        self.client.post(f'/historias/{self.historia.pk}/editar/', data)
        self.historia.refresh_from_db()

        self.assertEqual(self.historia.folio_expediente, 'EDITADO')
        self.assertEqual(
            self.historia.tratamientos_detalle.filter(columna='A').count(), 1
        )


# ─── Tests de Fase 5: estadísticas y dashboard ───────────────────────────────

class EstadisticasVistaTest(TestCase):
    """
    Verifica:
    - El módulo de estadísticas está restringido a administradoras (@solo_admin).
    - El dashboard es accesible para todos los usuarios autenticados.
    - La exportación de PNG funciona y rechaza variables inválidas.
    - Las funciones de graficas.py no explotan con datos reales.
    """

    def setUp(self):
        self.client = Client()
        self.cats   = crear_catalogos()
        self.admin, self.cap1, _ = crear_usuarios()

        # Crear una historia para que las gráficas tengan algo que dibujar
        ahora = timezone.now()
        HistoriaClinica.objects.create(
            folio_expediente='GRAF-001',
            nombre='Test',
            apellido='Grafica',
            tipo_contacto=self.cats['presencial'],
            motivo_consulta=self.cats['intoxicacion'],
            subtipo_presencial=self.cats['urgencias'],
            fecha_hora_consulta=ahora,
            fecha_hora_ingreso=ahora,
            usuario_captura=self.cap1,
            consulta_numero=99,
        )

    # ── Restricción de acceso ────────────────────────────────────────────────

    def test_estadisticas_sin_login_redirige(self):
        """Sin sesión, estadísticas redirige al login."""
        resp = self.client.get(reverse('estadisticas'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp['Location'])

    def test_estadisticas_capturista_redirige_a_dashboard(self):
        """Un capturista no puede entrar a estadísticas."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(reverse('estadisticas'))
        # @solo_admin redirige al dashboard con mensaje de error
        self.assertRedirects(resp, reverse('dashboard'))

    def test_estadisticas_admin_accede(self):
        """Una administradora puede ver la página de estadísticas."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(reverse('estadisticas'))
        self.assertEqual(resp.status_code, 200)

    # ── Dashboard accesible para todos ──────────────────────────────────────

    def test_dashboard_accesible_capturista(self):
        """El dashboard (RF-27) es visible para cualquier usuario autenticado."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_contiene_total(self):
        """El dashboard muestra el total de registros correcto."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, '1')   # hay 1 historia creada en setUp

    def test_dashboard_muestra_anio_actual(self):
        """El dashboard usa la redacción del año calendario actual."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, 'Tendencia mensual (año actual)')

    # ── Generación de gráficas con variables ────────────────────────────────

    def test_estadisticas_con_variable_barras(self):
        """Seleccionar una variable genera la gráfica sin error."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('estadisticas') + '?variables=tipo_contacto&tipo_grafica=barras'
        )
        self.assertEqual(resp.status_code, 200)
        # Debe haber exactamente un resultado
        self.assertEqual(len(resp.context['resultados']), 1)

    def test_estadisticas_incluye_edad_por_rangos(self):
        """La variable edad_rango existe y puede procesarse como gráfica individual."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('estadisticas') + '?variables=edad_rango&tipo_grafica=barras'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('edad_rango', resp.context['variables_disp'])
        self.assertEqual(len(resp.context['resultados']), 1)

    def test_estadisticas_con_cruce_barras_agrupadas(self):
        """
        Seleccionar 2 variables con tipo barras_agrupadas genera
        un resultado de cruce (es_cruce=True).
        """
        # Necesitamos catálogos de sexo para que haya cruce real
        CatSexo.objects.get_or_create(nombre='Masculino', defaults={'codigo': 1})
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('estadisticas')
            + '?variables=tipo_contacto&variables=sexo&tipo_grafica=barras_agrupadas'
        )
        self.assertEqual(resp.status_code, 200)
        resultados = resp.context['resultados']
        self.assertGreater(len(resultados), 0)
        # El primer resultado debe ser el cruce
        self.assertTrue(resultados[0]['es_cruce'])

    def test_estadisticas_limite_4_variables(self):
        """No se procesan más de 4 variables aunque se envíen más."""
        self.client.login(username='admin_t', password='admin1234test')
        params = ('variables=tipo_agente&variables=sexo&variables=severidad'
                  '&variables=evolucion&variables=circunstancia')
        resp = self.client.get(reverse('estadisticas') + '?' + params)
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(resp.context['variables_sel']), 4)

    # ── Exportación PNG ──────────────────────────────────────────────────────

    def test_exportar_variable_invalida_404(self):
        """Una variable inexistente devuelve 404."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('exportar_grafica') + '?variable=no_existe'
        )
        self.assertEqual(resp.status_code, 404)

    def test_exportar_capturista_bloqueado(self):
        """Un capturista no puede descargar gráficas."""
        self.client.login(username='cap1_t', password='cap1234test')
        resp = self.client.get(
            reverse('exportar_grafica') + '?variable=tipo_contacto'
        )
        self.assertRedirects(resp, reverse('dashboard'))

    def test_exportar_png_admin(self):
        """Admin descarga PNG correctamente (content-type image/png)."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('exportar_grafica') + '?variable=tipo_contacto&tipo_grafica=barras'
        )
        # Con datos existentes debe devolver 200 y PNG
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/png')

    def test_exportar_jpg_admin(self):
        """Admin descarga JPG correctamente (content-type image/jpeg)."""
        self.client.login(username='admin_t', password='admin1234test')
        resp = self.client.get(
            reverse('exportar_grafica')
            + '?variable=tipo_contacto&tipo_grafica=barras&formato=jpg'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'image/jpeg')
