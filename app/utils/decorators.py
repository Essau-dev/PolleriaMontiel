from functools import wraps
from typing import List, Tuple, Union # Importar para anotaciones de tipo
from flask import abort, flash, redirect, url_for
from flask_login import current_user

# Define un alias de tipo para mayor claridad en la firma de la función
RoleList = Union[List[str], Tuple[str, ...], str]

def role_required(roles: RoleList):
    """
    Decorador personalizado para restringir el acceso a rutas basado en roles de usuario.

    Verifica si el usuario actual está autenticado y si su rol
    está incluido en la lista de roles permitidos.

    :param roles: Una lista, tupla o cadena simple con los códigos de rol permitidos
                  (ej. ['ADMINISTRADOR', 'CAJERO'], ('REPARTIDOR',), 'ADMINISTRADOR').
                  Los códigos deben coincidir con los valores del Enum RolUsuario.
    """
    # Importar RolUsuario dentro de la función para evitar la importación circular
    from app.models import RolUsuario

    # Asegura que 'roles' sea siempre una lista para una verificación consistente
    if not isinstance(roles, (list, tuple)):
        roles = [roles]

    # Convierte los miembros del Enum en la lista de entrada a sus valores string
    # si se pasaron como objetos Enum, para una comparación consistente con current_user.rol
    allowed_roles_values = [r.value if isinstance(r, RolUsuario) else r for r in roles]


    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar si el usuario está autenticado
            if not current_user.is_authenticated:
                flash("Debes iniciar sesión para acceder a esta página.", "warning")
                return redirect(url_for('auth.login')) # Redirigir al login si no autenticado

            # Verificar si el usuario tiene alguno de los roles permitidos
            # Asumimos que current_user.rol es el valor string del Enum cargado desde la BD
            if not hasattr(current_user, 'rol') or current_user.rol not in allowed_roles_values:
                flash("No tienes permiso para acceder a esta página.", "danger")
                # Redirigir al dashboard principal o mostrar un error 403
                return redirect(url_for('main.index')) # Redirigir al dashboard principal
                # Alternativa: abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Puedes añadir más decoradores aquí, por ejemplo:
# - @permission_required (si los permisos son más granulares que solo roles)
# - @log_activity (para registrar acciones importantes)
