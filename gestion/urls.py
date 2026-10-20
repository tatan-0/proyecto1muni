from django.urls import path

from gestion.views import dashboard, login_view, logout_view

app_name = "gestion"

urlpatterns = [
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("", dashboard, name="dashboard"),
]
