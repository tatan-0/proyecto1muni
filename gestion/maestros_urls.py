from django.urls import path

from gestion.forms import CargoForm, DelegacionForm, FuncionarioForm, IndicadorForm, ServicioForm
from gestion.models import Cargo, Delegacion, Funcionario, Indicador, Servicio
from gestion.views.maestros import MaestroCreateView, MaestroDesactivarView, MaestroListView, MaestroUpdateView

app_name = "maestros"

MAESTROS = {
    "delegaciones": {
        "model": Delegacion,
        "form_class": DelegacionForm,
        "label": "Delegaciones",
        "description": "Administra la cobertura territorial de las delegaciones municipales.",
    },
    "cargos": {
        "model": Cargo,
        "form_class": CargoForm,
        "label": "Cargos",
        "description": "Mantén los cargos y áreas asociados al seguimiento de resultados.",
    },
    "funcionarios": {
        "model": Funcionario,
        "form_class": FuncionarioForm,
        "label": "Funcionarios",
        "description": "Asocia cuentas de acceso ficticias a cargos y delegaciones.",
    },
    "indicadores": {
        "model": Indicador,
        "form_class": IndicadorForm,
        "label": "Indicadores y funciones",
        "description": "Define metas trimestrales y ponderadores por cargo.",
    },
    "servicios": {
        "model": Servicio,
        "form_class": ServicioForm,
        "label": "Servicios",
        "description": "Administra el catálogo de servicios municipales.",
    },
}

urlpatterns = []
for entity, config in MAESTROS.items():
    shared = {"entity": entity, "entity_label": config["label"]}
    urlpatterns.extend(
        [
            path(
                f"{entity}/",
                MaestroListView.as_view(model=config["model"], description=config["description"], **shared),
                name=f"{entity}-lista",
            ),
            path(
                f"{entity}/crear/",
                MaestroCreateView.as_view(model=config["model"], form_class=config["form_class"], **shared),
                name=f"{entity}-crear",
            ),
            path(
                f"{entity}/<int:pk>/editar/",
                MaestroUpdateView.as_view(model=config["model"], form_class=config["form_class"], **shared),
                name=f"{entity}-editar",
            ),
            path(
                f"{entity}/<int:pk>/desactivar/",
                MaestroDesactivarView.as_view(model=config["model"], **shared),
                name=f"{entity}-desactivar",
            ),
        ]
    )
