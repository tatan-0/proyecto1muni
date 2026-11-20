from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse

from gestion.permissions import roles_de, usuario_tiene_acceso_sgr


class LoginPorRol(LoginView):
    template_name = "registration/login.html"

    def get_default_redirect_url(self):
        user = self.request.user
        roles = roles_de(user)
        # Coordinadores y profesionales no tienen acceso al dashboard del SGR.
        if roles & {"coordinador", "profesional"} or not usuario_tiene_acceso_sgr(user):
            return reverse("gestion:mis_tareas")
        return reverse("gestion:dashboard")


login_view = LoginPorRol.as_view()
logout_view = LogoutView.as_view()