from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import RequestFactory, TestCase
from django.urls import reverse

from gestion.models import Tarea
from gestion.views.tareas import mis_tareas, panel_cumplimiento


class TaskReviewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.delegate = User.objects.create_user("review_delegate", password="test-pass-123")
        self.delegate.groups.add(Group.objects.create(name="DELEGADO"))
        professional = User.objects.create_user("review_professional", password="test-pass-123")
        self.task = Tarea.objects.create(
            titulo="Revisar luminaria",
            descripcion="Tarea de prueba",
            fecha_limite=date(2026, 12, 1),
            creada_por=self.delegate,
            profesional=professional,
            delegado=self.delegate,
            estado=Tarea.Estado.EN_REVISION,
        )
        self.client.force_login(self.delegate)

    def test_delegate_can_request_more_evidence(self):
        response = self.client.post(
            reverse("gestion:revisar_tarea", kwargs={"pk": self.task.pk}),
            {"accion": "antecedentes", "observaciones": "Adjunta una foto más clara."},
        )

        self.assertRedirects(
            response,
            reverse("gestion:detalle_tarea", kwargs={"pk": self.task.pk}),
            fetch_redirect_response=False,
        )
        self.task.refresh_from_db()
        self.assertEqual(self.task.estado, Tarea.Estado.MAS_ANTECEDENTES)
        self.assertFalse(self.task.cumplida)
        self.assertEqual(self.task.observaciones_revision, "Adjunta una foto más clara.")

    def test_more_evidence_task_is_counted_as_pending(self):
        self.task.estado = Tarea.Estado.MAS_ANTECEDENTES
        self.task.save()
        request = RequestFactory().get("/mis-tareas/")
        request.user = self.delegate

        with patch("gestion.views.tareas.render") as render:
            mis_tareas(request)

        self.assertEqual(render.call_args.args[2]["pendientes"], 1)


class CompliancePanelTests(TestCase):
    def test_more_evidence_tasks_remain_in_panel_pending_list(self):
        User = get_user_model()
        coordinator = User.objects.create_user("panel_coordinator", password="test-pass-123")
        coordinator.groups.add(Group.objects.create(name="COORDINADOR"))
        professional = User.objects.create_user("panel_professional", password="test-pass-123")
        delegate = User.objects.create_user("panel_delegate", password="test-pass-123")
        task = Tarea.objects.create(
            titulo="Revisar luminaria",
            descripcion="Tarea de prueba",
            fecha_limite=date(2026, 12, 1),
            creada_por=coordinator,
            profesional=professional,
            delegado=delegate,
            estado=Tarea.Estado.MAS_ANTECEDENTES,
        )
        request = RequestFactory().get("/panel-cumplimiento/")
        request.user = coordinator

        with patch("gestion.views.tareas.render") as render:
            panel_cumplimiento(request)

        pendientes = render.call_args.args[2]["pendientes"]
        self.assertEqual(list(pendientes), [task])
