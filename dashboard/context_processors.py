from .models import PerfilUsuario


def user_es_admin(request):
    if not request.user.is_authenticated:
        return {'user_es_admin': False}

    try:
        perfil = request.user.perfil
        return {'user_es_admin': perfil.es_admin()}
    except PerfilUsuario.DoesNotExist:
        return {'user_es_admin': False}
    except Exception:
        return {'user_es_admin': False}