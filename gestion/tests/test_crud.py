from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Servicio


class MasterCrudTests(TestCase):
    def setUp(self):
        User = get_user_model()
        admin_group = Group.objects.create(name="ADMINISTRADOR")
        self.admin = User.objects.create_user("catalog_admin", password="test-pass-123")
        self.admin.groups.add(admin_group)
        self.client.force_login(self.admin)

        self.delegacion = Delegacion.objects.create(nombre="Delegación Base", descripcion_territorial="Zona de prueba")
        self.cargo = Cargo.objects.create(nombre="Cargo Base", area="Territorial")
        self.servicio = Servicio.objects.create(nombre="Servicio Base", descripcion="Descripción base")
        self.funcionario_user = User.objects.create_user("funcionario_base", password="test-pass-123")
        self.new_funcionario_user = User.objects.create_user("funcionario_nuevo", password="test-pass-123")
        self.funcionario = Funcionario.objects.create(
            usuario=self.funcionario_user,
            nombre="Funcionario Base",
            cargo=self.cargo,
            delegacion=self.delegacion,
        )
        self.indicador = Indicador.objects.create(
            nombre="Indicador Base",
            cargo=self.cargo,
            ponderador=50,
            meta_trimestral=8,
            unidad_medida="acciones",
        )
        self.entities = {
            "delegaciones": (Delegacion, self.delegacion),
            "cargos": (Cargo, self.cargo),
            "funcionarios": (Funcionario, self.funcionario),
            "indicadores": (Indicador, self.indicador),
            "servicios": (Servicio, self.servicio),
        }

    def route(self, entity, action, obj=None):
        kwargs = {"pk": obj.pk} if obj is not None else {}
        return reverse(f"maestros:{entity}-{action}", kwargs=kwargs)

    def payload(self, entity, name):
        if entity == "delegaciones":
            return {"nombre": f"Delegación {name}", "descripcion_territorial": "Zona ficticia", "activo": "on"}
        if entity == "cargos":
            return {"nombre": f"Cargo {name}", "area": "Territorial", "activo": "on"}
        if entity == "funcionarios":
            return {
                "usuario": self.new_funcionario_user.pk,
                "nombre": f"Funcionario {name}",
                "cargo": self.cargo.pk,
                "delegacion": self.delegacion.pk,
                "activo": "on",
            }
        if entity == "indicadores":
            return {
                "nombre": f"Indicador {name}",
                "cargo": self.cargo.pk,
                "ponderador": "25.00",
                "meta_trimestral": "10",
                "unidad_medida": "acciones",
                "activo": "on",
            }
        return {"nombre": f"Servicio {name}", "descripcion": "Descripción ficticia", "activo": "on"}

    def test_admin_can_create_each_master_record(self):
        for entity, (model, _) in self.entities.items():
            with self.subTest(entity=entity):
                response = self.client.post(self.route(entity, "crear"), self.payload(entity, "Nuevo"))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(model.objects.count(), 2)
                self.assertTrue(model.objects.filter(nombre__contains="Nuevo").exists())

    def test_admin_can_list_each_master_record(self):
        for entity, (_, obj) in self.entities.items():
            with self.subTest(entity=entity):
                response = self.client.get(self.route(entity, "lista"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, str(obj))

    def test_admin_can_update_each_master_record(self):
        for entity, (model, obj) in self.entities.items():
            with self.subTest(entity=entity):
                response = self.client.post(self.route(entity, "editar", obj), self.payload(entity, "Actualizado"))
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertTrue(model.objects.filter(pk=obj.pk, activo=True).exists())
                self.assertIn("Actualizado", obj.nombre)

    def test_admin_can_deactivate_each_master_record(self):
        for entity, (model, obj) in self.entities.items():
            with self.subTest(entity=entity):
                response = self.client.get(self.route(entity, "desactivar", obj))
                self.assertEqual(response.status_code, 200)
                response = self.client.post(self.route(entity, "desactivar", obj))
                self.assertEqual(response.status_code, 302)
                obj.refresh_from_db()
                self.assertFalse(obj.activo)
                self.assertFalse(self.client.get(self.route(entity, "lista")).context["object_list"].filter(pk=obj.pk).exists())
                self.assertTrue(
                    self.client.get(f"{self.route(entity, 'lista')}?estado=todos").context["object_list"].filter(pk=obj.pk).exists()
                )

    def test_invalid_and_duplicate_forms_do_not_persist(self):
        delegations_before = Delegacion.objects.count()
        duplicate = self.client.post(
            self.route("delegaciones", "crear"),
            {"nombre": self.delegacion.nombre, "descripcion_territorial": "duplicada", "activo": "on"},
        )
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Delegacion.objects.count(), delegations_before)

        indicators_before = Indicador.objects.count()
        invalid_indicator = self.payload("indicadores", "Inválido")
        invalid_indicator["ponderador"] = "101"
        invalid = self.client.post(self.route("indicadores", "crear"), invalid_indicator)
        self.assertEqual(invalid.status_code, 200)
        self.assertEqual(Indicador.objects.count(), indicators_before)

    def test_non_admin_cannot_create_master_record(self):
        User = get_user_model()
        delegate = User.objects.create_user("catalog_delegate", password="test-pass-123")
        delegate.groups.add(Group.objects.create(name="DELEGADO"))
        self.client.force_login(delegate)

        response = self.client.post(self.route("delegaciones", "crear"), self.payload("delegaciones", "No autorizada"))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Delegacion.objects.filter(nombre="Delegación No autorizada").exists())

    def test_crud_post_requires_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)

        response = csrf_client.post(self.route("delegaciones", "crear"), self.payload("delegaciones", "Sin CSRF"))

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Delegacion.objects.filter(nombre="Delegación Sin CSRF").exists())

    def test_deactivation_preserves_relations_and_hides_from_active_lists(self):
        cargo_id = self.cargo.pk

        response = self.client.post(self.route("cargos", "desactivar", self.cargo))

        self.assertEqual(response.status_code, 302)
        self.funcionario.refresh_from_db()
        self.indicador.refresh_from_db()
        self.assertEqual(self.funcionario.cargo_id, cargo_id)
        self.assertEqual(self.indicador.cargo_id, cargo_id)
        self.assertFalse(Cargo.objects.get(pk=cargo_id).activo)
        self.assertFalse(self.client.get(self.route("cargos", "lista")).context["object_list"].filter(pk=cargo_id).exists())
