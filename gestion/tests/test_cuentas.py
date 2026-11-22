from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from gestion.models import PerfilUsuario

User = get_user_model()


class RecuperacionClaveTests(TestCase):
    def test_envia_correo_si_la_cuenta_existe(self):
        User.objects.create_user("u1", email="u1@example.com", password="x12345678")
        r = self.client.post(reverse("password_reset"), {"email": "u1@example.com"})
        self.assertRedirects(r, reverse("password_reset_done"), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/recuperar/", mail.outbox[0].body)

    def test_no_revela_si_el_correo_no_existe(self):
        r = self.client.post(reverse("password_reset"), {"email": "nadie@example.com"})
        self.assertRedirects(r, reverse("password_reset_done"), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)


class CambioClaveObligatorioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("u2", password="x12345678")
        PerfilUsuario.objects.create(usuario=self.user, debe_cambiar_clave=True)
        self.client.login(username="u2", password="x12345678")

    def test_cuenta_con_clave_temporal_va_a_cambiar_clave(self):
        r = self.client.get("/tareas/")
        self.assertRedirects(r, reverse("cambiar_clave"), fetch_redirect_response=False)

    def test_al_cambiar_la_clave_se_libera_la_cuenta(self):
        r = self.client.post(reverse("cambiar_clave"), {
            "old_password": "x12345678",
            "new_password1": "NuevaClave#2026x",
            "new_password2": "NuevaClave#2026x",
        })
        self.assertEqual(r.status_code, 302)
        self.assertFalse(PerfilUsuario.objects.get(usuario=self.user).debe_cambiar_clave)


class AccionClaveTemporalTests(TestCase):
    def test_admin_asigna_clave_temporal(self):
        User.objects.create_superuser("adm", "a@example.com", "x12345678")
        objetivo = User.objects.create_user("obj", password="x12345678")
        self.client.login(username="adm", password="x12345678")
        r = self.client.post(reverse("admin:auth_user_changelist"), {
            "action": "asignar_clave_temporal",
            "_selected_action": [objetivo.pk],
        })
        self.assertEqual(r.status_code, 302)
        objetivo.refresh_from_db()
        self.assertFalse(objetivo.check_password("x12345678"))
        self.assertTrue(PerfilUsuario.objects.get(usuario=objetivo).debe_cambiar_clave)