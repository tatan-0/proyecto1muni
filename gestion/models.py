from decimal import Decimal

from django.conf import settings
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

    class Prioridad(models.TextChoices):
        ALTA = "alta", "Alta"
        MEDIA = "media", "Media"
        BAJA = "baja", "Baja"

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    ubicacion = models.CharField("Lugar o sector", max_length=200, blank=True)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)

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
    creada_en = models.DateTimeField(auto_now_add=True)

    cumplida = models.BooleanField(default=False)
    validada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="tareas_validadas",
    )
    validada_en = models.DateTimeField(null=True, blank=True)
    observaciones_revision = models.TextField(blank=True)

    class Meta:
        ordering = ["fecha_limite", "-creada_en"]

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