"""Pruebas del comando importar_organizaciones."""

import tempfile
from datetime import datetime
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from openpyxl import Workbook

from gestion.importacion import COLUMNAS_ESPERADAS
from gestion.models import Delegacion, OrganizacionComunitaria


class ImportarOrganizacionesTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta = self.crear_excel(
            [
                ("CLUB UNO", "CALLE 1 ", "CENTRO", 20, datetime(2010, 5, 4), 100, datetime(2010, 5, 10), 555),
                ("CLUB DOS", None, "CIAS", "6 CLUBES", "S/Inf.", "352-BIS", datetime(2011, 1, 2), None),
                ("CLUB TRES", "CALLE 3", None, 15, datetime(1900, 1, 1), 300, datetime(2012, 1, 2), 77),
            ]
        )

    def crear_excel(self, filas, nombre="organizaciones.xlsx"):
        libro = Workbook()
        hoja = libro.active
        hoja.append(list(COLUMNAS_ESPERADAS))
        for contenido in filas:
            hoja.append(list(contenido))
        ruta = Path(self.tmp.name) / nombre
        libro.save(ruta)
        return str(ruta)

    def importar(self, *args):
        salida = StringIO()
        call_command("importar_organizaciones", self.ruta, *args, stdout=salida, stderr=StringIO())
        return salida.getvalue()

    def test_importa_organizaciones_con_sus_datos(self):
        self.importar()
        self.assertEqual(OrganizacionComunitaria.objects.count(), 3)
        uno = OrganizacionComunitaria.objects.get(nombre="CLUB UNO")
        self.assertEqual(uno.delegacion.nombre, "Delegación Centro")
        self.assertEqual(uno.domicilio_legal, "CALLE 1")
        self.assertEqual(uno.socios_activos, 20)
        self.assertEqual(uno.numero_registro_pj, "100")
        self.assertEqual(uno.numero_registro_directiva, 555)
        self.assertEqual(uno.tipo, OrganizacionComunitaria.Tipo.SIN_CLASIFICAR)
        self.assertTrue(uno.activo)

    def test_datos_raros_quedan_anotados(self):
        self.importar()
        dos = OrganizacionComunitaria.objects.get(nombre="CLUB DOS")
        self.assertIsNone(dos.socios_activos)
        self.assertIsNone(dos.fecha_constitucion)
        self.assertEqual(dos.numero_registro_pj, "352-BIS")
        self.assertIn("6 CLUBES", dos.observaciones_origen)
        tres = OrganizacionComunitaria.objects.get(nombre="CLUB TRES")
        self.assertIsNone(tres.delegacion)
        self.assertIsNone(tres.fecha_constitucion)

    def test_es_repetible_sin_duplicar(self):
        self.importar()
        self.importar()
        self.assertEqual(OrganizacionComunitaria.objects.count(), 3)
        self.assertEqual(Delegacion.objects.filter(nombre="Delegación Centro").count(), 1)

    def test_no_pisa_cambios_hechos_en_el_sistema_salvo_con_actualizar(self):
        self.importar()
        uno = OrganizacionComunitaria.objects.get(nombre="CLUB UNO")
        uno.tipo = OrganizacionComunitaria.Tipo.DEPORTIVA
        uno.domicilio_legal = "DOMICILIO EDITADO"
        uno.save()
        self.importar()
        uno.refresh_from_db()
        self.assertEqual(uno.domicilio_legal, "DOMICILIO EDITADO")
        self.importar("--actualizar")
        uno.refresh_from_db()
        self.assertEqual(uno.domicilio_legal, "CALLE 1")
        self.assertEqual(uno.tipo, OrganizacionComunitaria.Tipo.DEPORTIVA)

    def test_simular_no_guarda_nada(self):
        delegaciones_antes = Delegacion.objects.count()
        salida = self.importar("--simular")
        self.assertEqual(OrganizacionComunitaria.objects.count(), 0)
        self.assertEqual(Delegacion.objects.count(), delegaciones_antes)
        self.assertIn("Simulación", salida)

    def test_archivo_inexistente(self):
        with self.assertRaises(CommandError):
            call_command("importar_organizaciones", str(Path(self.tmp.name) / "no_existe.xlsx"))

    def test_archivo_con_columnas_incorrectas(self):
        libro = Workbook()
        libro.active.append(["A", "B", "C"])
        ruta = Path(self.tmp.name) / "mal.xlsx"
        libro.save(ruta)
        with self.assertRaises(CommandError):
            call_command("importar_organizaciones", str(ruta))
