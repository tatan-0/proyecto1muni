from .auth import login_view, logout_view
from .dashboard import dashboard, ficha, resumen, semaforo, tubo
from .health import health_check
from .tareas import (
    crear_tarea, detalle_tarea, mis_tareas,
    panel_cumplimiento, revisar_tarea, subir_evidencia,
)
__all__ = ["dashboard", "ficha", "health_check", "login_view", "logout_view", "resumen", "semaforo", "tubo"]
