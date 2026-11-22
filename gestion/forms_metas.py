from datetime import date

from django import forms

from .models import Funcionario, Indicador, MetaIndividual

CLASE_INPUT = "input input-bordered w-full"
CLASE_SELECT = "select select-bordered w-full"


class MetaIndividualForm(forms.ModelForm):
    class Meta:
        model = MetaIndividual
        fields = ["funcionario", "indicador", "anio", "trimestre", "meta"]
        widgets = {
            "funcionario": forms.Select(attrs={"class": CLASE_SELECT}),
            "indicador": forms.Select(attrs={"class": CLASE_SELECT}),
            "anio": forms.NumberInput(attrs={"class": CLASE_INPUT, "min": 2020, "max": 2100}),
            "trimestre": forms.Select(attrs={"class": CLASE_SELECT}),
            "meta": forms.NumberInput(attrs={"class": CLASE_INPUT, "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["funcionario"].queryset = Funcionario.objects.filter(
            activo=True
        ).select_related("cargo")
        self.fields["indicador"].queryset = Indicador.objects.filter(
            activo=True
        ).select_related("cargo")
        if not self.instance.pk:
            hoy = date.today()
            self.fields["anio"].initial = hoy.year
            self.fields["trimestre"].initial = (hoy.month - 1) // 3 + 1
