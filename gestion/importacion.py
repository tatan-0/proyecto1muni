"""Lectura y limpieza de la base de organizaciones comunitarias en Excel.

Este módulo no usa Django: solo transforma las filas del Excel en datos limpios
que luego guarda el comando ``importar_organizaciones``. Todo lo que se corrige o
descarta queda anotado en ``observaciones`` para poder revisarlo después.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime

COLUMNAS_ESPERADAS = (
    "ORGANIZACIONES",
    "DOMICILIO LEGAL",
    "TERRIT. DELEG.",
    "SOCIOS ACTIVOS",
    "FECHA CONSTIT.",
    "Nº REG. P.J.",
    "FECHA INSCRIPC EN REG.",
    "REG. DIR. Nº",
)

# Territorio escrito en el Excel -> delegación del sistema (mismos nombres que load_demo_data).
DELEGACIONES = {
    "CIAS": "Delegación Las Compañías",
    "CENTRO": "Delegación Centro",
    "PAMPA": "Delegación La Pampa",
    "RURAL": "Delegación Rural",
    "ANTENA": "Delegación La Antena - La Florida",
    "AV DEL MAR": "Delegación Avenida del Mar",
}

MAX_NOMBRE = 160
MAX_DOMICILIO = 200
MAX_REGISTRO_PJ = 40
ANIO_MINIMO_VALIDO = 1901  # el Excel usa 1900 como fecha vacía/placeholder


@dataclass
class OrganizacionImportada:
    fila: int
    nombre: str
    domicilio_legal: str
    delegacion: "str | None"
    socios_activos: "int | None"
    fecha_constitucion: "date | None"
    numero_registro_pj: str
    fecha_inscripcion_registro: "date | None"
    numero_registro_directiva: "int | None"
    observaciones: str


def limpiar_texto(valor):
    """Quita espacios sobrantes (inicio, fin y repetidos) y convierte a texto."""
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor)).strip()


def _entero(valor):
    """Devuelve un entero si el valor es un número entero, o None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float) and valor.is_integer():
        return int(valor)
    return None


def interpretar_socios(valor, notas):
    numero = _entero(valor)
    if numero is not None:
        if numero < 0:
            notas.append(f"Socios activos en el Excel: '{valor}' (negativo); se dejó vacío.")
            return None
        return numero
    texto = limpiar_texto(valor)
    if not texto:
        return None
    coincidencia = re.fullmatch(r"(\d+)\W*", texto)
    if coincidencia:
        return int(coincidencia.group(1))
    notas.append(f"Socios activos en el Excel: '{texto}'; no es un número, se dejó vacío.")
    return None


def _es_sin_informacion(texto):
    texto = texto.lower()
    return texto.startswith("s/inf") or texto.startswith("sin inf")


def interpretar_fecha(valor, etiqueta, notas, hoy=None):
    hoy = hoy or date.today()
    if valor is None:
        return None
    if isinstance(valor, datetime):
        fecha = valor.date()
    elif isinstance(valor, date):
        fecha = valor
    else:
        texto = limpiar_texto(valor)
        if not texto or _es_sin_informacion(texto):
            return None
        notas.append(f"{etiqueta} en el Excel: '{texto}'; no es una fecha, se dejó vacía.")
        return None
    if fecha.year < ANIO_MINIMO_VALIDO:
        notas.append(f"{etiqueta} en el Excel: {fecha:%d-%m-%Y} no es válida; se dejó vacía.")
        return None
    if fecha > hoy:
        notas.append(f"{etiqueta} en el Excel: {fecha:%d-%m-%Y} es posterior a hoy; se dejó vacía.")
        return None
    return fecha


def interpretar_registro_pj(valor):
    numero = _entero(valor)
    if numero is not None:
        return str(numero)
    return limpiar_texto(valor)


def interpretar_registro_directiva(valor, notas):
    numero = _entero(valor)
    if numero is not None and numero >= 0:
        return numero
    texto = limpiar_texto(valor)
    if not texto:
        return None
    if texto.isdigit():
        return int(texto)
    notas.append(f"Nº de registro de directiva en el Excel: '{texto}'; no es un número, se dejó vacío.")
    return None


def interpretar_delegacion(valor, notas):
    texto = limpiar_texto(valor)
    if not texto:
        notas.append("El Excel no informa territorio/delegación.")
        return None
    delegacion = DELEGACIONES.get(texto.upper())
    if delegacion is None:
        notas.append(f"Territorio '{texto}' del Excel sin delegación equivalente; quedó sin delegación.")
    return delegacion


def convertir_fila(numero_fila, celdas, hoy=None):
    """Convierte una fila (8 celdas) en OrganizacionImportada. Lanza ValueError si no sirve."""
    celdas = tuple(celdas) + (None,) * (len(COLUMNAS_ESPERADAS) - len(celdas))
    nombre = limpiar_texto(celdas[0])
    if not nombre:
        raise ValueError("fila sin nombre de organización")
    if len(nombre) > MAX_NOMBRE:
        raise ValueError(f"el nombre supera {MAX_NOMBRE} caracteres")

    notas = []
    domicilio = limpiar_texto(celdas[1])
    if len(domicilio) > MAX_DOMICILIO:
        notas.append(f"Domicilio recortado a {MAX_DOMICILIO} caracteres; original: '{domicilio}'.")
        domicilio = domicilio[:MAX_DOMICILIO]
    registro_pj = interpretar_registro_pj(celdas[5])
    if len(registro_pj) > MAX_REGISTRO_PJ:
        notas.append(f"Nº de registro P.J. recortado; original: '{registro_pj}'.")
        registro_pj = registro_pj[:MAX_REGISTRO_PJ]
    if registro_pj and not registro_pj.isdigit():
        notas.append(f"Nº de registro P.J. en el Excel: '{registro_pj}' (no es solo un número).")

    return OrganizacionImportada(
        fila=numero_fila,
        nombre=nombre,
        domicilio_legal=domicilio,
        delegacion=interpretar_delegacion(celdas[2], notas),
        socios_activos=interpretar_socios(celdas[3], notas),
        fecha_constitucion=interpretar_fecha(celdas[4], "Fecha de constitución", notas, hoy),
        numero_registro_pj=registro_pj,
        fecha_inscripcion_registro=interpretar_fecha(celdas[6], "Fecha de inscripción", notas, hoy),
        numero_registro_directiva=interpretar_registro_directiva(celdas[7], notas),
        observaciones="\n".join(notas),
    )


def leer_excel(ruta, hoy=None):
    """Lee la primera hoja del Excel. Devuelve (organizaciones, errores).

    ``errores`` es una lista de (número de fila, motivo) de filas que no se pueden importar.
    Lanza ValueError si el archivo no tiene las columnas esperadas.
    """
    from openpyxl import load_workbook

    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        hoja = libro.worksheets[0]
        filas = hoja.iter_rows(values_only=True)
        encabezado = next(filas, None)
        if encabezado is None:
            raise ValueError("El archivo está vacío.")
        encontrados = tuple(limpiar_texto(c).upper() for c in encabezado[: len(COLUMNAS_ESPERADAS)])
        if encontrados != COLUMNAS_ESPERADAS:
            raise ValueError(
                "Las columnas del Excel no son las esperadas.\n"
                f"Esperadas: {', '.join(COLUMNAS_ESPERADAS)}\n"
                f"Encontradas: {', '.join(encontrados)}"
            )
        organizaciones, errores = [], []
        for numero, celdas in enumerate(filas, start=2):
            if not any(limpiar_texto(c) for c in celdas):
                continue  # fila totalmente vacía
            try:
                organizaciones.append(convertir_fila(numero, celdas, hoy))
            except ValueError as error:
                errores.append((numero, str(error)))
        return organizaciones, errores
    finally:
        libro.close()
