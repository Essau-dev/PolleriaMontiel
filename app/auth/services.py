# Archivo: PolleriaMontiel\app\auth\services.py

from app import db # Importar la instancia de SQLAlchemy
from app.models import Usuario, RolUsuario # Importar los modelos necesarios
from werkzeug.security import generate_password_hash # Importar para hashear contraseñas
from typing import Optional # Para type hints

def create_user(username: str, password: str, nombre_completo: str, rol: str, activo: bool = True) -> Optional[Usuario]:
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        username: Nombre de usuario único.
        password: Contraseña en texto plano.
        nombre_completo: Nombre completo del usuario.
        rol: Rol del usuario (valor del Enum RolUsuario).
        activo: Estado de actividad del usuario.

    Returns:
        El objeto Usuario creado si tiene éxito, None si el username ya existe.
    """
    # Verificar si el usuario ya existe (validación a nivel de servicio)
    existing_user = Usuario.query.filter_by(username=username).first()
    if existing_user:
        return None # O lanzar una excepción específica

    try:
        # Crear la instancia del usuario
        user = Usuario(
            username=username,
            nombre_completo=nombre_completo,
            # Asegurarse de que el rol es un miembro válido del Enum
            rol=RolUsuario(rol),
            activo=activo
        )
        # Establecer la contraseña hasheada
        user.set_password(password)

        # Añadir a la sesión y guardar en la base de datos
        db.session.add(user)
        db.session.commit()

        return user

    except ValueError:
        # Manejar el caso si el rol proporcionado no es válido para el Enum
        db.session.rollback() # Deshacer cualquier cambio pendiente
        print(f"Error al crear usuario: Rol '{rol}' no válido.") # Loggear el error
        return None
    except Exception as e:
        # Manejar otros posibles errores de base de datos
        db.session.rollback()
        print(f"Error inesperado al crear usuario: {e}") # Loggear el error
        return None


def get_user_by_username(username: str) -> Optional[Usuario]:
    """Busca un usuario por su nombre de usuario."""
    return Usuario.query.filter_by(username=username).first()

def get_user_by_id(user_id: int) -> Optional[Usuario]:
    """Carga un usuario dado su ID."""
    return Usuario.query.get(user_id)

def get_all_users(page: int = 1, per_page: int = 10):
    """Obtiene todos los usuarios con paginación."""
    return Usuario.query.order_by(Usuario.nombre_completo.asc()).paginate(page=page, per_page=per_page, error_out=False)

def update_user(user_id: int, nombre_completo: Optional[str] = None, rol: Optional[str] = None, activo: Optional[bool] = None) -> Optional[Usuario]:
    """
    Actualiza los datos de un usuario existente.

    Args:
        user_id: ID del usuario a actualizar.
        nombre_completo: Nuevo nombre completo (opcional).
        rol: Nuevo rol (valor del Enum RolUsuario, opcional).
        activo: Nuevo estado de actividad (opcional).

    Returns:
        El objeto Usuario actualizado si tiene éxito, None si el usuario no existe o hay un error.
    """
    user = get_user_by_id(user_id)
    if not user:
        return None

    try:
        if nombre_completo is not None:
            user.nombre_completo = nombre_completo
        if rol is not None:
            # Validar y asignar el nuevo rol
            user.rol = RolUsuario(rol)
        if activo is not None:
            user.activo = activo

        db.session.commit()
        return user

    except ValueError:
        # Manejar el caso si el rol proporcionado no es válido para el Enum
        db.session.rollback()
        print(f"Error al actualizar usuario {user_id}: Rol '{rol}' no válido.")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar usuario {user_id}: {e}")
        return None

def delete_user(user_id: int) -> bool:
    """
    Elimina un usuario de la base de datos.

    Args:
        user_id: ID del usuario a eliminar.

    Returns:
        True si el usuario fue eliminado, False si no se encontró o hubo un error.
    """
    user = get_user_by_id(user_id)
    if not user:
        return False

    try:
        # Considerar restricciones de FK antes de eliminar (ej. si tiene pedidos asociados)
        # Para MVP, podemos permitir la eliminación simple si la BD lo permite (ON DELETE SET NULL/CASCADE)
        # O añadir lógica para verificar si se puede eliminar
        db.session.delete(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar usuario {user_id}: {e}")
        return False

def reset_password(user_id: int, new_password: str) -> Optional[Usuario]:
    """
    Resetea la contraseña de un usuario.

    Args:
        user_id: ID del usuario.
        new_password: La nueva contraseña en texto plano.

    Returns:
        El objeto Usuario actualizado si tiene éxito, None si el usuario no existe o hay un error.
    """
    user = get_user_by_id(user_id)
    if not user:
        return None

    try:
        user.set_password(new_password)
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        print(f"Error al resetear contraseña para usuario {user_id}: {e}")
        return None

def deactivate_user(user_id: int) -> Optional[Usuario]:
    """Desactiva un usuario."""
    return update_user(user_id, activo=False)

def activate_user(user_id: int) -> Optional[Usuario]:
    """Activa un usuario."""
    return update_user(user_id, activo=True)

# Puedes añadir más funciones de servicio aquí según se necesiten
# Por ejemplo: get_users_by_role, search_users, etc.