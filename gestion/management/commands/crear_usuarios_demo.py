import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea los grupos de roles y 4 cuentas de demostración."

    def handle(self, *args, **options):
        password = os.environ.get("SGR_DEMO_PASSWORD")
        if not password:
            raise CommandError("Define la variable de entorno SGR_DEMO_PASSWORD.")
        User = get_user_model()
        for nombre in ("ADMINISTRADOR", "COORDINADOR", "DELEGADO", "PROFESIONAL"):
            Group.objects.get_or_create(name=nombre)

        cuentas = [
            ("admin_sgr", "ADMINISTRADOR", "Ana", "Administradora"),
            ("coord_sgr", "COORDINADOR", "Carlos", "Coordinador"),
            ("delegado_sgr", "DELEGADO", "Diana", "Delegada"),
            ("prof_sgr", "PROFESIONAL", "Pedro", "Profesional"),
        ]
        for username, grupo, nombre, apellido in cuentas:
            user, creado = User.objects.get_or_create(
                username=username,
                defaults={"first_name": nombre, "last_name": apellido},
            )
            if creado:
                user.set_password(password)
                user.is_staff = grupo == "ADMINISTRADOR"
                user.save()
            user.groups.add(Group.objects.get(name=grupo))
            self.stdout.write(self.style.SUCCESS(f"{username} -> {grupo}"))
            