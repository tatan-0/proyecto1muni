import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("gestion", "0003_tarea_sector"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sector", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="usuarios_asignados", to="gestion.delegacion", verbose_name="sector",
                )),
                ("usuario", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, related_name="perfil_sector",
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
