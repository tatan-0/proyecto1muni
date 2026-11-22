from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion', '0003_cargo_funciones'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='domicilio_legal',
            field=models.CharField(blank=True, max_length=200, verbose_name='domicilio legal'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='socios_activos',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='socios activos'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='fecha_constitucion',
            field=models.DateField(blank=True, null=True, verbose_name='fecha de constitución'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='numero_registro_pj',
            field=models.CharField(blank=True, max_length=40, verbose_name='Nº de registro de personalidad jurídica'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='fecha_inscripcion_registro',
            field=models.DateField(blank=True, null=True, verbose_name='fecha de inscripción en el registro'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='numero_registro_directiva',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Nº de registro de directiva'),
        ),
        migrations.AddField(
            model_name='organizacioncomunitaria',
            name='observaciones_origen',
            field=models.TextField(blank=True, verbose_name='observaciones de la carga de datos'),
        ),
        migrations.AlterField(
            model_name='organizacioncomunitaria',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('funcional', 'Organización comunitaria funcional'),
                    ('adulto_mayor', 'Club de adulto mayor'),
                    ('deportiva', 'Organización deportiva'),
                    ('cultural_juvenil', 'Centro cultural, de madres o agrupación juvenil'),
                    ('comite', 'Comité vecinal, de allegados o de seguridad'),
                    ('sin_clasificar', 'Sin clasificar'),
                ],
                max_length=24,
                verbose_name='tipo',
            ),
        ),
    ]
