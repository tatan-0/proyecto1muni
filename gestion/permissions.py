from gestion.models import Funcionario


def usuario_es_admin(user):
    return bool(
        user.is_authenticated
        and (user.is_superuser or user.groups.filter(name="ADMINISTRADOR").exists())
    )


def usuario_tiene_acceso_sgr(user):
    if not user.is_authenticated:
        return False
    return usuario_es_admin(user) or user.groups.filter(name__in=("DELEGADO", "FUNCIONARIO")).exists()


def funcionarios_visibles(user):
    funcionarios = Funcionario.objects.select_related("usuario", "cargo", "delegacion")
    if not user.is_authenticated:
        return funcionarios.none()
    if usuario_es_admin(user):
        return funcionarios
    if user.groups.filter(name="DELEGADO").exists():
        try:
            delegacion_id = user.perfil_sgr.delegacion_id
        except Funcionario.DoesNotExist:
            return funcionarios.none()
        return funcionarios.filter(delegacion_id=delegacion_id)
    if user.groups.filter(name="FUNCIONARIO").exists():
        return funcionarios.filter(usuario_id=user.pk)
    return funcionarios.none()
