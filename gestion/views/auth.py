from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse

from gestion.permissions import roles_de, usuario_tiene_acceso_sgr

# Página de inicio según el rol. Si tiene varios roles, gana el primero de esta lista.
DESTINO_POR_ROL = (
    ("admin", "gestion:dashboard"),
    ("coordinador", "gestion:panel_cumplimiento"),
    ("delegado", "gestion:mis_tareas"),
    ("profesional", "gestion:mis_tareas"),
)


def destino_inicial(user):
    roles = roles_de(user)
    for rol, nombre_url in DESTINO_POR_ROL:
        if rol in roles:
            return reverse(nombre_url)
    if usuario_tiene_acceso_sgr(user):
        return reverse("gestion:dashboard")
    return reverse("gestion:mis_tareas")


class LoginPorRol(LoginView):
    template_name = "registration/login.html"

    def get_success_url(self):
        # Siempre según el rol: se ignora la página anterior (?next=).
        return destino_inicial(self.request.user)


login_view = LoginPorRol.as_view()
logout_view = LogoutView.as_view()