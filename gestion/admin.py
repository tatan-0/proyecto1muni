import secrets

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Ausencia,
    Cargo,
    Delegacion,
    Evidencia,
    Funcionario,
    Gestion,
    Indicador,
    MetaIndividual,
    OrganizacionComunitaria,
    PerfilUsuario,
    Servicio,
    Tarea,
)

User = get_user_model()


# --- Usuarios: acción para asignar contraseña temporal -----------------------
admin.site.unregister(User)


@admin.register(User)
class UsuarioAdmin(BaseUserAdmin):
    actions = ["asignar_clave_temporal"]
    list_display = BaseUserAdmin.list_display + ("clave_temporal_pendiente",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("perfil_sector")

    @admin.display(boolean=True, description="Clave temporal pendiente")
    def clave_temporal_pendiente(self, obj):
        perfil = getattr(obj, "perfil_sector", None)
        return bool(perfil and perfil.debe_cambiar_clave)

    @admin.action(description="Asignar contraseña temporal (obliga a cambiarla al ingresar)")
    def asignar_clave_temporal(self, request, queryset):
        for user in queryset:
            if user == request.user:
                self.message_user(
                    request,
                    f"{user.username}: no se cambió, es tu propia cuenta.",
                    level=messages.WARNING,
                )
                continue
            clave = secrets.token_urlsafe(9)
            user.set_password(clave)
            user.save(update_fields=["password"])
            PerfilUsuario.objects.update_or_create(
                usuario=user, defaults={"debe_cambiar_clave": True}
            )
            self.message_user(
                request,
                f"{user.username}: contraseña temporal {clave} (se muestra solo ahora).",
                level=messages.SUCCESS,
            )


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "sector", "debe_cambiar_clave")
    list_filter = ("debe_cambiar_clave", "sector")
    search_fields = ("usuario__username",)


# --- Tareas y evidencias (una tarea aprobada queda en solo lectura) ----------
@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "profesional", "delegado", "estado", "cumplida", "fecha_limite")
    list_filter = ("estado", "cumplida", "prioridad")

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.estado == Tarea.Estado.APROBADA:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.estado == Tarea.Estado.APROBADA:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ("tarea", "subida_por", "subida_en")

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.tarea.estado == Tarea.Estado.APROBADA:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.tarea.estado == Tarea.Estado.APROBADA:
            return False
        return super().has_delete_permission(request, obj)


# --- Catálogos ---------------------------------------------------------------
@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion_territorial")


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "area", "activo")
    list_filter = ("activo", "area")
    search_fields = ("nombre", "area", "funciones")


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "usuario", "cargo", "delegacion", "activo")
    list_filter = ("activo", "cargo", "delegacion")
    search_fields = ("nombre", "usuario__username", "usuario__email")
    list_select_related = ("usuario", "cargo", "delegacion")


@admin.register(Indicador)
class IndicadorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cargo", "ponderador", "meta_trimestral", "unidad_medida", "activo")
    list_filter = ("activo", "cargo")
    search_fields = ("nombre", "cargo__nombre")
    list_select_related = ("cargo",)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")


@admin.register(MetaIndividual)
class MetaIndividualAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "indicador", "anio", "trimestre", "meta")
    list_filter = ("anio", "trimestre")
    search_fields = ("funcionario__nombre", "indicador__nombre")
    list_select_related = ("funcionario", "indicador")


@admin.register(OrganizacionComunitaria)
class OrganizacionComunitariaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "delegacion", "socios_activos", "numero_registro_pj", "activo")
    list_filter = ("tipo", "delegacion", "activo")
    search_fields = ("nombre", "descripcion", "domicilio_legal", "numero_registro_pj")
    list_select_related = ("delegacion",)


@admin.register(Gestion)
class GestionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "fecha", "funcionario", "indicador", "usuario_es_delegado")
    list_filter = ("tipo", "accion", "fecha", "funcionario__delegacion")
    search_fields = ("titulo", "usuario_nombre", "usuario_telefono", "funcionario__nombre")
    list_select_related = ("funcionario", "indicador", "organizacion", "creado_por")
    readonly_fields = ("creado_por", "creado_en")


@admin.register(Ausencia)
class AusenciaAdmin(admin.ModelAdmin):
    list_display = ("funcionario", "tipo", "fecha_desde", "fecha_hasta", "ingresado_por")
    list_filter = ("tipo", "fecha_desde", "funcionario__delegacion")
    list_select_related = ("funcionario", "ingresado_por")
    readonly_fields = ("ingresado_por", "creado_en")
