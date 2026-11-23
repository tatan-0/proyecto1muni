from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Tarea
from gestion.periodos import rango_trimestre
from gestion.views.dashboard import semaforo


class SemaforoTests(TestCase):
    def test_progress_counts_approved_tasks_in_current_quarter_and_caps_percentage(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="semaforo_admin",
            email="semaforo@example.com",
            password="test-pass-123",
        )
        delegacion = Delegacion.objects.create(nombre="Delegación semáforo")
        cargo = Cargo.objects.create(nombre="Cargo semáforo")
        Funcionario.objects.create(
            usuario=admin_user,
            nombre="Administrador",
            cargo=cargo,
            delegacion=delegacion,
        )
        indicador = Indicador.objects.create(
            nombre="Tareas completadas",
            cargo=cargo,
            ponderador=Decimal("100.00"),
            meta_trimestral=1,
            unidad_medida="tareas",
        )
        Tarea.objects.create(
            titulo="Tarea aprobada",
            descripcion="Prueba de avance",
            fecha_limite=date(2026, 12, 31),
            creada_por=admin_user,
            profesional=admin_user,
            delegado=admin_user,
            indicador=indicador,
            estado=Tarea.Estado.APROBADA,
            validada_en=timezone.now(),
        )

        request = RequestFactory().get("/semaforo/")
        request.user = admin_user
        with patch("gestion.views.dashboard.render") as render:
            semaforo(request)

        context = render.call_args.args[2]
        self.assertEqual(context["trimestre_desde"], rango_trimestre(timezone.localdate())[0])
        self.assertEqual(context["trimestre_hasta"], rango_trimestre(timezone.localdate())[1])
        fila = context["filas_funcionario"][0]
        self.assertEqual(fila["indicador"], indicador)
        self.assertEqual(fila["avance"], 1)
        self.assertEqual(fila["porcentaje"], 100)
        self.assertEqual(fila["meta"], 1)
        self.assertFalse(fila["propia"])
