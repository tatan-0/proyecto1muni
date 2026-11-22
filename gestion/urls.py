from django.urls import path

from gestion.views import dashboard, ficha, health_check, login_view, logout_view, registrar_gestion, resumen, semaforo, tubo

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
]
