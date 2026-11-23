from .auth import login_view, logout_view
from .dashboard import dashboard, ficha, registrar_gestion, resumen, semaforo, tubo
from .health import health_check
from .tareas import (
    crear_tarea, detalle_tarea, mis_tareas,
    panel_cumplimiento, revisar_tarea, subir_evidencia,
)

__all__ = [
    "crear_tarea",
    "dashboard",
    "detalle_tarea",
    "ficha",
    "health_check",
    "login_view",
    "logout_view",
    "mis_tareas",
    "panel_cumplimiento",
    "registrar_gestion",
    "resumen",
    "revisar_tarea",
    "semaforo",
    "subir_evidencia",
    "tubo",
]