from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gestion", "0005_tarea_indicador_alter_tarea_estado"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="debe_cambiar_clave",
            field=models.BooleanField(default=False, verbose_name="debe cambiar la contraseña"),
        ),
    ]
