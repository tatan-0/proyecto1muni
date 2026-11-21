from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password

from .models import Delegacion, PerfilUsuario

ROLES = (
    ("ADMINISTRADOR", "Administrador"),
    ("COORDINADOR", "Coordinador"),
    ("DELEGADO", "Delegado"),
    ("PROFESIONAL", "Profesional"),
)
NOMBRES_ROL = [r[0] for r in ROLES]
User = get_user_model()


def _estilo(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.Select):
            c = "select w-full"
        elif isinstance(w, forms.CheckboxInput):
            c = "checkbox"
        else:
            c = "input w-full"
        w.attrs["class"] = (w.attrs.get("class", "") + " " + c).strip()


def guardar_sector(user, sector):
    PerfilUsuario.objects.update_or_create(usuario=user, defaults={"sector": sector})


def _campo_sector():
    return forms.ModelChoiceField(
        label="Sector (obligatorio para profesionales)", required=False,
        queryset=Delegacion.objects.filter(activo=True), empty_label="Sin sector",
    )


def _validar_sector(form, data):
    if data.get("rol") == "PROFESIONAL" and not data.get("sector"):
        form.add_error("sector", "Un profesional debe tener un sector asignado.")


def asignar_rol(user, rol):
    """Deja al usuario en un solo grupo de rol y ajusta el acceso al panel /admin/."""
    user.groups.remove(*Group.objects.filter(name__in=NOMBRES_ROL))
    user.groups.add(Group.objects.get_or_create(name=rol)[0])
    es_admin = rol == "ADMINISTRADOR"
    if user.is_staff != es_admin and not user.is_superuser:
        user.is_staff = es_admin
        user.save(update_fields=["is_staff"])


class UsuarioCrearForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150)
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Correo (opcional)", required=False)
    rol = forms.ChoiceField(label="Rol", choices=ROLES)
    sector = _campo_sector()
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=u).exists():
            raise forms.ValidationError("Ese nombre de usuario ya existe.")
        return u

    def clean(self):
        data = super().clean()
        _validar_sector(self, data)
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                try:
                    validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        return data

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d["username"], password=d["password1"], email=d["email"],
            first_name=d["first_name"], last_name=d["last_name"],
        )
        asignar_rol(user, d["rol"])
        guardar_sector(user, d["sector"])
        return user


class UsuarioEditarForm(forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=150)
    last_name = forms.CharField(label="Apellido", max_length=150)
    email = forms.EmailField(label="Correo (opcional)", required=False)
    rol = forms.ChoiceField(label="Rol", choices=ROLES)
    sector = _campo_sector()
    is_active = forms.BooleanField(label="Cuenta activa", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def clean(self):
        data = super().clean()
        _validar_sector(self, data)
        return data


class ClaveForm(forms.Form):
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label="Repetir contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _estilo(self)

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2:
            if p1 != p2:
                self.add_error("password2", "Las contraseñas no coinciden.")
            else:
                try:
                    validate_password(p1)
                except forms.ValidationError as e:
                    self.add_error("password1", e)
        return data
