from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.urls import reverse_lazy

from gestion.models import PerfilUsuario


class CambiarClaveView(PasswordChangeView):
    template_name = "registration/cambiar_clave.html"
    success_url = reverse_lazy("gestion:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        PerfilUsuario.objects.filter(usuario=self.request.user).update(debe_cambiar_clave=False)
        return response


class RecuperarConfirmarView(PasswordResetConfirmView):
    """Al elegir una clave nueva desde el correo, también se limpia la marca de clave temporal."""

    template_name = "registration/recuperar_confirmar.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        PerfilUsuario.objects.filter(usuario=form.user).update(debe_cambiar_clave=False)
        return response