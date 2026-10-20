from django.contrib import admin

from .models import Cargo, Delegacion, Funcionario, Indicador, Servicio


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
