from datetime import timedelta
from decimal import Decimal
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from gestion.models import Delegacion, Funcionario, Indicador, Servicio
from gestion.permissions import funcionarios_visibles, usuario_es_admin, usuario_tiene_acceso_sgr

DEMO_LABEL = "Datos de demostración · Ejemplos ficticios sin persistencia transaccional."


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
            "demo_label": DEMO_LABEL,
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
            "fecha_actualizacion": timezone.localdate(),
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
            "demo_label": DEMO_LABEL,
            "funcionario": funcionario,
            "funcionarios": funcionarios,
            "indicadores": indicadores,
            "ponderador_total": Indicador.porcentaje_ponderadores(funcionario.cargo_id) if funcionario else Decimal("0.00"),
            "actividades": _actividades_demo(funcionario.nombre if funcionario else "Equipo territorial"),
        },
    )


@sgr_required
def tubo(request):
    profile = _profile(request.user)
    commitments = [
        {"titulo": "Preparar jornada de coordinación vecinal", "estado": "En preparación", "fecha": timezone.localdate() + timedelta(days=2)},
        {"titulo": "Revisar solicitudes comunitarias", "estado": "En seguimiento", "fecha": timezone.localdate() + timedelta(days=4)},
        {"titulo": "Coordinar recorrido territorial", "estado": "Programado", "fecha": timezone.localdate() + timedelta(days=7)},
    ]
    return render(
        request,
        "gestion/tubo.html",
        {"demo_label": DEMO_LABEL, "compromisos": commitments, "delegacion": profile.delegacion if profile else None},
    )


@sgr_required
def semaforo(request):
    staff = funcionarios_visibles(request.user).filter(activo=True)
    cargo_ids = staff.values_list("cargo_id", flat=True).distinct()
    indicators = Indicador.objects.filter(cargo_id__in=cargo_ids, activo=True).select_related("cargo")
    rows = []
    for index, indicator in enumerate(indicators):
        avance = (72, 48, 91, 36, 65)[index % 5]
        esperado = 60
        rows.append(
            {
                "indicador": indicator,
                "avance": avance,
                "esperado": esperado,
                "estado": "En rango" if avance >= esperado else "Requiere seguimiento",
                "estado_ok": avance >= esperado,
            }
        )
    return render(
        request,
        "gestion/semaforo.html",
        {"demo_label": DEMO_LABEL, "filas": rows, "fecha": timezone.localdate()},
    )


@sgr_required
def resumen(request):
    staff = funcionarios_visibles(request.user).filter(activo=True)
    delegation_ids = staff.values_list("delegacion_id", flat=True).distinct()
    delegaciones = Delegacion.objects.filter(activo=True, pk__in=delegation_ids)
    rows = [
        {
            "delegacion": delegation,
            "actividades": 3 + index,
            "compromisos": 1 + (index % 3),
            "ultima_actualizacion": timezone.localdate() - timedelta(days=index),
        }
        for index, delegation in enumerate(delegaciones)
    ]
    return render(
        request,
        "gestion/resumen.html",
        {
            "demo_label": DEMO_LABEL,
            "filas": rows,
            "cantidad_actividades": sum(row["actividades"] for row in rows),
            "cantidad_compromisos": sum(row["compromisos"] for row in rows),
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


def _actividades_demo(nombre):
    today = timezone.localdate()
    return [
        {"titulo": "Orientación a vecinas y vecinos", "fecha": today - timedelta(days=1), "responsable": nombre, "estado": "Registrada (demo)"},
        {"titulo": "Coordinación de apoyo comunitario", "fecha": today - timedelta(days=3), "responsable": nombre, "estado": "Revisada (demo)"},
    ]
