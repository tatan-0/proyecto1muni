from gestion.permissions import usuario_es_admin


def sgr_roles(request):
    return {"sgr_es_admin": usuario_es_admin(request.user)}
