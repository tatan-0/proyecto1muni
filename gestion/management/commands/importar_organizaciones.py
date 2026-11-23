from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gestion.importacion import leer_excel
from gestion.models import Delegacion, OrganizacionComunitaria

CAMPOS_EXCEL = (
    "domicilio_legal",
    "socios_activos",
    "fecha_constitucion",
    "numero_registro_pj",
    "fecha_inscripcion_registro",
    "numero_registro_directiva",
    "observaciones_origen",
)


class Command(BaseCommand):
    help = (
        "Importa organizaciones comunitarias desde el Excel de juntas de vecinos. "
        "Por defecto no toca las organizaciones que ya existen (mismo nombre y delegación); "
        "usa --actualizar para refrescar sus datos del Excel."
    )

    def add_arguments(self, parser):
        parser.add_argument("archivo", help="Ruta al archivo .xlsx")
        parser.add_argument(
            "--simular",
            action="store_true",
            help="Muestra qué pasaría sin guardar nada en la base de datos.",
        )
        parser.add_argument(
            "--actualizar",
            action="store_true",
            help="Actualiza con los datos del Excel las organizaciones que ya existen.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            organizaciones, errores = leer_excel(options["archivo"])
        except FileNotFoundError:
            raise CommandError(f"No se encontró el archivo: {options['archivo']}")
        except ImportError:
            raise CommandError("Falta la librería openpyxl. Ejecuta: pip install -r requirements.txt")
        except ValueError as error:
            raise CommandError(str(error))
        except Exception as error:  # archivo dañado o que no es un .xlsx
            raise CommandError(f"No se pudo leer el Excel: {error}")

        delegaciones = {}
        for nombre in sorted({o.delegacion for o in organizaciones if o.delegacion}):
            delegaciones[nombre] = Delegacion.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion_territorial": "", "activo": True},
            )[0]

        existentes = {(o.nombre, o.delegacion_id): o for o in OrganizacionComunitaria.objects.all()}
        vistas = set()
        por_crear, por_actualizar = [], []
        repetidas = 0
        for datos in organizaciones:
            delegacion = delegaciones.get(datos.delegacion)
            clave = (datos.nombre, delegacion.pk if delegacion else None)
            if clave in vistas:
                repetidas += 1
                self.stderr.write(f"Fila {datos.fila}: '{datos.nombre}' repetida en el Excel; se omitió.")
                continue
            vistas.add(clave)
            valores = {
                "domicilio_legal": datos.domicilio_legal,
                "socios_activos": datos.socios_activos,
                "fecha_constitucion": datos.fecha_constitucion,
                "numero_registro_pj": datos.numero_registro_pj,
                "fecha_inscripcion_registro": datos.fecha_inscripcion_registro,
                "numero_registro_directiva": datos.numero_registro_directiva,
                "observaciones_origen": datos.observaciones,
            }
            organizacion = existentes.get(clave)
            if organizacion is None:
                por_crear.append(
                    OrganizacionComunitaria(
                        nombre=datos.nombre,
                        tipo=OrganizacionComunitaria.Tipo.SIN_CLASIFICAR,
                        delegacion=delegacion,
                        activo=True,
                        **valores,
                    )
                )
            elif options["actualizar"]:
                for campo, valor in valores.items():
                    setattr(organizacion, campo, valor)
                por_actualizar.append(organizacion)

        OrganizacionComunitaria.objects.bulk_create(por_crear, batch_size=500)
        if por_actualizar:
            OrganizacionComunitaria.objects.bulk_update(por_actualizar, CAMPOS_EXCEL, batch_size=500)

        omitidas = len(organizaciones) - repetidas - len(por_crear) - len(por_actualizar)
        for numero, motivo in errores:
            self.stderr.write(f"Fila {numero}: no se importó ({motivo}).")

        por_delegacion = Counter(o.delegacion or "(sin delegación)" for o in organizaciones)
        self.stdout.write("Organizaciones por delegación en el Excel:")
        for nombre, cantidad in sorted(por_delegacion.items()):
            self.stdout.write(f"  {nombre}: {cantidad}")
        con_observaciones = sum(1 for o in organizaciones if o.observaciones)
        self.stdout.write(
            f"Filas leídas: {len(organizaciones)} · nuevas: {len(por_crear)} · "
            f"actualizadas: {len(por_actualizar)} · ya existentes sin cambios: {omitidas} · "
            f"repetidas: {repetidas} · con errores: {len(errores)} · "
            f"con observaciones para revisar: {con_observaciones}"
        )

        if options["simular"]:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("Simulación: no se guardó nada."))
        else:
            self.stdout.write(self.style.SUCCESS("Importación terminada."))
