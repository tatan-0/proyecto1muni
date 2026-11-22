from decimal import Decimal
from datetime import timedelta
from functools import wraps
from math import floor

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET

from gestion.forms import AusenciaForm, GestionForm
from gestion.models import Ausencia, Delegacion, Funcionario, Gestion, Indicador, Servicio
from gestion.permissions import funcionarios_visibles, usuario_es_admin, usuario_tiene_acceso_sgr


def sgr_access_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not usuario_tiene_acceso_sgr(request.user):
            return HttpResponseForbidden("Tu cuenta no tiene un perfil habilitado para el SGR.")
        return view_func(request, *args, **kwargs)

    return login_required(wrapped)


def sgr_required(view_func):
    return require_GET(sgr_access_required(view_func))


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
    actividades = (
        Gestion.objects.filter(funcionario=funcionario).select_related("indicador__cargo", "organizacion")
        if funcionario
        else Gestion.objects.none()
    )
    return render(
        request,
        "gestion/ficha_funcionario.html",
        {
            "funcionario": funcionario,
            "funcionarios": funcionarios,
            "indicadores": indicadores,
            "ponderador_total": Indicador.porcentaje_ponderadores(funcionario.cargo_id) if funcionario else Decimal("0.00"),
            "actividades": actividades,
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


@sgr_access_required
def semaforo(request):
    staff = funcionarios_visibles(request.user).filter(activo=True)
    cargo_ids = staff.values_list("cargo_id", flat=True).distinct()
    indicators = Indicador.objects.filter(cargo_id__in=cargo_ids, activo=True).select_related("cargo")
    today = timezone.localdate()
    quarter_start, quarter_end = _quarter_bounds(today)
    is_delegate = request.user.groups.filter(name="DELEGADO").exists()
    profile = _profile(request.user)
    ausencia_form = None

    if request.method == "POST":
        if not is_delegate or profile is None:
            return HttpResponseForbidden("Solo el delegado puede ingresar ausencias para su delegación.")
        ausencia_form = AusenciaForm(request.POST, delegacion=profile.delegacion)
        if ausencia_form.is_valid():
            ausencia = ausencia_form.save(commit=False)
            ausencia.ingresado_por = request.user
            ausencia.full_clean()
            ausencia.save()
            messages.success(request, "Ausencia ingresada; las metas trimestrales fueron ajustadas.")
            return redirect("gestion:semaforo")

    if is_delegate and profile:
        staff = staff.filter(delegacion=profile.delegacion)
        ausencia_form = ausencia_form or AusenciaForm(delegacion=profile.delegacion)
    else:
        staff = staff.none() if not usuario_es_admin(request.user) else staff

    rows = []
    for indicator in indicators.filter(cargo__funcionarios__in=staff).distinct():
        indicator_staff = list(staff.filter(cargo=indicator.cargo))
        target_total = sum(
            _adjusted_target(indicator.meta_trimestral, employee, quarter_start, quarter_end)
            for employee in indicator_staff
        )
        activity_filters = {
            "funcionario__in": indicator_staff,
            "indicador": indicator,
            "fecha__gte": quarter_start,
            "fecha__lte": quarter_end,
            "tipo__in": (Gestion.Tipo.ACTIVIDAD, Gestion.Tipo.SOLICITUD),
            "accion": Gestion.Accion.REALIZACION,
            "usuario_es_delegado": False,
        }
        completed = (
            Gestion.objects.filter(**activity_filters)
            .exclude(usuario_nombre="")
            .exclude(usuario_telefono="")
            .count()
        )
        progress = min(completed / target_total * 100, 120) if target_total else 0
        rows.append(
            {
                "indicador": indicator,
                "meta_ajustada": target_total,
                "acciones": completed,
                "avance": round(progress, 1),
                "puntaje": round(float(indicator.ponderador) * progress / 100, 2),
            }
        )

    absences = (
        Ausencia.objects.filter(funcionario__in=staff, fecha_hasta__gte=quarter_start, fecha_desde__lte=quarter_end)
        .select_related("funcionario")
        .order_by("-fecha_desde")
    )
    return render(
        request,
        "gestion/semaforo.html",
        {
            "filas": rows,
            "cantidad_indicadores": len(rows),
            "total_acciones_validas": sum(row["acciones"] for row in rows),
            "cantidad_funcionarios": staff.count(),
            "ausencia_form": ausencia_form,
            "puede_ingresar_ausencia": is_delegate and profile is not None,
            "ausencias": absences,
            "trimestre_desde": quarter_start,
            "trimestre_hasta": quarter_end,
        },
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


def _quarter_bounds(day):
    quarter_month = ((day.month - 1) // 3) * 3 + 1
    start = day.replace(month=quarter_month, day=1)
    if quarter_month == 10:
        end = day.replace(month=12, day=31)
    else:
        next_quarter = day.replace(month=quarter_month + 3, day=1)
        end = next_quarter - timedelta(days=1)
    return start, end


def _business_days(start, end):
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def _adjusted_target(target, funcionario, quarter_start, quarter_end):
    quarter_days = _business_days(quarter_start, quarter_end)
    if not quarter_days:
        return target
    absences = Ausencia.objects.filter(
        funcionario=funcionario,
        fecha_hasta__gte=quarter_start,
        fecha_desde__lte=quarter_end,
    )
    absent_days = set()
    for absence in absences:
        current = max(absence.fecha_desde, quarter_start)
        end = min(absence.fecha_hasta, quarter_end)
        while current <= end:
            if current.weekday() < 5:
                absent_days.add(current)
            current += timedelta(days=1)
    available_days = max(quarter_days - len(absent_days), 0)
    return floor(target * available_days / quarter_days + 0.5)


@sgr_access_required
def registrar_gestion(request):
    try:
        funcionario = request.user.perfil_sgr
    except Funcionario.DoesNotExist:
        return HttpResponseForbidden("Tu cuenta no tiene un perfil de funcionario activo.")
    if not funcionario.activo:
        return HttpResponseForbidden("El perfil de funcionario está inactivo.")

    if request.method == "POST":
        form = GestionForm(request.POST, funcionario=funcionario)
        if form.is_valid():
            gestion = form.save(commit=False)
            gestion.creado_por = request.user
            gestion.save()
            messages.success(
                request,
                "Gestión registrada. Solo las acciones realizadas con datos completos de usuario aportan avance.",
            )
            return redirect(f"{reverse('gestion:ficha')}?funcionario={funcionario.pk}")
    else:
        form = GestionForm(funcionario=funcionario)
    return render(request, "gestion/registrar_gestion.html", {"form": form, "funcionario": funcionario})
