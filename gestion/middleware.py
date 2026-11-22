from django.shortcuts import redirect
from django.urls import reverse


class CambioClaveObligatorioMiddleware:
    """Si la cuenta tiene una contraseña temporal, solo puede cambiarla o cerrar sesión."""

    RUTAS_LIBRES = ("/cuenta/cambiar-clave/", "/logout/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not request.path.startswith(self.RUTAS_LIBRES)
        ):
            perfil = getattr(user, "perfil_sector", None)
            if perfil is not None and perfil.debe_cambiar_clave:
                return redirect(reverse("cambiar_clave"))
        return self.get_response(request)