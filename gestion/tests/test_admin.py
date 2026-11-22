from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from gestion.admin import EvidenciaAdmin, TareaAdmin
from gestion.models import Evidencia, Tarea


class ApprovedTaskAdminTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="test-pass-123",
        )
        self.request = RequestFactory().get("/admin/")
        self.request.user = self.admin_user
        self.task_admin = TareaAdmin(Tarea, admin.site)
        self.evidence_admin = EvidenciaAdmin(Evidencia, admin.site)

    def create_task(self, estado):
        return Tarea.objects.create(
            titulo="Revisar luminaria",
            descripcion="Tarea de prueba",
            fecha_limite=date(2026, 12, 1),
            creada_por=self.admin_user,
            profesional=self.admin_user,
            delegado=self.admin_user,
            estado=estado,
        )

    def test_approved_tasks_are_read_only_in_admin(self):
        approved = self.create_task(Tarea.Estado.APROBADA)
        pending = self.create_task(Tarea.Estado.PENDIENTE)

        self.assertFalse(self.task_admin.has_change_permission(self.request, approved))
        self.assertFalse(self.task_admin.has_delete_permission(self.request, approved))
        self.assertTrue(self.task_admin.has_change_permission(self.request, pending))
        self.assertTrue(self.task_admin.has_delete_permission(self.request, pending))

    def test_evidence_for_approved_tasks_is_read_only_in_admin(self):
        approved = self.create_task(Tarea.Estado.PENDIENTE)
        pending = self.create_task(Tarea.Estado.PENDIENTE)
        approved_evidence = Evidencia.objects.create(
            tarea=approved,
            imagen="evidencias/aprobada.jpg",
            subida_por=self.admin_user,
        )
        pending_evidence = Evidencia.objects.create(
            tarea=pending,
            imagen="evidencias/pendiente.jpg",
            subida_por=self.admin_user,
        )
        approved.estado = Tarea.Estado.APROBADA
        approved.save()

        self.assertFalse(self.evidence_admin.has_change_permission(self.request, approved_evidence))
        self.assertFalse(self.evidence_admin.has_delete_permission(self.request, approved_evidence))
        self.assertTrue(self.evidence_admin.has_change_permission(self.request, pending_evidence))
        self.assertTrue(self.evidence_admin.has_delete_permission(self.request, pending_evidence))
