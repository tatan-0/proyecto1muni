from decimal import Decimal
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


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
    funciones = models.TextField("funciones y responsabilidades", blank=True)
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


class OrganizacionComunitaria(models.Model):
    class Tipo(models.TextChoices):
        FUNCIONAL = "funcional", "Organización comunitaria funcional"
        ADULTO_MAYOR = "adulto_mayor", "Club de adulto mayor"
        DEPORTIVA = "deportiva", "Organización deportiva"
        CULTURAL_JUVENIL = "cultural_juvenil", "Centro cultural, de madres o agrupación juvenil"
        COMITE = "comite", "Comité vecinal, de allegados o de seguridad"
        SIN_CLASIFICAR = "sin_clasificar", "Sin clasificar"

    nombre = models.CharField("nombre", max_length=160)
    tipo = models.CharField("tipo", max_length=24, choices=Tipo.choices)
    descripcion = models.TextField("descripción", blank=True)
    delegacion = models.ForeignKey(
        Delegacion,
        on_delete=models.PROTECT,
        related_name="organizaciones",
        verbose_name="delegación de referencia",
        null=True,
        blank=True,
    )
    domicilio_legal = models.CharField("domicilio legal", max_length=200, blank=True)
    socios_activos = models.PositiveIntegerField("socios activos", null=True, blank=True)
    fecha_constitucion = models.DateField("fecha de constitución", null=True, blank=True)
    numero_registro_pj = models.CharField("Nº de registro de personalidad jurídica", max_length=40, blank=True)
    fecha_inscripcion_registro = models.DateField("fecha de inscripción en el registro", null=True, blank=True)
    numero_registro_directiva = models.PositiveIntegerField("Nº de registro de directiva", null=True, blank=True)
    observaciones_origen = models.TextField("observaciones de la carga de datos", blank=True)
    activo = models.BooleanField("activa", default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "organización comunitaria"
        verbose_name_plural = "organizaciones comunitarias"
        constraints = [
            models.UniqueConstraint(fields=["nombre", "delegacion"], name="uniq_organizacion_delegacion"),
        ]

    def __str__(self):
        return self.nombre


class Gestion(models.Model):
    class Tipo(models.TextChoices):
        ACTIVIDAD = "actividad", "Actividad"
        SOLICITUD = "solicitud", "Solicitud"
        OTRA = "otra", "Otra gestión"

    class Accion(models.TextChoices):
        REALIZACION = "realizacion", "Acción realizada"
        COORDINACION = "coordinacion", "Coordinación o preparación"

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT, related_name="gestiones", verbose_name="responsable"
    )
    indicador = models.ForeignKey(
        Indicador,
        on_delete=models.PROTECT,
        related_name="gestiones",
        verbose_name="indicador",
        null=True,
        blank=True,
    )
    organizacion = models.ForeignKey(
        OrganizacionComunitaria,
        on_delete=models.PROTECT,
        related_name="gestiones",
        verbose_name="organización comunitaria",
        null=True,
        blank=True,
    )
    tipo = models.CharField("tipo de gestión", max_length=12, choices=Tipo.choices, default=Tipo.ACTIVIDAD)
    accion = models.CharField("tipo de acción", max_length=16, choices=Accion.choices, default=Accion.REALIZACION)
    fecha = models.DateField("fecha de realización")
    titulo = models.CharField("acción realizada", max_length=180)
    descripcion = models.TextField("detalle", blank=True)
    usuario_nombre = models.CharField("nombre del usuario", max_length=160, blank=True)
    usuario_telefono = models.CharField("teléfono del usuario", max_length=40, blank=True)
    usuario_es_delegado = models.BooleanField("el usuario es delegado", default=False)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="gestiones_creadas",
        verbose_name="ingresado por",
    )
    creado_en = models.DateTimeField("fecha de ingreso", auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-creado_en"]
        verbose_name = "gestión"
        verbose_name_plural = "gestiones"

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo} ({self.fecha})"

    @property
    def contabilizable(self):
        return bool(
            self.tipo != self.Tipo.OTRA
            and self.accion == self.Accion.REALIZACION
            and self.indicador_id
            and self.funcionario_id
            and self.indicador.cargo_id == self.funcionario.cargo_id
            and self.usuario_nombre.strip()
            and self.usuario_telefono.strip()
            and not self.usuario_es_delegado
        )

    @staticmethod
    def periodo_semanal_abierto(fecha, hoy=None):
        hoy = hoy or timezone.localdate()
        inicio_semana_actual = hoy - timedelta(days=hoy.weekday())
        inicio_semana_gestion = fecha - timedelta(days=fecha.weekday())
        if fecha.weekday() > 4 or fecha > hoy:
            return False
        if inicio_semana_gestion == inicio_semana_actual:
            return True
        return hoy.weekday() == 0 and inicio_semana_gestion == inicio_semana_actual - timedelta(days=7)


class Ausencia(models.Model):
    class Tipo(models.TextChoices):
        DIA_LIBRE = "dia_libre", "Día libre"
        VACACIONES = "vacaciones", "Vacaciones"
        ADMINISTRATIVO = "administrativo", "Día administrativo"
        LICENCIA = "licencia", "Licencia"

    funcionario = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT, related_name="ausencias", verbose_name="funcionario"
    )
    tipo = models.CharField("tipo de ausencia", max_length=16, choices=Tipo.choices)
    fecha_desde = models.DateField("desde")
    fecha_hasta = models.DateField("hasta")
    observacion = models.CharField("observación", max_length=240, blank=True)
    ingresado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ausencias_ingresadas",
        verbose_name="ingresado por",
    )
    creado_en = models.DateTimeField("fecha de ingreso", auto_now_add=True)

    class Meta:
        ordering = ["-fecha_desde"]
        verbose_name = "ausencia"
        verbose_name_plural = "ausencias"

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.funcionario} ({self.fecha_desde}–{self.fecha_hasta})"

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}
        if self.fecha_desde and self.fecha_hasta and self.fecha_desde > self.fecha_hasta:
            errors["fecha_hasta"] = "La fecha de término debe ser igual o posterior al inicio."
        if self.fecha_desde and self.fecha_hasta and self.fecha_desde.weekday() > 4:
            errors["fecha_desde"] = "Las ausencias deben comenzar en un día hábil."
        if self.fecha_desde and self.fecha_hasta and self.fecha_hasta.weekday() > 4:
            errors["fecha_hasta"] = "Las ausencias deben terminar en un día hábil."
        if self.funcionario_id and self.fecha_desde and self.fecha_hasta:
            overlapping = Ausencia.objects.filter(
                funcionario_id=self.funcionario_id,
                fecha_desde__lte=self.fecha_hasta,
                fecha_hasta__gte=self.fecha_desde,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                errors["fecha_desde"] = "Este período se cruza con otra ausencia del funcionario."
        if errors:
            raise ValidationError(errors)
