from django.contrib import admin

from .models import Cargo, Delegacion, Evidencia, Funcionario, Indicador, Servicio, Tarea


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


@admin.register(Delegacion)
class DelegacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion_territorial")


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "area", "activo")
    list_filter = ("activo", "area")
    search_fields = ("nombre", "area")


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