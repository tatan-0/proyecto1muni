from django.urls import path

from gestion.views import (
    crear_tarea, dashboard, detalle_tarea, ficha, health_check, login_view,
    logout_view, mis_tareas, panel_cumplimiento, resumen, revisar_tarea,
    semaforo, subir_evidencia, tubo,
)

app_name = "gestion"

urlpatterns = [
    path("health/", health_check, name="health"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard, name="dashboard"),
    path("ficha/", ficha, name="ficha"),
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
]
