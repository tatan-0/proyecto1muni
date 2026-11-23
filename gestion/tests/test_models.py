from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from gestion.models import Cargo, Delegacion, Evidencia, Funcionario, Indicador, Servicio, Tarea


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
        self.assertEqual(
            Cargo.objects.filter(
                nombre__in=("Coordinación territorial", "Gestión comunitaria", "Atención municipal")
            ).count(),
            3,
        )
        self.assertEqual(Funcionario.objects.count(), 6)
        self.assertEqual(Group.objects.count(), 3)
        self.assertTrue(
            all(not funcionario.usuario.has_usable_password() for funcionario in Funcionario.objects.select_related("usuario"))
        )

    def test_descriptor_roles_are_loaded_with_responsibilities(self):
        roles = {
            "Delegado",
            "Gestor Social",
            "Apoyo Administrativo",
            "Organizaciones Comunitarias",
            "Gestor de Compras y Proyectos",
            "Gestión y Planificación",
            "Coordinador de Servicios Comunitarios",
        }

        loaded_roles = Cargo.objects.filter(nombre__in=roles)

        self.assertEqual(set(loaded_roles.values_list("nombre", flat=True)), roles)
        self.assertTrue(all(cargo.funciones.strip() for cargo in loaded_roles))


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


class ApprovedTaskIntegrityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.coordinator = User.objects.create_user("task_coordinator")
        self.professional = User.objects.create_user("task_professional")
        self.other_professional = User.objects.create_user("other_professional")
        self.delegate = User.objects.create_user("task_delegate")
        self.cargo = Cargo.objects.create(nombre="Operaciones")
        self.indicator = Indicador.objects.create(
            nombre="Atenciones realizadas",
            cargo=self.cargo,
            ponderador=Decimal("100.00"),
            meta_trimestral=10,
            unidad_medida="atenciones",
        )

    def create_task(self, **kwargs):
        values = {
            "titulo": "Reparar luminaria",
            "descripcion": "Reparación de prueba",
            "fecha_limite": datetime(2026, 5, 1).date(),
            "creada_por": self.coordinator,
            "profesional": self.professional,
            "delegado": self.delegate,
            "indicador": self.indicator,
        }
        values.update(kwargs)
        return Tarea.objects.create(**values)

    def test_approved_task_cannot_be_changed_or_deleted(self):
        tarea = self.create_task()
        tarea.estado = Tarea.Estado.APROBADA
        tarea.save()

        tarea.titulo = "Cambio no permitido"
        with self.assertRaises(ValidationError):
            tarea.save()
        with self.assertRaises(ValidationError):
            tarea.delete()

        self.assertTrue(Tarea.objects.filter(pk=tarea.pk).exists())
        self.assertEqual(Tarea.objects.get(pk=tarea.pk).titulo, "Reparar luminaria")

    def test_evidence_cannot_be_saved_or_deleted_for_approved_task(self):
        tarea = self.create_task()
        evidencia = Evidencia.objects.create(
            tarea=tarea,
            imagen="evidencias/prueba.jpg",
            subida_por=self.professional,
        )
        tarea.estado = Tarea.Estado.APROBADA
        tarea.save()

        evidencia.descripcion = "Cambio no permitido"
        with self.assertRaises(ValidationError):
            evidencia.save()
        with self.assertRaises(ValidationError):
            evidencia.delete()
        with self.assertRaises(ValidationError):
            Evidencia.objects.create(
                tarea=tarea,
                imagen="evidencias/nueva.jpg",
                subida_por=self.professional,
            )

        self.assertTrue(Evidencia.objects.filter(pk=evidencia.pk).exists())

    def test_indicator_counts_only_approved_tasks_in_date_range_and_by_professional(self):
        approved_in_range = {
            "estado": Tarea.Estado.APROBADA,
            "validada_en": timezone.make_aware(datetime(2026, 5, 12, 12)),
        }
        self.create_task(**approved_in_range)
        self.create_task(**approved_in_range)
        self.create_task(profesional=self.other_professional, **approved_in_range)
        self.create_task(
            estado=Tarea.Estado.APROBADA,
            validada_en=timezone.make_aware(datetime(2026, 6, 1, 12)),
        )
        self.create_task(
            estado=Tarea.Estado.EN_REVISION,
            validada_en=timezone.make_aware(datetime(2026, 5, 12, 12)),
        )

        desde, hasta = datetime(2026, 5, 1).date(), datetime(2026, 5, 31).date()
        self.assertEqual(self.indicator.aprobadas(desde, hasta), 3)
        self.assertEqual(self.indicator.aprobadas(desde, hasta, self.professional), 2)
