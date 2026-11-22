from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum

class Tarea(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROGRESO = "en_progreso", "En progreso"
        EN_REVISION = "en_revision", "En revisión"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"
        MAS_ANTECEDENTES = "mas_antecedentes", "Más antecedentes"

    class Prioridad(models.TextChoices):
        ALTA = "alta", "Alta"
        MEDIA = "media", "Media"
        BAJA = "baja", "Baja"

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    sector = models.ForeignKey(
        "Delegacion", null=True, blank=True, on_delete=models.PROTECT,
        related_name="tareas", verbose_name="Sector",
    )
    ubicacion = models.CharField("Calle o dirección", max_length=200, blank=True)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.PENDIENTE)

    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tareas_creadas"
    )
    profesional = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tareas_asignadas",
        limit_choices_to={"groups__name": "PROFESIONAL"},
    )
    delegado = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tareas_a_revisar",
        limit_choices_to={"groups__name": "DELEGADO"},
    )
    indicador = models.ForeignKey(
        "Indicador", null=True, blank=True, on_delete=models.PROTECT,
        related_name="tareas", verbose_name="Indicador al que aporta",
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    @property
    def lugar(self):
        partes = [str(self.sector) if self.sector_id else "", self.ubicacion]
        return " · ".join(p for p in partes if p)

    cumplida = models.BooleanField(default=False)
    validada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tareas_validadas",
    )
    validada_en = models.DateTimeField(null=True, blank=True)
    observaciones_revision = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha_limite", "-creada_en"]

    def _estado_guardado(self):
        if not self.pk:
            return None
        return Tarea.objects.filter(pk=self.pk).values_list("estado", flat=True).first()

    def save(self, *args, **kwargs):
        if self._estado_guardado() == self.Estado.APROBADA:
            raise ValidationError("Una tarea aprobada no se puede modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self._estado_guardado() == self.Estado.APROBADA:
            raise ValidationError("Una tarea aprobada no se puede eliminar.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.titulo


class Evidencia(models.Model):
    class Tipo(models.TextChoices):
        EJECUCION = "ejecucion", "Evidencia de ejecución"
        VERIFICACION = "verificacion", "Verificación del delegado"

    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="evidencias")
    imagen = models.ImageField(upload_to="evidencias/%Y/%m/")
    descripcion = models.CharField(max_length=200, blank=True)
    tipo = models.CharField(max_length=15, choices=Tipo.choices, default=Tipo.EJECUCION)
    subida_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subida_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subida_en"]

    def _tarea_aprobada(self):
        return Tarea.objects.filter(
            pk=self.tarea_id, estado=Tarea.Estado.APROBADA
        ).exists()

    def save(self, *args, **kwargs):
        if self._tarea_aprobada():
            raise ValidationError("La tarea está aprobada: sus evidencias ya no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self._tarea_aprobada():
            raise ValidationError("La tarea está aprobada: sus evidencias ya no se pueden modificar.")
        return super().delete(*args, **kwargs)


class Delegacion(models.Model):
    nombre = models.CharField("nombre", max_length=120, unique=True)
    descripcion_territorial = models.TextField("descripción territorial", blank=True)
    activo = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "delegación"
        verbose_name_plural = "delegaciones"

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    nombre = models.CharField("nombre", max_length=120, unique=True)
    area = models.CharField("área", max_length=120, blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return self.nombre


class Funcionario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="perfil_sgr",
        verbose_name="usuario",
    )
    nombre = models.CharField("nombre visible", max_length=160)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="funcionarios", verbose_name="cargo")
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.PROTECT,
        related_name="funcionarios",
        verbose_name="delegación",
    )
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "funcionario"
        verbose_name_plural = "funcionarios"

    def __str__(self):
        return self.nombre


class Indicador(models.Model):
    nombre = models.CharField("nombre", max_length=160)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="indicadores", verbose_name="cargo")
    ponderador = models.DecimalField(
        "ponderador (%)",
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
    )
    meta_trimestral = models.PositiveIntegerField("meta trimestral", validators=[MinValueValidator(1)])
    unidad_medida = models.CharField("unidad de medida", max_length=80)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["cargo__nombre", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["cargo", "nombre"], name="uniq_indicador_nombre_cargo"),
            models.CheckConstraint(condition=models.Q(ponderador__gte=0, ponderador__lte=100), name="indicador_ponderador_0_100"),
            models.CheckConstraint(condition=models.Q(meta_trimestral__gte=1), name="indicador_meta_positiva"),
        ]
        verbose_name = "indicador / función"
        verbose_name_plural = "indicadores / funciones"

    def __str__(self):
        return f"{self.nombre} ({self.cargo})"

    @classmethod
    def porcentaje_ponderadores(cls, cargo_id):
        total = cls.objects.filter(cargo_id=cargo_id, activo=True).aggregate(total=Sum("ponderador"))["total"]
        return total if total is not None else Decimal("0.00")

    def aprobadas(self, desde, hasta, usuario=None):
        """Tareas aprobadas que aportan a este indicador en un rango de fechas."""
        from datetime import datetime, time, timedelta

        from django.utils import timezone

        inicio = timezone.make_aware(datetime.combine(desde, time.min))
        fin = timezone.make_aware(datetime.combine(hasta + timedelta(days=1), time.min))
        qs = self.tareas.filter(
            estado="aprobada", validada_en__gte=inicio, validada_en__lt=fin
        )
        if usuario is not None:
            qs = qs.filter(profesional=usuario)
        return qs.count()


class Servicio(models.Model):
    nombre = models.CharField("nombre", max_length=160, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    activo = models.BooleanField("activo", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return self.nombre


class PerfilUsuario(models.Model):
    """Sector (delegación) al que pertenece una cuenta; sirve para asignar profesionales por sector."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_sector",
    )
    sector = models.ForeignKey(
        "Delegacion", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="usuarios_asignados", verbose_name="sector",
    )
    debe_cambiar_clave = models.BooleanField("debe cambiar la contraseña", default=False)

    def __str__(self):
        return f"{self.usuario} · {self.sector or 'sin sector'}"


class MetaIndividual(models.Model):
    """Meta trimestral de un funcionario para un indicador de su cargo."""

    TRIMESTRES = [
        (1, "1.er trimestre (ene-mar)"),
        (2, "2.º trimestre (abr-jun)"),
        (3, "3.er trimestre (jul-sep)"),
        (4, "4.º trimestre (oct-dic)"),
    ]

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.CASCADE,
        related_name="metas_individuales", verbose_name="funcionario",
    )
    indicador = models.ForeignKey(
        Indicador, on_delete=models.PROTECT,
        related_name="metas_individuales", verbose_name="indicador",
    )
    anio = models.PositiveSmallIntegerField(
        "año", validators=[MinValueValidator(2020), MaxValueValidator(2100)],
    )
    trimestre = models.PositiveSmallIntegerField("trimestre", choices=TRIMESTRES)
    meta = models.PositiveIntegerField("meta", validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["-anio", "-trimestre", "funcionario__nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["funcionario", "indicador", "anio", "trimestre"],
                name="uniq_meta_individual_periodo",
            ),
            models.CheckConstraint(
                condition=models.Q(trimestre__gte=1, trimestre__lte=4),
                name="meta_individual_trimestre_1_4",
            ),
            models.CheckConstraint(
                condition=models.Q(meta__gte=1),
                name="meta_individual_meta_positiva",
            ),
        ]
        verbose_name = "meta individual"
        verbose_name_plural = "metas individuales"

    def __str__(self):
        return f"{self.funcionario} · {self.indicador.nombre} · {self.anio} T{self.trimestre}: {self.meta}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.funcionario_id and self.indicador_id:
            if self.funcionario.cargo_id != self.indicador.cargo_id:
                raise ValidationError(
                    {"indicador": "El indicador debe pertenecer al cargo del funcionario."}
                )
