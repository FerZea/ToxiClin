"""
Pruebas automatizadas para ToxiClin.
Ejecutar con: python manage.py test expedientes
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
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
