from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import EvidenciaForm, TareaForm
from ..models import PerfilUsuario, Tarea
from ..permissions import roles_de


def tareas_visibles(user):
    """Cada rol ve solo lo que le corresponde (se combinan si tiene varios)."""
    roles = roles_de(user)
    if "admin" in roles:
        return Tarea.objects.all()
    condiciones = Q(pk__in=[])
    if "coordinador" in roles:
        condiciones |= Q(creada_por=user)
    if "delegado" in roles:
        condiciones |= Q(delegado=user)
    if "profesional" in roles:
        condiciones |= Q(profesional=user)
    return Tarea.objects.filter(condiciones).distinct()


def solo_roles(user, *roles):
    if not roles_de(user) & set(roles):
        raise PermissionDenied


@login_required
def mis_tareas(request):
    tareas = tareas_visibles(request.user)
    return render(request, "gestion/mis_tareas.html", {
        "roles": roles_de(request.user),
        "tareas": tareas,
        "total": tareas.count(),
        "pendientes": tareas.filter(estado__in=["pendiente", "en_progreso", "rechazada"]).count(),
        "por_revisar": tareas.filter(estado="en_revision").count(),
        "cumplidas": tareas.filter(cumplida=True).count(),
    })


@login_required
def crear_tarea(request):
    solo_roles(request.user, "coordinador", "admin")
    form = TareaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tarea = form.save(commit=False)
        tarea.creada_por = request.user
        tarea.save()
        messages.success(request, "Tarea creada y asignada.")
        return redirect("gestion:detalle_tarea", pk=tarea.pk)
    calles = {}
    for sector_id, calle in (
        Tarea.objects.exclude(ubicacion="").exclude(sector__isnull=True)
        .values_list("sector_id", "ubicacion").distinct().order_by("ubicacion")
    ):
        calles.setdefault(str(sector_id), []).append(calle)
    por_sector = {}
    for usuario_id, sector_id in PerfilUsuario.objects.exclude(sector__isnull=True).values_list("usuario_id", "sector_id"):
        por_sector.setdefault(str(sector_id), []).append(usuario_id)
    return render(request, "gestion/tarea_form.html", {
        "form": form, "roles": roles_de(request.user), "calles_por_sector": calles,
        "profesionales_por_sector": por_sector,
    })


@login_required
def detalle_tarea(request, pk):
    tarea = get_object_or_404(tareas_visibles(request.user), pk=pk)
    return render(request, "gestion/tarea_detalle.html", {
        "roles": roles_de(request.user),
        "tarea": tarea,
        "evidencias": tarea.evidencias.all(),
    })


@login_required
def subir_evidencia(request, pk):
    solo_roles(request.user, "profesional")
    tarea = get_object_or_404(Tarea, pk=pk, profesional=request.user)
    if tarea.cumplida or tarea.estado == "en_revision":
        messages.info(request, "Esta tarea ya no admite más evidencia por ahora.")
        return redirect("gestion:detalle_tarea", pk=tarea.pk)
    form = EvidenciaForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        ev = form.save(commit=False)
        ev.tarea, ev.subida_por, ev.tipo = tarea, request.user, "ejecucion"
        ev.save()
        tarea.estado = "en_revision"
        tarea.save(update_fields=["estado"])
        messages.success(request, "Evidencia enviada. El delegado la revisará.")
        return redirect("gestion:detalle_tarea", pk=tarea.pk)
    return render(request, "gestion/subir_evidencia.html",
                  {"form": form, "tarea": tarea, "roles": roles_de(request.user)})


@login_required
def revisar_tarea(request, pk):
    solo_roles(request.user, "delegado")
    tarea = get_object_or_404(Tarea, pk=pk, delegado=request.user, estado="en_revision")
    if request.method == "POST":
        aprobar = request.POST.get("accion") == "aprobar"
        tarea.cumplida = aprobar
        tarea.estado = "aprobada" if aprobar else "rechazada"
        tarea.validada_por = request.user
        tarea.validada_en = timezone.now()
        tarea.observaciones_revision = request.POST.get("observaciones", "")
        tarea.save()
        messages.success(request, "Tarea aprobada." if aprobar else "Tarea devuelta al profesional.")
        return redirect("gestion:detalle_tarea", pk=tarea.pk)
    return render(request, "gestion/revisar_tarea.html", {
        "roles": roles_de(request.user),
        "tarea": tarea,
        "evidencias": tarea.evidencias.all(),
    })


@login_required
def panel_cumplimiento(request):
    solo_roles(request.user, "coordinador", "admin")
    tareas = tareas_visibles(request.user).prefetch_related("evidencias")
    total = tareas.count()
    porcentaje = round(100 * tareas.filter(cumplida=True).count() / total) if total else 0
    return render(request, "gestion/panel_cumplimiento.html", {
        "roles": roles_de(request.user),
        "total": total,
        "porcentaje": porcentaje,
        "cumplidas": tareas.filter(cumplida=True),
        "en_revision": tareas.filter(estado="en_revision"),
        "pendientes": tareas.filter(cumplida=False).exclude(estado="en_revision"),
    })