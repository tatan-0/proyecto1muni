import io
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from gestion.models import Cargo, Evidencia, Indicador, Tarea
from gestion.periodos import rango_trimestre

User = get_user_model()
MEDIA = tempfile.mkdtemp()
CLAVE = "x12345678"


def usuario(nombre, grupo):
    u = User.objects.create_user(nombre, password=CLAVE)
    u.groups.add(Group.objects.get_or_create(name=grupo)[0])
    return u


def foto():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="PNG")
    return SimpleUploadedFile("p.png", buf.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA)
class AprobacionTests(TestCase):
    def setUp(self):
        self.coord = usuario("coord", "COORDINADOR")
        self.deleg = usuario("deleg", "DELEGADO")
        self.prof = usuario("prof", "PROFESIONAL")
        self.tarea = Tarea.objects.create(
            titulo="T", descripcion="d", fecha_limite="2026-12-31",
            creada_por=self.coord, profesional=self.prof, delegado=self.deleg,
            estado="en_revision",
        )

    def test_mas_antecedentes_exige_observacion(self):
        self.client.login(username="deleg", password=CLAVE)
        self.client.post(reverse("gestion:revisar_tarea", args=[self.tarea.pk]),
                         {"accion": "antecedentes", "observaciones": ""})
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, "en_revision")

    def test_mas_antecedentes_vuelve_al_profesional(self):
        self.client.login(username="deleg", password=CLAVE)
        self.client.post(reverse("gestion:revisar_tarea", args=[self.tarea.pk]),
                         {"accion": "antecedentes", "observaciones": "Falta foto del frente"})
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, "mas_antecedentes")
        self.assertFalse(self.tarea.cumplida)

        self.client.login(username="prof", password=CLAVE)
        self.client.post(reverse("gestion:subir_evidencia", args=[self.tarea.pk]),
                         {"imagen": foto(), "descripcion": "frente"})
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, "en_revision")

    def test_tarea_aprobada_es_inmutable(self):
        self.client.login(username="deleg", password=CLAVE)
        self.client.post(reverse("gestion:revisar_tarea", args=[self.tarea.pk]), {"accion": "aprobar"})
        self.tarea.refresh_from_db()
        self.assertEqual(self.tarea.estado, "aprobada")
        self.tarea.titulo = "Cambiado"
        with self.assertRaises(ValidationError):
            self.tarea.save()
        with self.assertRaises(ValidationError):
            self.tarea.delete()
        with self.assertRaises(ValidationError):
            Evidencia.objects.create(tarea=self.tarea, imagen=foto(), subida_por=self.prof)

    def test_puntaje_solo_cuenta_aprobadas(self):
        cargo = Cargo.objects.create(nombre="Cargo de prueba")
        ind = Indicador.objects.create(
            nombre="Ind", cargo=cargo, ponderador=100, meta_trimestral=12, unidad_medida="acciones",
        )
        for estado in ("aprobada", "en_revision", "rechazada", "mas_antecedentes"):
            Tarea.objects.create(
                titulo=estado, descripcion="d", fecha_limite="2026-12-31",
                creada_por=self.coord, profesional=self.prof, delegado=self.deleg,
                estado=estado, indicador=ind,
                cumplida=(estado == "aprobada"),
                validada_en=timezone.now() if estado == "aprobada" else None,
            )
        desde, hasta = rango_trimestre(timezone.localdate())
        self.assertEqual(ind.aprobadas(desde, hasta), 1)