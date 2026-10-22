from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

# Si la ruta de cierre de sesion tiene otro nombre en gestion/urls.py,
# cambiar solo esta constante (ver instrucciones de entrega).
LOGOUT_URL_NAME = "gestion:logout"


class LoginLogoutTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.group = Group.objects.create(name="ADMINISTRADOR")
        self.user = User.objects.create_user("usuario_prueba", password="test-pass-123")
        self.user.groups.add(self.group)
        self.inactive = User.objects.create_user(
            "usuario_inactivo", password="test-pass-123", is_active=False
        )
        self.login_url = reverse("gestion:login")
        self.dashboard_url = reverse("gestion:dashboard")

    def _is_authenticated(self):
        return "_auth_user_id" in self.client.session

    def test_login_with_valid_credentials_redirects_to_dashboard(self):
        """CP-LOGIN-002: credenciales validas inician sesion y redirigen al resumen."""
        response = self.client.post(
            self.login_url, {"username": "usuario_prueba", "password": "test-pass-123"}
        )

        self.assertRedirects(response, self.dashboard_url, fetch_redirect_response=False)
        self.assertTrue(self._is_authenticated())

    def test_login_rejects_wrong_password(self):
        """CP-LOGIN-003: contrasena incorrecta no inicia sesion."""
        response = self.client.post(
            self.login_url, {"username": "usuario_prueba", "password": "contrasena-incorrecta"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self._is_authenticated())

    def test_login_rejects_nonexistent_user(self):
        """CP-LOGIN-004: usuario inexistente no inicia sesion."""
        response = self.client.post(
            self.login_url, {"username": "usuario_ficticio_inexistente", "password": "cualquiera-123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self._is_authenticated())

    def test_login_rejects_inactive_account(self):
        """CP-LOGIN-005: cuenta inactiva no inicia sesion aunque las credenciales sean correctas."""
        response = self.client.post(
            self.login_url, {"username": "usuario_inactivo", "password": "test-pass-123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self._is_authenticated())

    def test_logout_ends_session_and_protects_dashboard(self):
        """CP-LOGIN-006: al cerrar sesion se pierde el acceso a paginas protegidas."""
        self.client.force_login(self.user)
        self.assertTrue(self._is_authenticated())

        response = self.client.post(reverse(LOGOUT_URL_NAME))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self._is_authenticated())
        protected = self.client.get(self.dashboard_url)
        self.assertRedirects(
            protected,
            f"{self.login_url}?next={self.dashboard_url}",
            fetch_redirect_response=False,
        )
