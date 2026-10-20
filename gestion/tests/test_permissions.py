from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from gestion.models import Cargo, Delegacion, Funcionario
from gestion.permissions import funcionarios_visibles


class SGRPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_group = Group.objects.create(name="ADMINISTRADOR")
        self.delegate_group = Group.objects.create(name="DELEGADO")
        self.employee_group = Group.objects.create(name="FUNCIONARIO")
        self.admin = User.objects.create_user("admin", password="test-pass-123")
        self.admin.groups.add(self.admin_group)
        self.delegate = User.objects.create_user("delegate", password="test-pass-123")
        self.delegate.groups.add(self.delegate_group)
        self.employee = User.objects.create_user("employee", password="test-pass-123")
        self.employee.groups.add(self.employee_group)
        self.unassigned = User.objects.create_user("unassigned", password="test-pass-123")
        self.cargo = Cargo.objects.create(nombre="Gestión territorial")
        self.norte = Delegacion.objects.create(nombre="Delegación de prueba norte")
        self.sur = Delegacion.objects.create(nombre="Delegación de prueba sur")
        Funcionario.objects.create(usuario=self.delegate, nombre="Delegado ficticio", cargo=self.cargo, delegacion=self.norte)
        Funcionario.objects.create(usuario=self.employee, nombre="Funcionario ficticio", cargo=self.cargo, delegacion=self.norte)
        self.other_employee = User.objects.create_user("other", password="test-pass-123")
        self.other_employee.groups.add(self.employee_group)
        Funcionario.objects.create(usuario=self.other_employee, nombre="Otro funcionario", cargo=self.cargo, delegacion=self.sur)

    def test_anonymous_user_cannot_open_dashboard(self):
        response = self.client.get(reverse("gestion:dashboard"))

        self.assertRedirects(response, f"{reverse('gestion:login')}?next={reverse('gestion:dashboard')}", fetch_redirect_response=False)

    def test_login_view_renders_username_and_password_inputs(self):
        response = self.client.get(reverse("gestion:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

    def test_user_without_sgr_group_has_no_dashboard_access(self):
        self.client.force_login(self.unassigned)

        response = self.client.get(reverse("gestion:dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_admin_sees_all_staff(self):
        visible = funcionarios_visibles(self.admin)

        self.assertEqual(visible.count(), 3)

    def test_delegate_cannot_read_other_delegation_staff(self):
        visible = funcionarios_visibles(self.delegate)

        self.assertEqual(set(visible.values_list("nombre", flat=True)), {"Delegado ficticio", "Funcionario ficticio"})
        self.assertNotIn(self.other_employee.perfil_sgr, visible)

    def test_dashboard_renders_only_current_delegation_staff(self):
        self.client.force_login(self.delegate)

        response = self.client.get(reverse("gestion:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delegado ficticio")
        self.assertContains(response, "Funcionario ficticio")
        self.assertNotContains(response, "Otro funcionario")

    def test_employee_sees_only_own_profile(self):
        visible = funcionarios_visibles(self.employee)

        self.assertEqual(list(visible.values_list("usuario_id", flat=True)), [self.employee.pk])
