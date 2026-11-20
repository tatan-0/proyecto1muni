from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from gestion.models import Cargo, Delegacion, Evidencia, Funcionario, Indicador, Servicio, Tarea


class SGRModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.Select):
                component = "select w-full"
            elif isinstance(widget, forms.CheckboxInput):
                component = "checkbox"
            elif isinstance(widget, forms.Textarea):
                component = "textarea w-full"
            else:
                component = "input w-full"
            widget.attrs["class"] = f"{existing} {component}".strip()
            field.error_messages.setdefault("required", "Este campo es obligatorio.")


class DelegacionForm(SGRModelForm):
    class Meta:
        model = Delegacion
        fields = ("nombre", "descripcion_territorial", "activo")


class CargoForm(SGRModelForm):
    class Meta:
        model = Cargo
        fields = ("nombre", "area", "activo")


class FuncionarioForm(SGRModelForm):
    class Meta:
        model = Funcionario
        fields = ("usuario", "nombre", "cargo", "delegacion", "activo")
        labels = {"usuario": "Cuenta de acceso", "nombre": "Nombre visible"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        available_users = User.objects.filter(is_active=True, perfil_sgr__isnull=True)
        if self.instance.pk:
            available_users = User.objects.filter(Q(pk=self.instance.usuario_id) | Q(perfil_sgr__isnull=True, is_active=True))
        self.fields["usuario"].queryset = available_users.order_by("username")
        self.fields["cargo"].queryset = _active_or_current(Cargo.objects.all(), self.instance, "cargo_id")
        self.fields["delegacion"].queryset = _active_or_current(Delegacion.objects.all(), self.instance, "delegacion_id")


class IndicadorForm(SGRModelForm):
    class Meta:
        model = Indicador
        fields = ("nombre", "cargo", "ponderador", "meta_trimestral", "unidad_medida", "activo")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cargo"].queryset = _active_or_current(Cargo.objects.all(), self.instance, "cargo_id")
        self.fields["ponderador"].help_text = "Porcentaje entre 0 y 100. La suma del cargo se revisa en el catálogo."
        self.fields["meta_trimestral"].help_text = "Debe ser un número entero mayor que cero."


class ServicioForm(SGRModelForm):
    class Meta:
        model = Servicio
        fields = ("nombre", "descripcion", "activo")


def _active_or_current(queryset, instance, field_name):
    active = queryset.filter(activo=True)
    current_id = getattr(instance, field_name, None)
    if instance.pk and current_id:
        return queryset.filter(Q(activo=True) | Q(pk=current_id)).distinct()
    return active
class TareaForm(SGRModelForm):
    class Meta:
        model = Tarea
        fields = ("titulo", "descripcion", "sector", "ubicacion", "prioridad",
                  "fecha_limite", "profesional", "delegado")
        widgets = {
            "fecha_limite": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "ubicacion": forms.TextInput(attrs={
                "list": "lista-calles", "autocomplete": "off",
                "placeholder": "Ej: Av. Francisco de Aguirre 450, entre Los Carrera y Brasil",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].queryset = Delegacion.objects.filter(activo=True)
        self.fields["sector"].required = True
        self.fields["sector"].empty_label = "Selecciona un sector"
        self.fields["ubicacion"].help_text = (
            "Escribe la calle o dirección exacta. Si no está en la lista, "
            "escríbela y quedará disponible para próximas tareas."
        )
        User = get_user_model()
        self.fields["profesional"].queryset = User.objects.filter(
            groups__name="PROFESIONAL",
            is_active=True,
        ).distinct()
        self.fields["delegado"].queryset = User.objects.filter(
            groups__name="DELEGADO",
            is_active=True,
        ).distinct()


class EvidenciaForm(SGRModelForm):
    class Meta:
        model = Evidencia
        fields = ("imagen", "descripcion")
        labels = {"imagen": "Foto de evidencia", "descripcion": "Descripción (opcional)"}
        widgets = {"imagen": forms.ClearableFileInput(attrs={"accept": "image/*", "capture": "environment"})}

    def clean_imagen(self):
        img = self.cleaned_data["imagen"]
        if img.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La foto no puede superar 5 MB.")
        tipo = getattr(img, "content_type", "")
        if tipo not in ("image/jpeg", "image/png", "image/webp"):
            raise forms.ValidationError("Solo se aceptan fotos JPG, PNG o WebP.")
        return img