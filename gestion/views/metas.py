from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms_metas import MetaIndividualForm
from ..models import MetaIndividual
from ..permissions import roles_de


def _solo_admin_o_coordinador(user):
    if not roles_de(user) & {"admin", "coordinador"}:
        raise PermissionDenied


@login_required
def metas_lista(request):
    _solo_admin_o_coordinador(request.user)
    metas = MetaIndividual.objects.select_related(
        "funcionario", "indicador", "indicador__cargo"
    )
    return render(request, "gestion/metas_lista.html", {"metas": metas})


@login_required
def metas_crear(request):
    _solo_admin_o_coordinador(request.user)
    form = MetaIndividualForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        meta = form.save()
        messages.success(request, f"Meta creada para {meta.funcionario}.")
        return redirect("gestion:metas_lista")
    return render(
        request,
        "gestion/meta_form.html",
        {"form": form, "titulo": "Nueva meta individual", "boton": "Crear meta"},
    )


@login_required
def metas_editar(request, pk):
    _solo_admin_o_coordinador(request.user)
    meta = get_object_or_404(MetaIndividual, pk=pk)
    form = MetaIndividualForm(request.POST or None, instance=meta)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Meta actualizada.")
        return redirect("gestion:metas_lista")
    return render(
        request,
        "gestion/meta_form.html",
        {"form": form, "titulo": "Editar meta individual", "boton": "Guardar cambios"},
    )


@login_required
@require_POST
def metas_eliminar(request, pk):
    _solo_admin_o_coordinador(request.user)
    meta = get_object_or_404(MetaIndividual, pk=pk)
    meta.delete()
    messages.success(request, "Meta eliminada. Se usará la meta del cargo.")
    return redirect("gestion:metas_lista")
