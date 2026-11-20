import django.db.models.deletion
from django.db import migrations, models

SECTORES = (
    "Delegación Rural",
    "Delegación Centro",
    "Delegación Avenida del Mar",
    "Delegación La Antena - La Florida",
    "Delegación Las Compañías",
    "Delegación La Pampa",
)


def crear_sectores(apps, schema_editor):
    Delegacion = apps.get_model("gestion", "Delegacion")
    for nombre in SECTORES:
        Delegacion.objects.get_or_create(
            nombre=nombre,
            defaults={"descripcion_territorial": "Registro territorial ficticio para demostración.", "activo": True},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("gestion", "0002_tarea_evidencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="tarea",
            name="sector",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="tareas", to="gestion.delegacion", verbose_name="Sector",
            ),
        ),
        migrations.AlterField(
            model_name="tarea",
            name="ubicacion",
            field=models.CharField(blank=True, max_length=200, verbose_name="Calle o dirección"),
        ),
        migrations.RunPython(crear_sectores, migrations.RunPython.noop),
    ]
