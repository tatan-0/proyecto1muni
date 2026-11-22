import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from gestion.models import PerfilUsuario


class Command(BaseCommand):
    help = "Asigna una contraseña temporal a una cuenta y la obliga a cambiarla al próximo ingreso."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"No existe la cuenta '{options['username']}'.")
        clave = secrets.token_urlsafe(9)
        user.set_password(clave)
        user.save(update_fields=["password"])
        PerfilUsuario.objects.update_or_create(usuario=user, defaults={"debe_cambiar_clave": True})
        self.stdout.write(self.style.SUCCESS(f"Cuenta: {user.username}"))
        self.stdout.write(self.style.SUCCESS(f"Contraseña temporal: {clave}"))
        self.stdout.write("Entrégala a la persona; se muestra solo ahora y deberá cambiarla al ingresar.")
