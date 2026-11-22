"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from gestion.views.cuentas import CambiarClaveView, RecuperarConfirmarView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('maestros/', include('gestion.maestros_urls')),
    path(
        "recuperar/<uidb64>/<token>/",
        RecuperarConfirmarView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "recuperar/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/recuperar_form.html",
            email_template_name="registration/recuperar_correo.html",
            subject_template_name="registration/recuperar_asunto.txt",
        ),
        name="password_reset",
    ),
    path(
        "cuenta/cambiar-clave/",
        CambiarClaveView.as_view(),
        name="cambiar_clave",
    ),
    path(
        "recuperar/listo/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/recuperar_listo.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "recuperar/enviado/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/recuperar_enviado.html",
        ),
        name="password_reset_done",
    ),
    path('', include('gestion.urls')),
]
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)