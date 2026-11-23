from django.urls import path

from gestion.views import (
    crear_tarea, dashboard, detalle_tarea, ficha, health_check, login_view,
    logout_view, mis_tareas, panel_cumplimiento, registrar_gestion, resumen,
    revisar_tarea, semaforo, subir_evidencia, tubo,
)
from gestion.views.metas import metas_crear, metas_editar, metas_eliminar, metas_lista
from gestion.views.usuarios import usuario_clave, usuario_crear, usuario_editar, usuarios_lista

app_name = "gestion"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard, name="dashboard"),
    path("ficha/", ficha, name="ficha"),
    path("gestiones/nueva/", registrar_gestion, name="registrar_gestion"),
    path("agenda/", tubo, name="tubo"),
    path("semaforo/", semaforo, name="semaforo"),
    path("resumen/", resumen, name="resumen"),
    # Tareas y evidencias
    path("tareas/", mis_tareas, name="mis_tareas"),
    path("tareas/nueva/", crear_tarea, name="crear_tarea"),
    path("tareas/<int:pk>/", detalle_tarea, name="detalle_tarea"),
    path("tareas/<int:pk>/evidencia/", subir_evidencia, name="subir_evidencia"),
    path("tareas/<int:pk>/revisar/", revisar_tarea, name="revisar_tarea"),
    path("cumplimiento/", panel_cumplimiento, name="panel_cumplimiento"),
    # Metas individuales (administrador y coordinador)
    path("metas/", metas_lista, name="metas_lista"),
    path("metas/nueva/", metas_crear, name="metas_crear"),
    path("metas/<int:pk>/", metas_editar, name="metas_editar"),
    path("metas/<int:pk>/eliminar/", metas_eliminar, name="metas_eliminar"),
    # Administración de usuarios (solo administrador)
    path("usuarios/", usuarios_lista, name="usuarios_lista"),
    path("usuarios/nuevo/", usuario_crear, name="usuario_crear"),
    path("usuarios/<int:pk>/", usuario_editar, name="usuario_editar"),
    path("usuarios/<int:pk>/clave/", usuario_clave, name="usuario_clave"),
]