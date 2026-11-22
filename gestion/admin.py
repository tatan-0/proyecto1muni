from django.contrib import admin

from .models import Ausencia, Cargo, Delegacion, Funcionario, Gestion, Indicador, OrganizacionComunitaria, Servicio


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


@admin.register(OrganizacionComunitaria)
class OrganizacionComunitariaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "delegacion", "activo")
    list_filter = ("tipo", "delegacion", "activo")
    search_fields = ("nombre", "descripcion")
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
