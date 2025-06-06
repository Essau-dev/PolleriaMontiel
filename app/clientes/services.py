# Archivo: PolleriaMontiel\app\clientes\services.py

from app import db # Importar la instancia de SQLAlchemy
from app.models import Cliente, TipoCliente, Telefono, TipoTelefono, Direccion, TipoDireccion # Importar los modelos y Enums necesarios
from typing import Optional, List, Dict, Any # Para type hints
from datetime import datetime # Para fechas de registro
from sqlalchemy.exc import IntegrityError # Para manejar errores de unicidad, FK, etc.
from decimal import Decimal # Importar Decimal para tipos de datos precisos

# --- Funciones de Servicio para Cliente ---

def create_client(
    nombre: str,
    apellidos: Optional[str] = None,
    alias: Optional[str] = None,
    tipo_cliente_value: str = TipoCliente.PUBLICO.value, # Valor del Enum TipoCliente
    notas_cliente: Optional[str] = None,
    activo: bool = True
) -> Optional[Cliente]:
    """
    Crea un nuevo cliente en la base de datos.

    Args:
        nombre: Nombre(s) del cliente.
        apellidos: Apellidos del cliente (opcional).
        alias: Alias o apodo (opcional).
        tipo_cliente_value: Valor del tipo de cliente (ej. 'PUBLICO').
        notas_cliente: Notas adicionales sobre el cliente (opcional).
        activo: Estado de actividad del cliente.

    Returns:
        El objeto Cliente creado si tiene éxito, None si hay un error (ej. alias duplicado si se valida).
    """
    try:
        # Validar que el tipo de cliente sea válido
        tipo_cliente_enum = TipoCliente(tipo_cliente_value)

        # Opcional: Validar unicidad del alias si es una regla de negocio estricta
        # Descomentar la validación de unicidad del alias
        if alias:
            existing_client_with_alias = Cliente.query.filter_by(alias=alias).first()
            if existing_client_with_alias:
                print(f"Error al crear cliente: Alias '{alias}' ya existe.")
                return None # Retorna None si el alias ya existe


        client = Cliente(
            nombre=nombre,
            apellidos=apellidos,
            alias=alias,
            tipo_cliente=tipo_cliente_enum,
            notas_cliente=notas_cliente,
            activo=activo,
            fecha_registro=datetime.utcnow()
        )

        db.session.add(client)
        db.session.commit()
        return client

    except ValueError:
        db.session.rollback()
        print(f"Error al crear cliente: Tipo de cliente '{tipo_cliente_value}' no válido.")
        return None
    except IntegrityError as e:
        db.session.rollback()
        # Manejar errores específicos de integridad si es necesario (ej. alias único)
        # Aunque ya validamos arriba, la restricción de BD es la última defensa
        print(f"Error de integridad al crear cliente: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear cliente: {e}")
        return None

def get_client_by_id(client_id: int) -> Optional[Cliente]:
    """Busca un cliente por su ID."""
    return Cliente.query.get(client_id)

def get_all_clients(page: int = 1, per_page: int = 10):
    """Obtiene todos los clientes activos con paginación."""
    # Podrías añadir filtros (ej. solo activos) o ordenación aquí
    return Cliente.query.filter_by(activo=True).order_by(Cliente.nombre.asc(), Cliente.apellidos.asc()).paginate(page=page, per_page=per_page, error_out=False)

def search_clients(query: str, page: int = 1, per_page: int = 10):
    """
    Busca clientes por nombre, apellidos, alias o número de teléfono.
    Para MVP, una búsqueda simple que cubra los campos principales.
    """
    # La búsqueda por teléfono requiere un join con la tabla Telefono
    # Usamos ilike para búsqueda insensible a mayúsculas/minúsculas
    search_term = f"%{query}%"

    # Buscar en Cliente (nombre, apellidos, alias)
    clients_by_details = Cliente.query.filter(
        (Cliente.nombre.ilike(search_term)) |
        (Cliente.apellidos.ilike(search_term)) |
        (Cliente.alias.ilike(search_term))
    )

    # Buscar en Telefono y obtener los clientes correspondientes
    clients_by_phone = Cliente.query.join(Cliente.telefonos).filter(
        Telefono.numero_telefono.ilike(search_term)
    )

    # Combinar resultados y eliminar duplicados
    # Para paginación, es más eficiente hacer la combinación y luego paginar
    # O paginar cada query y combinar los resultados (más complejo)
    # Para MVP, combinamos y luego paginamos (puede ser menos eficiente con muchos resultados)
    combined_query = clients_by_details.union(clients_by_phone)

    # Filtrar por clientes activos si es necesario
    combined_query = combined_query.filter(Cliente.activo == True)

    # Aplicar paginación
    pagination = combined_query.order_by(Cliente.nombre.asc(), Cliente.apellidos.asc()).paginate(page=page, per_page=per_page, error_out=False)

    return pagination


def update_client(
    client_id: int,
    nombre: Optional[str] = None,
    apellidos: Optional[str] = None,
    alias: Optional[str] = None,
    tipo_cliente_value: Optional[str] = None,
    notas_cliente: Optional[str] = None,
    activo: Optional[bool] = None
) -> Optional[Cliente]:
    """
    Actualiza los datos de un cliente existente.

    Args:
        client_id: ID del cliente a actualizar.
        ... (otros campos opcionales para actualizar)

    Returns:
        El objeto Cliente actualizado si tiene éxito, None si el cliente no existe o hay un error.
    """
    client = get_client_by_id(client_id)
    if not client:
        print(f"Error al actualizar cliente: Cliente con ID {client_id} no encontrado.")
        return None

    try:
        if nombre is not None:
            client.nombre = nombre
        if apellidos is not None:
            client.apellidos = apellidos
        if alias is not None:
            # Descomentar la validación de unicidad del alias al actualizar
            existing_client_with_alias = Cliente.query.filter_by(alias=alias).first()
            if existing_client_with_alias and existing_client_with_alias.id != client.id:
                print(f"Error al actualizar cliente: Alias '{alias}' ya existe.")
                return None # Retorna None si el alias ya existe para otro cliente
            client.alias = alias
        if tipo_cliente_value is not None:
            client.tipo_cliente = TipoCliente(tipo_cliente_value)
        if notas_cliente is not None:
            client.notas_cliente = notas_cliente
        if activo is not None:
            client.activo = activo

        db.session.commit()
        return client

    except ValueError:
        db.session.rollback()
        print(f"Error al actualizar cliente {client_id}: Tipo de cliente '{tipo_cliente_value}' no válido.")
        return None
    except IntegrityError as e:
        db.session.rollback()
        # Aunque ya validamos arriba, la restricción de BD es la última defensa
        print(f"Error de integridad al actualizar cliente {client_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar cliente {client_id}: {e}")
        return None

def delete_client(client_id: int) -> bool:
    """
    Elimina un cliente de la base de datos.

    Args:
        client_id: ID del cliente a eliminar.

    Returns:
        True si el cliente fue eliminado, False si no se encontró o hubo un error.
    """
    client = get_client_by_id(client_id)
    if not client:
        print(f"Error al eliminar cliente: Cliente con ID {client_id} no encontrado.")
        return False

    try:
        # La cascada 'all, delete-orphan' en las relaciones de Cliente
        # (telefonos, direcciones, pedidos) debería manejar la eliminación
        # de registros relacionados automáticamente por SQLAlchemy.
        # Si hay FKs que impiden la eliminación (ej. pedidos asociados que no se deben borrar),
        # la BD lanzará un error de integridad. Se debe manejar o cambiar la política (ej. desactivar en lugar de borrar).
        db.session.delete(client)
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al eliminar cliente {client_id}: No se puede eliminar porque tiene registros asociados (ej. pedidos). Considere desactivarlo en su lugar.")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar cliente {client_id}: {e}")
        return False

def deactivate_client(client_id: int) -> Optional[Cliente]:
    """Desactiva un cliente."""
    return update_client(client_id, activo=False)

def activate_client(client_id: int) -> Optional[Cliente]:
    """Activa un cliente."""
    return update_client(client_id, activo=True)


# --- Funciones de Servicio para Teléfono ---

def create_phone_for_client(
    client_id: int,
    numero_telefono: str,
    tipo_telefono_value: str = TipoTelefono.CELULAR.value,
    es_principal: bool = False
) -> Optional[Telefono]:
    """
    Crea un nuevo número de teléfono para un cliente.

    Args:
        client_id: ID del cliente.
        numero_telefono: Número de teléfono.
        tipo_telefono_value: Valor del tipo de teléfono.
        es_principal: Si debe marcarse como principal.

    Returns:
        El objeto Telefono creado si tiene éxito, None si hay un error.
    """
    client = get_client_by_id(client_id)
    if not client:
        print(f"Error al crear teléfono: Cliente con ID {client_id} no encontrado.")
        return None

    try:
        # Validar que el tipo de teléfono sea válido
        tipo_telefono_enum = TipoTelefono(tipo_telefono_value)

        # Validar unicidad del número de teléfono para este cliente
        existing_phone = Telefono.query.filter_by(
            cliente_id=client_id,
            numero_telefono=numero_telefono
        ).first()
        if existing_phone:
            print(f"Error al crear teléfono: El número '{numero_telefono}' ya existe para el cliente {client_id}.")
            return None # O lanzar una excepción

        # Si se marca como principal, desactivar otros teléfonos principales del cliente
        if es_principal:
            set_principal_phone(client_id, None) # Desactivar el actual principal

        phone = Telefono(
            cliente_id=client_id,
            numero_telefono=numero_telefono,
            tipo_telefono=tipo_telefono_enum,
            es_principal=es_principal
        )

        db.session.add(phone)
        db.session.commit()
        return phone

    except ValueError:
        db.session.rollback()
        print(f"Error al crear teléfono: Tipo de teléfono '{tipo_telefono_value}' no válido.")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear teléfono para cliente {client_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear teléfono para cliente {client_id}: {e}")
        return None

def get_phone_by_id(phone_id: int) -> Optional[Telefono]:
    """Busca un teléfono por su ID."""
    return Telefono.query.get(phone_id)

def update_phone(
    phone_id: int,
    numero_telefono: Optional[str] = None,
    tipo_telefono_value: Optional[str] = None,
    es_principal: Optional[bool] = None
) -> Optional[Telefono]:
    """
    Actualiza los datos de un número de teléfono existente.

    Args:
        phone_id: ID del teléfono a actualizar.
        ... (otros campos opcionales para actualizar)

    Returns:
        El objeto Telefono actualizado si tiene éxito, None si el teléfono no existe o hay un error.
    """
    phone = get_phone_by_id(phone_id)
    if not phone:
        print(f"Error al actualizar teléfono: Teléfono con ID {phone_id} no encontrado.")
        return None

    try:
        if numero_telefono is not None:
            # Validar unicidad del número de teléfono para este cliente (excluyendo el propio teléfono)
            existing_phone = Telefono.query.filter_by(
                cliente_id=phone.cliente_id,
                numero_telefono=numero_telefono
            ).filter(Telefono.id != phone_id).first()
            if existing_phone:
                print(f"Error al actualizar teléfono: El número '{numero_telefono}' ya existe para el cliente {phone.cliente_id}.")
                return None # O lanzar una excepción
            phone.numero_telefono = numero_telefono

        if tipo_telefono_value is not None:
            phone.tipo_telefono = TipoTelefono(tipo_telefono_value)

        if es_principal is not None:
            # Si se marca como principal, desactivar otros teléfonos principales del cliente
            if es_principal:
                set_principal_phone(phone.cliente_id, phone_id)
            else:
                # Si se desmarca como principal, solo actualizar este teléfono
                phone.es_principal = False

        db.session.commit()
        return phone

    except ValueError:
        db.session.rollback()
        print(f"Error al actualizar teléfono {phone_id}: Tipo de teléfono '{tipo_telefono_value}' no válido.")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar teléfono {phone_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar teléfono {phone_id}: {e}")
        return None

def delete_phone(phone_id: int) -> bool:
    """
    Elimina un número de teléfono.

    Args:
        phone_id: ID del teléfono a eliminar.

    Returns:
        True si el teléfono fue eliminado, False si no se encontró o hubo un error.
    """
    phone = get_phone_by_id(phone_id)
    if not phone:
        print(f"Error al eliminar teléfono: Teléfono con ID {phone_id} no encontrado.")
        return False

    try:
        db.session.delete(phone)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar teléfono {phone_id}: {e}")
        return False

def set_principal_phone(client_id: int, phone_id: Optional[int]) -> bool:
    """
    Establece un teléfono como principal para un cliente, asegurando que solo uno lo sea.

    Args:
        client_id: ID del cliente.
        phone_id: ID del teléfono a marcar como principal, o None para desmarcar todos.

    Returns:
        True si la operación fue exitosa, False si hay un error o el teléfono no pertenece al cliente.
    """
    try:
        # Desmarcar todos los teléfonos principales actuales para este cliente
        Telefono.query.filter_by(cliente_id=client_id, es_principal=True).update({Telefono.es_principal: False})
        db.session.flush() # Aplicar el update antes de buscar el nuevo principal

        if phone_id is not None:
            # Buscar el teléfono a marcar como principal
            phone_to_set_principal = Telefono.query.filter_by(
                id=phone_id,
                cliente_id=client_id # Asegurar que el teléfono pertenece al cliente
            ).first()

            if not phone_to_set_principal:
                print(f"Error al establecer teléfono principal: Teléfono con ID {phone_id} no encontrado o no pertenece al cliente {client_id}.")
                db.session.rollback()
                return False

            # Marcar el teléfono seleccionado como principal
            phone_to_set_principal.es_principal = True

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al establecer teléfono principal para cliente {client_id}: {e}")
        return False


# --- Funciones de Servicio para Dirección ---

def create_address_for_client(
    client_id: int,
    calle_numero: str,
    ciudad: str,
    colonia: Optional[str] = None,
    codigo_postal: Optional[str] = None,
    referencias: Optional[str] = None,
    tipo_direccion_value: str = TipoDireccion.CASA.value,
    latitud: Optional[Decimal] = None,
    longitud: Optional[Decimal] = None,
    es_principal: bool = False
) -> Optional[Direccion]:
    """
    Crea una nueva dirección para un cliente.

    Args:
        client_id: ID del cliente.
        ... (otros campos)

    Returns:
        El objeto Direccion creado si tiene éxito, None si hay un error.
    """
    client = get_client_by_id(client_id)
    if not client:
        print(f"Error al crear dirección: Cliente con ID {client_id} no encontrado.")
        return None

    try:
        # Validar que el tipo de dirección sea válido
        tipo_direccion_enum = TipoDireccion(tipo_direccion_value)

        # Si se marca como principal, desactivar otras direcciones principales del cliente
        if es_principal:
            set_principal_address(client_id, None) # Desactivar la actual principal

        address = Direccion(
            cliente_id=client_id,
            calle_numero=calle_numero,
            colonia=colonia,
            ciudad=ciudad,
            codigo_postal=codigo_postal,
            referencias=referencias,
            tipo_direccion=tipo_direccion_enum,
            latitud=latitud,
            longitud=longitud,
            es_principal=es_principal
        )

        db.session.add(address)
        db.session.commit()
        return address

    except ValueError:
        db.session.rollback()
        print(f"Error al crear dirección: Tipo de dirección '{tipo_direccion_value}' no válido.")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear dirección para cliente {client_id}: {e}")
        return None

def get_address_by_id(address_id: int) -> Optional[Direccion]:
    """Busca una dirección por su ID."""
    return Direccion.query.get(address_id)

def update_address(
    address_id: int,
    calle_numero: Optional[str] = None,
    ciudad: Optional[str] = None,
    colonia: Optional[str] = None,
    codigo_postal: Optional[str] = None,
    referencias: Optional[str] = None,
    tipo_direccion_value: Optional[str] = None,
    latitud: Optional[Decimal] = None,
    longitud: Optional[Decimal] = None,
    es_principal: Optional[bool] = None
) -> Optional[Direccion]:
    """
    Actualiza los datos de una dirección existente.

    Args:
        address_id: ID de la dirección a actualizar.
        ... (otros campos opcionales para actualizar)

    Returns:
        El objeto Direccion actualizado si tiene éxito, None si la dirección no existe o hay un error.
    """
    address = get_address_by_id(address_id)
    if not address:
        print(f"Error al actualizar dirección: Dirección con ID {address_id} no encontrada.")
        return None

    try:
        if calle_numero is not None:
            address.calle_numero = calle_numero
        if colonia is not None:
            address.colonia = colonia
        if ciudad is not None:
            address.ciudad = ciudad
        if codigo_postal is not None:
            address.codigo_postal = codigo_postal
        if referencias is not None:
            address.referencias = referencias
        if tipo_direccion_value is not None:
            address.tipo_direccion = TipoDireccion(tipo_direccion_value)
        if latitud is not None:
            address.latitud = latitud
        if longitud is not None:
            address.longitud = longitud

        if es_principal is not None:
            # Si se marca como principal, desactivar otras direcciones principales del cliente
            if es_principal:
                set_principal_address(address.cliente_id, address_id)
            else:
                # Si se desmarca como principal, solo actualizar esta dirección
                address.es_principal = False

        db.session.commit()
        return address

    except ValueError:
        db.session.rollback()
        print(f"Error al actualizar dirección {address_id}: Tipo de dirección '{tipo_direccion_value}' no válido.")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar dirección {address_id}: {e}")
        return None

def delete_address(address_id: int) -> bool:
    """
    Elimina una dirección.

    Args:
        address_id: ID de la dirección a eliminar.

    Returns:
        True si la dirección fue eliminada, False si no se encontró o hubo un error.
    """
    address = get_address_by_id(address_id)
    if not address:
        print(f"Error al eliminar dirección: Dirección con ID {address_id} no encontrada.")
        return False

    try:
        db.session.delete(address)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar dirección {address_id}: {e}")
        return False

def set_principal_address(client_id: int, address_id: Optional[int]) -> bool:
    """
    Establece una dirección como principal para un cliente, asegurando que solo una lo sea.

    Args:
        client_id: ID del cliente.
        address_id: ID de la dirección a marcar como principal, o None para desmarcar todas.

    Returns:
        True si la operación fue exitosa, False si hay un error o la dirección no pertenece al cliente.
    """
    try:
        # Desmarcar todas las direcciones principales actuales para este cliente
        Direccion.query.filter_by(cliente_id=client_id, es_principal=True).update({Direccion.es_principal: False})
        db.session.flush() # Aplicar el update antes de buscar la nueva principal

        if address_id is not None:
            # Buscar la dirección a marcar como principal
            address_to_set_principal = Direccion.query.filter_by(
                id=address_id,
                cliente_id=client_id # Asegurar que la dirección pertenece al cliente
            ).first()

            if not address_to_set_principal:
                print(f"Error al establecer dirección principal: Dirección con ID {address_id} no encontrada o no pertenece al cliente {client_id}.")
                db.session.rollback()
                return False

            # Marcar la dirección seleccionada como principal
            address_to_set_principal.es_principal = True

        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al establecer dirección principal para cliente {client_id}: {e}")
        return False

# Puedes añadir más funciones de servicio aquí según se necesiten
# Por ejemplo: get_principal_phone, get_principal_address (aunque estos pueden ser métodos del modelo Cliente)
# get_phones_for_client, get_addresses_for_client (aunque las relaciones en el modelo Cliente ya permiten esto)