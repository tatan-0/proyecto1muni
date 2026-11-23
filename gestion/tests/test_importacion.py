"""Pruebas de la lectura y limpieza del Excel (no requieren base de datos)."""

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook

from gestion.importacion import COLUMNAS_ESPERADAS, convertir_fila, leer_excel

HOY = date(2026, 11, 22)


def fila(nombre="CLUB EJEMPLO", dom="CALLE 1", terr="CENTRO", socios=20, const=datetime(2010, 5, 4),
         reg=100, insc=datetime(2010, 5, 10), directiva=555):
    return (nombre, dom, terr, socios, const, reg, insc, directiva)


class ConvertirFilaTests(unittest.TestCase):
    def test_fila_normal(self):
        org = convertir_fila(2, fila(), HOY)
        self.assertEqual(org.nombre, "CLUB EJEMPLO")
        self.assertEqual(org.delegacion, "Delegación Centro")
        self.assertEqual(org.socios_activos, 20)
        self.assertEqual(org.fecha_constitucion, date(2010, 5, 4))
        self.assertEqual(org.numero_registro_pj, "100")
        self.assertEqual(org.fecha_inscripcion_registro, date(2010, 5, 10))
        self.assertEqual(org.numero_registro_directiva, 555)
        self.assertEqual(org.observaciones, "")

    def test_limpia_espacios_del_nombre_y_territorio(self):
        org = convertir_fila(2, fila(nombre="  CLUB   CON  ESPACIOS ", terr="CENTRO "), HOY)
        self.assertEqual(org.nombre, "CLUB CON ESPACIOS")
        self.assertEqual(org.delegacion, "Delegación Centro")

    def test_todos_los_territorios_conocidos(self):
        esperados = {
            "CIAS": "Delegación Las Compañías",
            "PAMPA": "Delegación La Pampa",
            "RURAL": "Delegación Rural",
            "ANTENA": "Delegación La Antena - La Florida",
            "AV DEL MAR": "Delegación Avenida del Mar",
        }
        for territorio, delegacion in esperados.items():
            with self.subTest(territorio=territorio):
                self.assertEqual(convertir_fila(2, fila(terr=territorio), HOY).delegacion, delegacion)

    def test_territorio_desconocido_o_vacio_queda_sin_delegacion_y_anotado(self):
        desconocido = convertir_fila(2, fila(terr="ALFALFARES"), HOY)
        self.assertIsNone(desconocido.delegacion)
        self.assertIn("ALFALFARES", desconocido.observaciones)
        vacio = convertir_fila(2, fila(terr=None), HOY)
        self.assertIsNone(vacio.delegacion)
        self.assertIn("no informa territorio", vacio.observaciones)

    def test_socios_como_texto(self):
        self.assertEqual(convertir_fila(2, fila(socios="32!"), HOY).socios_activos, 32)
        self.assertIsNone(convertir_fila(2, fila(socios=" "), HOY).socios_activos)
        org = convertir_fila(2, fila(socios="6 CLUBES"), HOY)
        self.assertIsNone(org.socios_activos)
        self.assertIn("6 CLUBES", org.observaciones)

    def test_fechas_sin_informacion_no_generan_observacion(self):
        for texto in ("S/Inf.", "s/inf", "Sin inf."):
            with self.subTest(texto=texto):
                org = convertir_fila(2, fila(const=texto), HOY)
                self.assertIsNone(org.fecha_constitucion)
                self.assertEqual(org.observaciones, "")

    def test_fechas_invalidas_se_dejan_vacias_y_se_anotan(self):
        antigua = convertir_fila(2, fila(const=datetime(1900, 2, 4)), HOY)
        self.assertIsNone(antigua.fecha_constitucion)
        self.assertIn("04-02-1900", antigua.observaciones)
        futura = convertir_fila(2, fila(insc=datetime(2027, 7, 30)), HOY)
        self.assertIsNone(futura.fecha_inscripcion_registro)
        self.assertIn("posterior a hoy", futura.observaciones)
        rara = convertir_fila(2, fila(const="ayer"), HOY)
        self.assertIsNone(rara.fecha_constitucion)
        self.assertIn("'ayer'", rara.observaciones)

    def test_registro_pj_con_texto_se_conserva_y_se_anota(self):
        org = convertir_fila(2, fila(reg="352-BIS"), HOY)
        self.assertEqual(org.numero_registro_pj, "352-BIS")
        self.assertIn("352-BIS", org.observaciones)

    def test_registro_directiva_vacio(self):
        self.assertIsNone(convertir_fila(2, fila(directiva=None), HOY).numero_registro_directiva)

    def test_fila_sin_nombre_es_error(self):
        with self.assertRaises(ValueError):
            convertir_fila(2, fila(nombre="   "), HOY)

    def test_nombre_demasiado_largo_es_error(self):
        with self.assertRaises(ValueError):
            convertir_fila(2, fila(nombre="X" * 161), HOY)


class LeerExcelTests(unittest.TestCase):
    def crear_excel(self, directorio, encabezado=COLUMNAS_ESPERADAS, filas=()):
        libro = Workbook()
        hoja = libro.active
        hoja.append(list(encabezado))
        for contenido in filas:
            hoja.append(list(contenido))
        ruta = Path(directorio) / "organizaciones.xlsx"
        libro.save(ruta)
        return ruta

    def test_lee_filas_y_salta_vacias(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = self.crear_excel(tmp, filas=[fila("CLUB A"), (None,) * 8, fila("CLUB B", terr="PAMPA")])
            organizaciones, errores = leer_excel(ruta, HOY)
        self.assertEqual([o.nombre for o in organizaciones], ["CLUB A", "CLUB B"])
        self.assertEqual([o.fila for o in organizaciones], [2, 4])
        self.assertEqual(errores, [])

    def test_fila_con_error_se_informa_y_no_detiene_la_lectura(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = self.crear_excel(tmp, filas=[fila("CLUB A"), fila(nombre=None, dom="SOLO DOMICILIO")])
            organizaciones, errores = leer_excel(ruta, HOY)
        self.assertEqual(len(organizaciones), 1)
        self.assertEqual(errores[0][0], 3)

    def test_columnas_incorrectas(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = self.crear_excel(tmp, encabezado=("A", "B", "C", "D", "E", "F", "G", "H"))
            with self.assertRaises(ValueError):
                leer_excel(ruta, HOY)

    def test_encabezado_con_espacios_y_minusculas_se_acepta(self):
        encabezado = tuple(f" {c.lower()} " for c in COLUMNAS_ESPERADAS)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = self.crear_excel(tmp, encabezado=encabezado, filas=[fila()])
            organizaciones, _ = leer_excel(ruta, HOY)
        self.assertEqual(len(organizaciones), 1)


if __name__ == "__main__":
    unittest.main()
