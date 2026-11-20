from gestion.permissions import roles_de, usuario_es_admin


def sgr_roles(request):
    return {"sgr_es_admin": usuario_es_admin(request.user), "sgr_roles": roles_de(request.user)}
