from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Servicio


class Command(BaseCommand):
    help = "Carga catálogos y perfiles ficticios para demostración del SGR. No crea contraseñas de acceso."

    @transaction.atomic
    def handle(self, *args, **options):
        roles = {
            name: Group.objects.get_or_create(name=name)[0]
            for name in ("ADMINISTRADOR", "DELEGADO", "FUNCIONARIO")
        }
        delegaciones = (
            ("Delegación Rural", "Registro territorial ficticio para demostración."),
            ("Delegación Centro", "Registro territorial ficticio para demostración."),
            ("Delegación Avenida del Mar", "Registro territorial ficticio para demostración."),
            ("Delegación La Antena - La Florida", "Registro territorial ficticio para demostración."),
            ("Delegación Las Compañías", "Registro territorial ficticio para demostración."),
            ("Delegación La Pampa", "Registro territorial ficticio para demostración."),
        )
        delegation_records = {
            name: Delegacion.objects.update_or_create(
                nombre=name,
                defaults={"descripcion_territorial": description, "activo": True},
            )[0]
            for name, description in delegaciones
        }

        cargos = (
            ("Coordinación territorial", "Territorial"),
            ("Gestión comunitaria", "Comunidad"),
            ("Atención municipal", "Atención ciudadana"),
        )
        cargo_records = {
            name: Cargo.objects.update_or_create(nombre=name, defaults={"area": area, "activo": True})[0]
            for name, area in cargos
        }

        User = get_user_model()
        for index, delegation in enumerate(delegation_records.values()):
            slug = ("rural", "centro", "avenida_mar", "antena_florida", "companias", "pampa")[index]
            username = f"demo_funcionario_{slug}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"password": make_password(None), "is_active": True},
            )
            if created or not user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=["password"])
            user.groups.add(roles["FUNCIONARIO"])
            cargo = tuple(cargo_records.values())[index % len(cargo_records)]
            Funcionario.objects.update_or_create(
                usuario=user,
                defaults={
                    "nombre": f"Funcionario/a de demostración {index + 1}",
                    "cargo": cargo,
                    "delegacion": delegation,
                    "activo": True,
                },
            )

        for cargo, indicator_name in zip(
            cargo_records.values(),
            ("Coordinación vecinal", "Actividades comunitarias", "Orientación ciudadana"),
        ):
            Indicador.objects.update_or_create(
                cargo=cargo,
                nombre=indicator_name,
                defaults={
                    "ponderador": 100,
                    "meta_trimestral": 12,
                    "unidad_medida": "acciones",
                    "activo": True,
                },
            )

        for name, description in (
            ("Orientación municipal", "Servicio de ejemplo para atención de consultas."),
            ("Apoyo comunitario", "Servicio de ejemplo para coordinación territorial."),
        ):
            Servicio.objects.update_or_create(nombre=name, defaults={"descripcion": description, "activo": True})

        self.stdout.write(self.style.SUCCESS("Datos ficticios de demostracion cargados de forma repetible."))
