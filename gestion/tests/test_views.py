from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Servicio


class SGRViewTests(TestCase):
    pages = {
        "gestion:dashboard": "Resumen de gestión",
        "gestion:ficha": "Ficha del funcionario",
        "gestion:tubo": "Agenda de compromisos",
        "gestion:semaforo": "Semáforo diario",
        "gestion:resumen": "Resumen territorial",
    }

    def setUp(self):
        User = get_user_model()
        employee_group, _ = Group.objects.get_or_create(name="FUNCIONARIO")
        self.user = User.objects.create_user("vista_demo", password="test-pass-123")
        self.user.groups.add(employee_group)
        self.delegacion = Delegacion.objects.create(nombre="Delegación vista de prueba")
        self.cargo = Cargo.objects.create(nombre="Cargo vista de prueba")
        Funcionario.objects.create(
            usuario=self.user,
            nombre="Funcionario demostrativo",
            cargo=self.cargo,
            delegacion=self.delegacion,
        )
        Indicador.objects.create(
            nombre="Indicador de prueba",
            cargo=self.cargo,
            ponderador=100,
            meta_trimestral=10,
            unidad_medida="acciones",
        )
        Servicio.objects.create(nombre="Servicio de prueba")
        self.client.force_login(self.user)

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_health_check_is_public_and_get_only(self):
        anonymous = Client()
        response = anonymous.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(anonymous.post("/health/").status_code, 405)

    def test_each_sgr_template_renders_for_authenticated_user(self):
        for route_name, heading in self.pages.items():
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)

    def test_sgr_views_use_persisted_data_without_demo_label(self):
        for route_name in self.pages:
            with self.subTest(route=route_name):
                self.assertNotContains(self.client.get(reverse(route_name)), "Datos de demostración")

    def test_anonymous_users_cannot_open_sgr_views(self):
        anonymous = Client()
        for route_name in self.pages:
            with self.subTest(route=route_name):
                response = anonymous.get(reverse(route_name))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("gestion:login")))

    def test_employee_cannot_open_another_employees_ficha_by_changing_url(self):
        User = get_user_model()
        other = User.objects.create_user("otro_funcionario", password="test-pass-123")
        other.groups.add(Group.objects.get(name="FUNCIONARIO"))
        other_delegation = Delegacion.objects.create(nombre="Delegación ajena de prueba")
        Funcionario.objects.create(
            usuario=other,
            nombre="Perfil que no debe aparecer",
            cargo=self.cargo,
            delegacion=other_delegation,
        )

        response = self.client.get(f"{reverse('gestion:ficha')}?funcionario={other.perfil_sgr.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Funcionario demostrativo")
        self.assertNotContains(response, "Perfil que no debe aparecer")

    def test_operational_views_reject_transaction_posts(self):
        for route_name in self.pages:
            with self.subTest(route=route_name):
                self.assertEqual(self.client.post(reverse(route_name), {"actividad": "No debe guardarse"}).status_code, 405)
