from django.urls import path

from gestion.views import dashboard, ficha, login_view, logout_view, resumen, semaforo, tubo

app_name = "gestion"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard, name="dashboard"),
    path("ficha/", ficha, name="ficha"),
    path("agenda/", tubo, name="tubo"),
    path("semaforo/", semaforo, name="semaforo"),
    path("resumen/", resumen, name="resumen"),
]
