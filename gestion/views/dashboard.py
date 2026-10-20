from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from gestion.permissions import funcionarios_visibles, usuario_tiene_acceso_sgr


@login_required
def dashboard(request):
    if not usuario_tiene_acceso_sgr(request.user):
        return HttpResponseForbidden("Tu cuenta no tiene un perfil habilitado para el SGR.")
    context = {
        "funcionarios": funcionarios_visibles(request.user),
        "es_administrador": request.user.is_superuser or request.user.groups.filter(name="ADMINISTRADOR").exists(),
        "es_delegado": request.user.groups.filter(name="DELEGADO").exists(),
    }
    return render(request, "gestion/dashboard.html", context)
