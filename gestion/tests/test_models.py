from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Servicio


class CatalogNameTests(TestCase):
    def test_master_catalog_names_are_unique(self):
        delegation = Delegacion.objects.create(nombre="Centro")
        cargo = Cargo.objects.create(nombre="Coordinación", area="Territorial")
        service = Servicio.objects.create(nombre="Atención vecinal")

        with self.assertRaises(ValidationError):
            Delegacion(nombre=delegation.nombre).full_clean()
        with self.assertRaises(ValidationError):
            Cargo(nombre=cargo.nombre, area="Otra área").full_clean()
        with self.assertRaises(ValidationError):
            Servicio(nombre=service.nombre).full_clean()

    def test_demo_data_command_is_idempotent(self):
        call_command("load_demo_data")
        call_command("load_demo_data")

        self.assertEqual(
            set(Delegacion.objects.values_list("nombre", flat=True)),
            {
                "Delegación Rural",
                "Delegación Centro",
                "Delegación Avenida del Mar",
                "Delegación La Antena - La Florida",
                "Delegación Las Compañías",
                "Delegación La Pampa",
            },
        )
        self.assertEqual(Delegacion.objects.count(), 6)
        self.assertEqual(Cargo.objects.count(), 3)
        self.assertEqual(Funcionario.objects.count(), 6)
        self.assertEqual(Group.objects.count(), 3)
        self.assertTrue(
            all(not funcionario.usuario.has_usable_password() for funcionario in Funcionario.objects.select_related("usuario"))
        )


class IndicatorValidationTests(TestCase):
    def setUp(self):
        self.cargo = Cargo.objects.create(nombre="Coordinación")

    def test_indicator_rejects_invalid_weight_and_target(self):
        invalid_weight = Indicador(
            nombre="Gestión comunitaria",
            cargo=self.cargo,
            ponderador=Decimal("100.01"),
            meta_trimestral=1,
            unidad_medida="acciones",
        )
        with self.assertRaises(ValidationError):
            invalid_weight.full_clean()

        invalid_target = Indicador(
            nombre="Atención territorial",
            cargo=self.cargo,
            ponderador=Decimal("20.00"),
            meta_trimestral=0,
            unidad_medida="acciones",
        )
        with self.assertRaises(ValidationError):
            invalid_target.full_clean()

    def test_indicator_requires_existing_cargo(self):
        indicator = Indicador(
            nombre="Indicador huérfano",
            cargo_id=999999,
            ponderador=Decimal("10.00"),
            meta_trimestral=1,
            unidad_medida="acciones",
        )
        with self.assertRaises(ValidationError):
            indicator.full_clean()

    def test_weight_sum_is_calculated_per_cargo(self):
        another_cargo = Cargo.objects.create(nombre="Inspección")
        Indicador.objects.create(nombre="A", cargo=self.cargo, ponderador=Decimal("40.00"), meta_trimestral=1, unidad_medida="acciones")
        inactive = Indicador.objects.create(nombre="B", cargo=self.cargo, ponderador=Decimal("20.00"), meta_trimestral=1, unidad_medida="acciones", activo=False)
        Indicador.objects.create(nombre="C", cargo=another_cargo, ponderador=Decimal("80.00"), meta_trimestral=1, unidad_medida="acciones")

        self.assertEqual(Indicador.porcentaje_ponderadores(self.cargo.pk), Decimal("40.00"))
        self.assertEqual(Indicador.porcentaje_ponderadores(another_cargo.pk), Decimal("80.00"))
        self.assertIsNotNone(inactive.pk)
