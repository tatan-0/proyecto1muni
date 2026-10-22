from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from gestion.permissions import usuario_es_admin


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
    }

    def get_queryset(self):
        queryset = super().get_queryset()
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
