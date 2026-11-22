from .auth import login_view, logout_view
from .dashboard import dashboard, ficha, registrar_gestion, resumen, semaforo, tubo
from .health import health_check

__all__ = [
    "dashboard",
    "ficha",
    "health_check",
    "login_view",
    "logout_view",
    "registrar_gestion",
    "resumen",
    "semaforo",
    "tubo",
]
