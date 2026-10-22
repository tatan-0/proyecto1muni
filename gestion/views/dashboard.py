from decimal import Decimal
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from gestion.models import Delegacion, Funcionario, Indicador, Servicio
from gestion.permissions import funcionarios_visibles, usuario_es_admin, usuario_tiene_acceso_sgr

def sgr_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not usuario_tiene_acceso_sgr(request.user):
            return HttpResponseForbidden("Tu cuenta no tiene un perfil habilitado para el SGR.")
        return view_func(request, *args, **kwargs)

    return require_GET(login_required(wrapped))


@sgr_required
def dashboard(request):
    visible_staff = funcionarios_visibles(request.user).filter(activo=True)
    is_admin = usuario_es_admin(request.user)
    if is_admin:
        delegaciones = Delegacion.objects.filter(activo=True)
    else:
        delegation_ids = visible_staff.values_list("delegacion_id", flat=True).distinct()
        delegaciones = Delegacion.objects.filter(activo=True, pk__in=delegation_ids)

    selected_id = _int_or_none(request.GET.get("delegacion"))
    selected_delegation = delegaciones.filter(pk=selected_id).first() if selected_id else None
    if selected_delegation is None and delegaciones.count() == 1:
        selected_delegation = delegaciones.first()

    staff = visible_staff.filter(delegacion=selected_delegation) if selected_delegation else visible_staff
    active_indicators = Indicador.objects.filter(activo=True, cargo__funcionarios__in=staff).distinct()
    cargo_ids = staff.values_list("cargo_id", flat=True).distinct()
    return render(
        request,
        "gestion/dashboard.html",
        {
            "es_administrador": is_admin,
            "delegaciones": delegaciones,
            "delegacion_actual": selected_delegation,
            "funcionarios": staff,
            "cantidad_funcionarios": staff.count(),
            "cantidad_delegaciones": 1 if selected_delegation else delegaciones.count(),
            "cantidad_indicadores": active_indicators.count(),
            "cantidad_servicios": Servicio.objects.filter(activo=True).count(),
            "ponderador_total": sum(
                (Indicador.porcentaje_ponderadores(cargo_id) for cargo_id in cargo_ids),
                start=Decimal("0.00"),
            ),
            "fecha_consulta": timezone.localdate(),
        },
    )


@sgr_required
def ficha(request):
    funcionarios = funcionarios_visibles(request.user).filter(activo=True)
    selected_id = _int_or_none(request.GET.get("funcionario"))
    funcionario = funcionarios.filter(pk=selected_id).first() if selected_id else None
    if funcionario is None:
        funcionario = funcionarios.first()
    indicadores = (
        Indicador.objects.filter(cargo=funcionario.cargo, activo=True)
        if funcionario
        else Indicador.objects.none()
    )
    return render(
        request,
        "gestion/ficha_funcionario.html",
        {
            "funcionario": funcionario,
            "funcionarios": funcionarios,
            "indicadores": indicadores,
            "ponderador_total": Indicador.porcentaje_ponderadores(funcionario.cargo_id) if funcionario else Decimal("0.00"),
            "actividades": [],
        },
    )


@sgr_required
def tubo(request):
    profile = _profile(request.user)
    return render(
        request,
        "gestion/tubo.html",
        {"compromisos": [], "delegacion": profile.delegacion if profile else None},
    )


@sgr_required
def semaforo(request):
    staff = funcionarios_visibles(request.user).filter(activo=True)
    cargo_ids = staff.values_list("cargo_id", flat=True).distinct()
    indicators = Indicador.objects.filter(cargo_id__in=cargo_ids, activo=True).select_related("cargo")
    rows = [{"indicador": indicator} for indicator in indicators]
    return render(
        request,
        "gestion/semaforo.html",
        {"filas": rows},
    )


@sgr_required
def resumen(request):
    staff = funcionarios_visibles(request.user).filter(activo=True)
    delegation_ids = staff.values_list("delegacion_id", flat=True).distinct()
    delegaciones = Delegacion.objects.filter(activo=True, pk__in=delegation_ids)
    rows = []
    for delegation in delegaciones:
        delegation_staff = staff.filter(delegacion=delegation)
        rows.append(
            {
                "delegacion": delegation,
                "cantidad_funcionarios": delegation_staff.count(),
                "cantidad_indicadores": Indicador.objects.filter(
                    activo=True, cargo__funcionarios__in=delegation_staff
                ).distinct().count(),
            }
        )
    cargo_ids = staff.values_list("cargo_id", flat=True).distinct()
    return render(
        request,
        "gestion/resumen.html",
        {
            "filas": rows,
            "cantidad_delegaciones": len(rows),
            "cantidad_funcionarios": staff.count(),
            "cantidad_indicadores": Indicador.objects.filter(activo=True, cargo_id__in=cargo_ids).distinct().count(),
            "cantidad_servicios": Servicio.objects.filter(activo=True).count(),
        },
    )


def _profile(user):
    try:
        return user.perfil_sgr
    except Funcionario.DoesNotExist:
        return None


def _int_or_none(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
