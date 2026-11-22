from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, MetaIndividual

User = get_user_model()


class MetaIndividualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for nombre in ("ADMINISTRADOR", "COORDINADOR", "DELEGADO", "PROFESIONAL"):
            Group.objects.get_or_create(name=nombre)
        cls.admin = User.objects.create_superuser("admin_t", password="x-Clave-123")
        cls.coord = User.objects.create_user("coord_t", password="x-Clave-123")
        cls.coord.groups.add(Group.objects.get(name="COORDINADOR"))
        cls.prof = User.objects.create_user("prof_t", password="x-Clave-123")
        cls.prof.groups.add(Group.objects.get(name="PROFESIONAL"))

        cls.cargo = Cargo.objects.create(nombre="Cargo prueba")
        cls.otro_cargo = Cargo.objects.create(nombre="Otro cargo")
        cls.sector = Delegacion.objects.create(nombre="Delegación prueba")
        cls.func = Funcionario.objects.create(
            usuario=cls.prof, nombre="Prof Prueba", cargo=cls.cargo, delegacion=cls.sector,
        )
        cls.ind = Indicador.objects.create(
            nombre="Ind A", cargo=cls.cargo, ponderador=100,
            meta_trimestral=12, unidad_medida="acciones",
        )
        cls.ind_ajeno = Indicador.objects.create(
            nombre="Ind B", cargo=cls.otro_cargo, ponderador=100,
            meta_trimestral=5, unidad_medida="acciones",
        )
        hoy = date.today()
        cls.anio, cls.trim = hoy.year, (hoy.month - 1) // 3 + 1

    def datos(self, **extra):
        base = {
            "funcionario": self.func.pk, "indicador": self.ind.pk,
            "anio": self.anio, "trimestre": self.trim, "meta": 7,
        }
        base.update(extra)
        return base

    def test_anonimo_y_profesional_no_acceden(self):
        url = reverse("gestion:metas_lista")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.prof)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_coordinador_y_admin_acceden(self):
        url = reverse("gestion:metas_lista")
        for usuario in (self.coord, self.admin):
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_coordinador_crea_meta(self):
        self.client.force_login(self.coord)
        resp = self.client.post(reverse("gestion:metas_crear"), self.datos())
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(MetaIndividual.objects.count(), 1)

    def test_rechaza_indicador_de_otro_cargo(self):
        self.client.force_login(self.coord)
        resp = self.client.post(
            reverse("gestion:metas_crear"), self.datos(indicador=self.ind_ajeno.pk)
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(MetaIndividual.objects.count(), 0)

    def test_rechaza_meta_duplicada(self):
        self.client.force_login(self.coord)
        self.client.post(reverse("gestion:metas_crear"), self.datos())
        resp = self.client.post(reverse("gestion:metas_crear"), self.datos(meta=9))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(MetaIndividual.objects.count(), 1)

    def test_editar_y_eliminar(self):
        meta = MetaIndividual.objects.create(
            funcionario=self.func, indicador=self.ind,
            anio=self.anio, trimestre=self.trim, meta=7,
        )
        self.client.force_login(self.admin)
        self.client.post(reverse("gestion:metas_editar", args=[meta.pk]), self.datos(meta=10))
        meta.refresh_from_db()
        self.assertEqual(meta.meta, 10)
        self.client.post(reverse("gestion:metas_eliminar", args=[meta.pk]))
        self.assertEqual(MetaIndividual.objects.count(), 0)

    def test_semaforo_usa_meta_individual_o_la_del_cargo(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("gestion:semaforo"))
        self.assertContains(resp, "del cargo")
        MetaIndividual.objects.create(
            funcionario=self.func, indicador=self.ind,
            anio=self.anio, trimestre=self.trim, meta=7,
        )
        resp = self.client.get(reverse("gestion:semaforo"))
        self.assertContains(resp, "individual")
