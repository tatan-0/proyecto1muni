from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from ..forms_usuarios import (
    NOMBRES_ROL, ClaveForm, UsuarioCrearForm, UsuarioEditarForm, asignar_rol,
)
from ..permissions import roles_de

User = get_user_model()


def _solo_admin(user):
    if "admin" not in roles_de(user):
        raise PermissionDenied


def _rol_de(user):
    for nombre in user.groups.filter(name__in=NOMBRES_ROL).values_list("name", flat=True):
        return nombre
    return ""


@login_required
def usuarios_lista(request):
    _solo_admin(request.user)
    usuarios = list(User.objects.order_by("username"))
    for u in usuarios:
        u.rol = _rol_de(u) or ("SUPERUSUARIO" if u.is_superuser else "Sin rol")
    return render(request, "gestion/usuarios_lista.html", {"usuarios": usuarios})


@login_required
def usuario_crear(request):
    _solo_admin(request.user)
    form = UsuarioCrearForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        messages.success(request, f"Usuario {user.username} creado. Entrégale su contraseña de forma segura.")
        return redirect("gestion:usuarios_lista")
    return render(request, "gestion/usuario_form.html", {"form": form, "titulo": "Nuevo usuario", "boton": "Crear usuario"})


@login_required
def usuario_editar(request, pk):
    _solo_admin(request.user)
    user = get_object_or_404(User, pk=pk)
    inicial = {
        "first_name": user.first_name, "last_name": user.last_name, "email": user.email,
        "rol": _rol_de(user) or "PROFESIONAL", "is_active": user.is_active,
    }
    form = UsuarioEditarForm(request.POST or None, initial=inicial)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        if user.pk == request.user.pk and (not d["is_active"] or d["rol"] != "ADMINISTRADOR"):
            messages.error(request, "No puedes desactivarte ni quitarte el rol de administrador a ti mismo.")
        else:
            user.first_name, user.last_name, user.email = d["first_name"], d["last_name"], d["email"]
            user.is_active = d["is_active"]
            user.save()
            asignar_rol(user, d["rol"])
            messages.success(request, f"Usuario {user.username} actualizado.")
            return redirect("gestion:usuarios_lista")
    return render(request, "gestion/usuario_form.html", {
        "form": form, "titulo": f"Editar {user.username}", "boton": "Guardar cambios", "editando": user,
    })


@login_required
def usuario_clave(request, pk):
    _solo_admin(request.user)
    user = get_object_or_404(User, pk=pk)
    form = ClaveForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user.set_password(form.cleaned_data["password1"])
        user.save()
        messages.success(request, f"Contraseña de {user.username} cambiada.")
        return redirect("gestion:usuarios_lista")
    return render(request, "gestion/usuario_form.html", {
        "form": form, "titulo": f"Nueva contraseña para {user.username}", "boton": "Cambiar contraseña",
    })
