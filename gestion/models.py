from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum


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
