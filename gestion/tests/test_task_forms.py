from decimal import Decimal

from django.test import TestCase

from gestion.forms import TareaForm
from gestion.models import Cargo, Indicador


class TareaFormTests(TestCase):
    def test_indicador_is_optional_and_only_active_indicators_are_available(self):
        cargo = Cargo.objects.create(nombre="Coordinación")
        active = Indicador.objects.create(
            nombre="Indicador activo",
            cargo=cargo,
            ponderador=Decimal("50.00"),
            meta_trimestral=1,
            unidad_medida="acciones",
        )
        inactive = Indicador.objects.create(
            nombre="Indicador inactivo",
            cargo=cargo,
            ponderador=Decimal("50.00"),
            meta_trimestral=1,
            unidad_medida="acciones",
            activo=False,
        )

        form = TareaForm()

        self.assertIn("indicador", form.fields)
        self.assertFalse(form.fields["indicador"].required)
        self.assertEqual(form.fields["indicador"].label, "Indicador al que aporta (opcional)")
        self.assertEqual(list(form.fields["indicador"].queryset), [active])
        self.assertNotIn(inactive, form.fields["indicador"].queryset)
