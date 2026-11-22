from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from gestion.forms import GestionForm
from gestion.models import Ausencia, Cargo, Delegacion, Funcionario, Gestion, Indicador
from gestion.views.dashboard import _adjusted_target


class GestionRulesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("gestor_prueba", password="test-pass-123")
        self.user.groups.add(Group.objects.create(name="FUNCIONARIO"))
        self.delegacion = Delegacion.objects.create(nombre="Delegación gestión prueba")
        self.cargo = Cargo.objects.create(nombre="Cargo gestión prueba")
        self.funcionario = Funcionario.objects.create(
            usuario=self.user,
            nombre="Gestor de prueba",
            cargo=self.cargo,
            delegacion=self.delegacion,
        )
        self.indicador = Indicador.objects.create(
            nombre="Atención comunitaria",
            cargo=self.cargo,
            ponderador=100,
            meta_trimestral=12,
            unidad_medida="acciones",
        )

    def payload(self, **overrides):
        values = {
            "tipo": Gestion.Tipo.ACTIVIDAD,
            "accion": Gestion.Accion.REALIZACION,
            "fecha": "2026-11-18",
            "indicador": self.indicador.pk,
            "titulo": "Taller realizado",
            "descripcion": "",
            "usuario_nombre": "Persona usuaria",
            "usuario_telefono": "+56912345678",
            "usuario_es_delegado": "",
        }
        values.update(overrides)
        return values

    def test_only_completed_actions_with_both_user_details_are_countable(self):
        with patch.object(Gestion, "periodo_semanal_abierto", return_value=True):
            form = GestionForm(self.payload(), funcionario=self.funcionario)
            self.assertTrue(form.is_valid(), form.errors)
        gestion = form.save(commit=False)
        gestion.creado_por = self.user
        gestion.save()
        self.assertTrue(gestion.contabilizable)

        with patch.object(Gestion, "periodo_semanal_abierto", return_value=True):
            missing_phone = GestionForm(
                self.payload(fecha="2026-11-19", usuario_telefono=""),
                funcionario=self.funcionario,
            )
            self.assertTrue(missing_phone.is_valid(), missing_phone.errors)
        uncounted = missing_phone.save(commit=False)
        uncounted.creado_por = self.user
        uncounted.save()
        self.assertFalse(uncounted.contabilizable)

    def test_coordination_and_delegate_user_are_not_countable(self):
        with patch.object(Gestion, "periodo_semanal_abierto", return_value=True):
            form = GestionForm(
                self.payload(tipo=Gestion.Tipo.SOLICITUD, usuario_es_delegado="on"),
                funcionario=self.funcionario,
            )
            self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["tipo"], Gestion.Tipo.OTRA)
        self.assertIsNone(form.cleaned_data["indicador"])

        coordination = Gestion(
            funcionario=self.funcionario,
            indicador=self.indicador,
            tipo=Gestion.Tipo.ACTIVIDAD,
            accion=Gestion.Accion.COORDINACION,
            fecha=date(2026, 11, 18),
            titulo="Coordinación",
            usuario_nombre="Persona usuaria",
            usuario_telefono="+56912345678",
            creado_por=self.user,
        )
        self.assertFalse(coordination.contabilizable)

        delegate_request = Gestion(
            funcionario=self.funcionario,
            indicador=self.indicador,
            tipo=Gestion.Tipo.SOLICITUD,
            accion=Gestion.Accion.REALIZACION,
            fecha=date(2026, 11, 18),
            titulo="Solicitud",
            usuario_nombre="Delegado",
            usuario_telefono="+56912345678",
            usuario_es_delegado=True,
            creado_por=self.user,
        )
        self.assertFalse(delegate_request.contabilizable)

    def test_activity_does_not_count_if_indicator_belongs_to_another_cargo(self):
        another_cargo = Cargo.objects.create(nombre="Otro cargo")
        another_indicator = Indicador.objects.create(
            nombre="Indicador de otro cargo",
            cargo=another_cargo,
            ponderador=100,
            meta_trimestral=10,
            unidad_medida="acciones",
        )
        gestion = Gestion.objects.create(
            funcionario=self.funcionario,
            indicador=another_indicator,
            fecha=date(2026, 11, 18),
            titulo="Gestión registrada antes de cambiar el cargo",
            usuario_nombre="Persona usuaria",
            usuario_telefono="+56912345678",
            creado_por=self.user,
        )

        self.assertFalse(gestion.contabilizable)

    def test_daily_limit_is_seven_all_gestiones(self):
        for index in range(7):
            Gestion.objects.create(
                funcionario=self.funcionario,
                indicador=self.indicador,
                fecha=date(2026, 11, 18),
                titulo=f"Gestión {index}",
                usuario_nombre="Persona usuaria",
                usuario_telefono="+56912345678",
                creado_por=self.user,
            )

        with patch.object(Gestion, "periodo_semanal_abierto", return_value=True):
            form = GestionForm(self.payload(), funcionario=self.funcionario)

            self.assertFalse(form.is_valid())
        self.assertIn("Ya se alcanzó el máximo de siete gestiones para este día.", form.errors["fecha"])

    def test_week_closes_after_monday_of_the_following_week(self):
        self.assertTrue(Gestion.periodo_semanal_abierto(date(2026, 11, 20), hoy=date(2026, 11, 23)))
        self.assertFalse(Gestion.periodo_semanal_abierto(date(2026, 11, 20), hoy=date(2026, 11, 24)))
        self.assertTrue(Gestion.periodo_semanal_abierto(date(2026, 11, 23), hoy=date(2026, 11, 24)))

    def test_absence_proportionally_reduces_quarter_target(self):
        quarter_start = date(2026, 10, 1)
        quarter_end = date(2026, 12, 31)
        Ausencia.objects.create(
            funcionario=self.funcionario,
            tipo=Ausencia.Tipo.VACACIONES,
            fecha_desde=date(2026, 10, 5),
            fecha_hasta=date(2026, 10, 9),
            ingresado_por=self.user,
        )

        self.assertEqual(_adjusted_target(12, self.funcionario, quarter_start, quarter_end), 11)
