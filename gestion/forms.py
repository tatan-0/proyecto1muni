from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from gestion.models import (
    Ausencia,
    Cargo,
    Delegacion,
    Evidencia,
    Funcionario,
    Gestion,
    Indicador,
    OrganizacionComunitaria,
    Servicio,
    Tarea,
)


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
        fields = ("nombre", "area", "funciones", "activo")
        labels = {"funciones": "Funciones principales"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["funciones"].help_text = "Responsabilidades del cargo según el Descriptor de Funciones 2026."


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


class OrganizacionComunitariaForm(SGRModelForm):
    class Meta:
        model = OrganizacionComunitaria
        fields = (
            "nombre",
            "tipo",
            "descripcion",
            "delegacion",
            "domicilio_legal",
            "socios_activos",
            "fecha_constitucion",
            "numero_registro_pj",
            "fecha_inscripcion_registro",
            "numero_registro_directiva",
            "observaciones_origen",
            "activo",
        )
        widgets = {
            "fecha_constitucion": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "fecha_inscripcion_registro": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "observaciones_origen": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["delegacion"].queryset = Delegacion.objects.filter(activo=True)
        self.fields["delegacion"].required = False


class GestionForm(SGRModelForm):
    class Meta:
        model = Gestion
        fields = (
            "tipo",
            "accion",
            "fecha",
            "indicador",
            "organizacion",
            "titulo",
            "descripcion",
            "usuario_nombre",
            "usuario_telefono",
            "usuario_es_delegado",
        )
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "tipo": "Tipo de gestión",
            "accion": "Tipo de acción",
            "fecha": "Fecha de realización",
            "indicador": "Indicador asociado",
            "organizacion": "Organización comunitaria",
            "titulo": "Acción realizada",
            "descripcion": "Detalle de la acción",
            "usuario_nombre": "Nombre del usuario",
            "usuario_telefono": "Teléfono del usuario",
            "usuario_es_delegado": "El usuario es delegado",
        }

    def __init__(self, *args, funcionario, **kwargs):
        self.funcionario = funcionario
        super().__init__(*args, **kwargs)
        self.fields["indicador"].queryset = Indicador.objects.filter(cargo=funcionario.cargo, activo=True)
        self.fields["indicador"].required = False
        self.fields["organizacion"].queryset = OrganizacionComunitaria.objects.filter(activo=True).filter(
            Q(delegacion__isnull=True) | Q(delegacion=funcionario.delegacion)
        )
        self.fields["organizacion"].required = False
        self.fields["usuario_nombre"].required = False
        self.fields["usuario_telefono"].required = False
        self.fields["usuario_nombre"].help_text = "Sin nombre y teléfono la gestión se guarda, pero no suma avance."
        self.fields["usuario_telefono"].help_text = "Se requiere un teléfono de contacto para contabilizarla."
        self.fields["titulo"].widget.attrs["placeholder"] = "Ej.: Orientación realizada a vecino/a"
        self.fields["descripcion"].widget.attrs["placeholder"] = "Describe brevemente la acción efectivamente realizada."
        self.fields["usuario_nombre"].widget.attrs.update(
            {"autocomplete": "name", "placeholder": "Nombre y apellido"}
        )
        self.fields["usuario_telefono"].widget.attrs.update(
            {"autocomplete": "tel", "inputmode": "tel", "placeholder": "+56 9 1234 5678"}
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("usuario_es_delegado"):
            cleaned_data["tipo"] = Gestion.Tipo.OTRA
            cleaned_data["indicador"] = None

        fecha = cleaned_data.get("fecha")
        if fecha and not Gestion.periodo_semanal_abierto(fecha):
            self.add_error("fecha", "Solo se puede ingresar la semana actual; la semana anterior cierra el lunes.")

        indicador = cleaned_data.get("indicador")
        if indicador and indicador.cargo_id != self.funcionario.cargo_id:
            self.add_error("indicador", "El indicador no corresponde al cargo de este funcionario.")

        if fecha:
            existing = Gestion.objects.filter(funcionario=self.funcionario, fecha=fecha)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.count() >= 7:
                self.add_error("fecha", "Ya se alcanzó el máximo de siete gestiones para este día.")
        return cleaned_data

    def save(self, commit=True):
        gestion = super().save(commit=False)
        gestion.funcionario = self.funcionario
        if commit:
            gestion.save()
            self.save_m2m()
        return gestion


class AusenciaForm(SGRModelForm):
    class Meta:
        model = Ausencia
        fields = ("funcionario", "tipo", "fecha_desde", "fecha_hasta", "observacion")
        widgets = {
            "fecha_desde": forms.DateInput(attrs={"type": "date"}),
            "fecha_hasta": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, delegacion, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["funcionario"].queryset = Funcionario.objects.filter(
            delegacion=delegacion,
            activo=True,
        ).select_related("cargo")


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
                  "fecha_limite", "profesional", "delegado", "indicador")
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
        self.fields["indicador"].queryset = Indicador.objects.filter(activo=True)
        self.fields["indicador"].required = False
        self.fields["indicador"].label = "Indicador al que aporta (opcional)"

    def clean(self):
        data = super().clean()
        sector, prof = data.get("sector"), data.get("profesional")
        if sector and prof:
            perfil = getattr(prof, "perfil_sector", None)
            if perfil and perfil.sector_id and perfil.sector_id != sector.pk:
                self.add_error("profesional", f"Este profesional pertenece a {perfil.sector}. Elige un profesional de {sector}.")
        return data


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