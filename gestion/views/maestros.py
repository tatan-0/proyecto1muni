from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from gestion.models import Cargo, Delegacion, Funcionario
from gestion.permissions import usuario_es_admin


def _separar_funciones(texto):
    lineas = [linea.strip() for linea in (texto or "").splitlines() if linea.strip()]
    resumen = lineas[0] if lineas else ""
    tareas = [linea.lstrip("•- ").strip() for linea in lineas[1:] if linea.strip("•- ")]
    return resumen, tareas


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return usuario_es_admin(self.request.user)


class MaestroListView(AdminRequiredMixin, ListView):
    template_name = "gestion/maestros/lista.html"
    entity = ""
    entity_label = ""
    description = ""
    search_fields = {
        "delegaciones": ("nombre", "descripcion_territorial"),
        "cargos": ("nombre", "area"),
        "funcionarios": ("nombre", "usuario__username", "cargo__nombre", "delegacion__nombre"),
        "indicadores": ("nombre", "cargo__nombre", "unidad_medida"),
        "servicios": ("nombre", "descripcion"),
        "organizaciones": (
            "nombre",
            "tipo",
            "descripcion",
            "delegacion__nombre",
            "domicilio_legal",
            "numero_registro_pj",
        ),
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.entity == "delegaciones":
            queryset = queryset.annotate(
                funcionarios_activos=Count("funcionarios", filter=Q(funcionarios__activo=True), distinct=True)
            ).prefetch_related(
                Prefetch(
                    "funcionarios",
                    queryset=Funcionario.objects.filter(activo=True)
                    .select_related("cargo")
                    .order_by("nombre"),
                    to_attr="equipo_activo",
                )
            )
        self.show_inactive = self.request.GET.get("estado") == "todos"
        if not self.show_inactive:
            queryset = queryset.filter(activo=True)
        self.search_query = self.request.GET.get("q", "").strip()
        if self.search_query:
            search = Q()
            for field in self.search_fields[self.entity]:
                search |= Q(**{f"{field}__icontains": self.search_query})
            queryset = queryset.filter(search)
        return queryset

    def _list_url(self, include_inactive, include_search=True):
        params = self.request.GET.copy()
        params.pop("estado", None)
        if not include_search:
            params.pop("q", None)
        if include_inactive:
            params["estado"] = "todos"
        url = reverse(f"maestros:{self.entity}-lista")
        return f"{url}?{params.urlencode()}" if params else url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "entity": self.entity,
                "entity_label": self.entity_label,
                "description": self.description,
                "show_inactive": self.show_inactive,
                "create_url": reverse(f"maestros:{self.entity}-crear"),
                "inactive_url": self._list_url(include_inactive=True),
                "active_url": self._list_url(include_inactive=False),
                "clear_search_url": self._list_url(
                    include_inactive=self.show_inactive,
                    include_search=False,
                ),
                "search_query": self.search_query,
                "result_count": len(context["object_list"]),
            }
        )
        if self.entity == "delegaciones":
            for delegacion in context["object_list"]:
                descripcion = (delegacion.descripcion_territorial or "").strip()
                marcas_de_plantilla = ("ficticio", "demostración", "ejemplo")
                delegacion.descripcion_visible = (
                    "" if any(marca in descripcion.casefold() for marca in marcas_de_plantilla) else descripcion
                )
            perfiles = []
            for cargo in Cargo.objects.filter(activo=True).order_by("nombre"):
                resumen, tareas = _separar_funciones(cargo.funciones)
                if resumen:
                    perfiles.append(
                        {
                            "nombre": cargo.nombre,
                            "area": cargo.area,
                            "resumen": resumen,
                            "tareas": tareas,
                        }
                    )
            context.update(
                {
                    "delegaciones_activas": Delegacion.objects.filter(activo=True).count(),
                    "funcionarios_activos_total": Funcionario.objects.filter(
                        activo=True, delegacion__activo=True
                    ).count(),
                    "roles_guia": perfiles,
                }
            )
        return context


class DelegacionDetailView(AdminRequiredMixin, DetailView):
    model = Delegacion
    template_name = "gestion/maestros/delegacion_detail.html"
    context_object_name = "delegacion"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        funcionarios = list(
            self.object.funcionarios.select_related("cargo", "usuario").order_by("nombre")
        )
        for funcionario in funcionarios:
            resumen, tareas = _separar_funciones(funcionario.cargo.funciones)
            funcionario.funciones_resumen = resumen
            funcionario.funciones_clave = tareas
            es_cuenta_inicial = (
                (
                    funcionario.usuario
                    and funcionario.usuario.get_username().startswith("demo_funcionario_")
                )
                or funcionario.nombre.casefold().startswith("funcionario/a de demostración")
            )
            funcionario.nombre_visible = (
                "Identidad por registrar" if es_cuenta_inicial else funcionario.nombre
            )

        descripcion = (self.object.descripcion_territorial or "").strip()
        marcas_de_plantilla = ("ficticio", "demostración", "ejemplo")
        context["descripcion_territorial_visible"] = (
            "" if any(marca in descripcion.casefold() for marca in marcas_de_plantilla) else descripcion
        )

        activos = [funcionario for funcionario in funcionarios if funcionario.activo]
        context["funcionarios"] = funcionarios
        context["cantidad_funcionarios"] = len(funcionarios)
        context["cantidad_funcionarios_activos"] = len(activos)
        context["cantidad_cargos"] = len({funcionario.cargo_id for funcionario in activos})
        context["cantidad_perfiles_descritos"] = len(
            {funcionario.cargo_id for funcionario in activos if funcionario.funciones_resumen}
        )
        return context


class MaestroCreateView(AdminRequiredMixin, CreateView):
    template_name = "gestion/maestros/formulario.html"
    entity = ""
    entity_label = ""

    def get_success_url(self):
        return reverse(f"maestros:{self.entity}-lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"entity": self.entity, "entity_label": self.entity_label, "action_label": "Crear"})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.entity_label} creado correctamente.")
        return super().form_valid(form)


class MaestroUpdateView(AdminRequiredMixin, UpdateView):
    template_name = "gestion/maestros/formulario.html"
    entity = ""
    entity_label = ""

    def get_success_url(self):
        return reverse(f"maestros:{self.entity}-lista")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"entity": self.entity, "entity_label": self.entity_label, "action_label": "Editar"})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.entity_label} actualizado correctamente.")
        return super().form_valid(form)


class MaestroDesactivarView(AdminRequiredMixin, View):
    template_name = "gestion/maestros/confirmar_baja.html"
    model = None
    entity = ""
    entity_label = ""

    def get_object(self):
        return get_object_or_404(self.model, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        return render(
            request,
            self.template_name,
            {"object": self.get_object(), "entity": self.entity, "entity_label": self.entity_label},
        )

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.activo:
            obj.activo = False
            obj.save(update_fields=["activo"])
            messages.success(request, f"{self.entity_label} desactivado; sus relaciones se conservaron.")
        else:
            messages.info(request, f"{self.entity_label} ya estaba desactivado.")
        return HttpResponseRedirect(reverse(f"maestros:{self.entity}-lista"))
