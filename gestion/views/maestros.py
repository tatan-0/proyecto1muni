from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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

    def get_queryset(self):
        queryset = super().get_queryset()
        self.show_inactive = self.request.GET.get("estado") == "todos"
        if not self.show_inactive:
            queryset = queryset.filter(activo=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "entity": self.entity,
                "entity_label": self.entity_label,
                "description": self.description,
                "show_inactive": self.show_inactive,
                "create_url": reverse(f"maestros:{self.entity}-crear"),
                "inactive_url": f"{reverse(f'maestros:{self.entity}-lista')}?estado=todos",
                "active_url": reverse(f"maestros:{self.entity}-lista"),
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
