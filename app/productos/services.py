# Archivo: PolleriaMontiel\app\productos\services.py

from app import db # Importar la instancia de SQLAlchemy
from app.models import (
    Producto, Subproducto, Modificacion, Precio, TipoCliente,
    producto_modificacion_association, subproducto_modificacion_association,
    Cliente # Necesario para obtener TipoCliente en la lógica de precios
) # Importar los modelos y tablas de asociación
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal # Importar Decimal para cálculos monetarios y cantidades precisas
from datetime import date # Importar date para vigencia de precios
from sqlalchemy.exc import IntegrityError # Para manejar errores de unicidad, FK, etc.
from sqlalchemy import or_, and_ # Para consultas complejas

# --- Funciones de Ayuda Internas ---

def _get_precio_aplicable(
    producto_id: Optional[str] = None,
    subproducto_id: Optional[int] = None,
    cliente_id: Optional[int] = None,
    cantidad_solicitada: Decimal = Decimal('0.0')
) -> Optional[Decimal]:
    """
    Determina el precio unitario (por kg) aplicable para un producto/subproducto
    basado en el tipo de cliente y la cantidad. (Lógica de Sección 4.2)
    Esta función es una copia o versión centralizada de la que estaba en pedidos.services.
    Idealmente, pedidos.services debería llamar a esta función.
    """
    # 1. Obtener el tipo de cliente
    tipo_cliente_value = TipoCliente.PUBLICO.value # Default si no hay cliente
    if cliente_id:
        cliente = Cliente.query.get(cliente_id)
        if cliente:
            tipo_cliente_value = cliente.tipo_cliente.value

    # 2. Consultar precios aplicables
    query = Precio.query.filter(
        Precio.activo == True,
        Precio.tipo_cliente == tipo_cliente_value,
        # Filtrar por producto O subproducto
        or_(
            (Precio.producto_id == producto_id) if producto_id else False,
            (Precio.subproducto_id == subproducto_id) if subproducto_id else False
        ),
        # Filtrar por vigencia (si aplica)
        and_(
            or_(Precio.fecha_inicio_vigencia.is_(None), Precio.fecha_inicio_vigencia <= date.today()),
            or_(Precio.fecha_fin_vigencia.is_(None), Precio.fecha_fin_vigencia >= date.today())
        )
    )

    # 3. Seleccionar el precio más específico por cantidad mínima
    # Ordenar por cantidad_minima_kg descendente para priorizar promociones por volumen
    precios_aplicables = query.order_by(Precio.cantidad_minima_kg.desc()).all()

    # Encontrar el mejor precio que cumpla con la cantidad mínima
    best_price: Optional[Precio] = None
    for precio in precios_aplicables:
        if cantidad_solicitada >= precio.cantidad_minima_kg:
            best_price = precio
            break # Tomamos el primero (el de mayor cantidad_minima_kg <= cantidad_solicitada)

    if best_price:
        return best_price.precio_kg
    else:
        # Si no se encontró ningún precio (ni siquiera el de cantidad_minima_kg = 0),
        # buscar el precio base (cantidad_minima_kg = 0) como fallback
        fallback_query = Precio.query.filter(
            Precio.activo == True,
            Precio.tipo_cliente == tipo_cliente_value,
             or_(
                (Precio.producto_id == producto_id) if producto_id else False,
                (Precio.subproducto_id == subproducto_id) if subproducto_id else False
            ),
            Precio.cantidad_minima_kg == Decimal('0.0') # Buscar el precio base
        )
        fallback_price = fallback_query.first()
        if fallback_price:
             return fallback_price.precio_kg
        else:
             # Si no hay precio base, retornar None o un precio por defecto (ej. 0.0)
             print(f"Advertencia: No se encontró precio para Producto {producto_id} / Subproducto {subproducto_id} para cliente {tipo_cliente_value} y cantidad {cantidad_solicitada}")
             return None # O Decimal('0.0') si se prefiere


# --- Funciones de Servicio para Producto ---

def create_producto(
    id: str, # Código del producto
    nombre: str,
    categoria: str,
    descripcion: Optional[str] = None,
    activo: bool = True
) -> Optional[Producto]:
    """
    Crea un nuevo producto principal.
    """
    try:
        # Validar unicidad de ID y nombre (aunque la restricción de BD es la última defensa)
        existing_prod_id = Producto.query.get(id)
        if existing_prod_id:
            print(f"Error al crear producto: Código '{id}' ya existe.")
            return None
        existing_prod_name = Producto.query.filter_by(nombre=nombre).first()
        if existing_prod_name:
            print(f"Error al crear producto: Nombre '{nombre}' ya existe.")
            return None

        producto = Producto(
            id=id,
            nombre=nombre,
            categoria=categoria,
            descripcion=descripcion,
            activo=activo
        )
        db.session.add(producto)
        db.session.commit()
        return producto
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear producto '{id}': {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear producto '{id}': {e}")
        return None

def get_producto_by_id(producto_id: str) -> Optional[Producto]:
    """Obtiene un producto por su ID (código)."""
    return Producto.query.get(producto_id)

def get_all_productos(page: int = 1, per_page: int = 10, include_inactive: bool = False):
    """Obtiene todos los productos con paginación."""
    query = Producto.query.order_by(Producto.nombre.asc())
    if not include_inactive:
        query = query.filter_by(activo=True)
    return query.paginate(page=page, per_page=per_page, error_out=False)

def search_productos(query: str, page: int = 1, per_page: int = 10):
    """Busca productos por código o nombre."""
    search_term = f"%{query}%"
    query = Producto.query.filter(
        (Producto.id.ilike(search_term)) |
        (Producto.nombre.ilike(search_term))
    ).order_by(Producto.nombre.asc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def update_producto(
    producto_id: str,
    nombre: Optional[str] = None,
    categoria: Optional[str] = None,
    descripcion: Optional[str] = None,
    activo: Optional[bool] = None
) -> Optional[Producto]:
    """
    Actualiza los datos de un producto existente.
    No permite cambiar el ID.
    """
    producto = get_producto_by_id(producto_id)
    if not producto:
        print(f"Error al actualizar producto: Producto con ID '{producto_id}' no encontrado.")
        return None

    try:
        if nombre is not None:
            # Validar unicidad del nombre al actualizar (excluyendo el propio producto)
            existing_prod_name = Producto.query.filter_by(nombre=nombre).filter(Producto.id != producto_id).first()
            if existing_prod_name:
                print(f"Error al actualizar producto '{producto_id}': Nombre '{nombre}' ya existe.")
                return None
            producto.nombre = nombre
        if categoria is not None:
            producto.categoria = categoria
        if descripcion is not None:
            producto.descripcion = descripcion
        if activo is not None:
            producto.activo = activo

        db.session.commit()
        return producto
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar producto '{producto_id}': {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar producto '{producto_id}': {e}")
        return None

def delete_producto(producto_id: str) -> bool:
    """
    Elimina un producto.
    """
    producto = get_producto_by_id(producto_id)
    if not producto:
        print(f"Error al eliminar producto: Producto con ID '{producto_id}' no encontrado.")
        return False

    try:
        # Las cascadas 'all, delete-orphan' en las relaciones (subproductos, precios, items_pedido)
        # deberían manejar la eliminación de registros relacionados automáticamente.
        # Si hay FKs que impiden la eliminación (ej. items de pedidos finalizados),
        # la BD lanzará un error de integridad. Se debe manejar o cambiar la política (ej. desactivar en lugar de borrar).
        db.session.delete(producto)
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al eliminar producto '{producto_id}': No se puede eliminar porque tiene registros asociados (ej. subproductos, precios, ítems de pedido). Considere desactivarlo en su lugar.")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar producto '{producto_id}': {e}")
        return False

def activate_producto(producto_id: str) -> Optional[Producto]:
    """Activa un producto."""
    return update_producto(producto_id, activo=True)

def deactivate_producto(producto_id: str) -> Optional[Producto]:
    """Desactiva un producto."""
    return update_producto(producto_id, activo=False)


# --- Funciones de Servicio para Subproducto ---

def create_subproducto(
    producto_padre_id: str,
    codigo_subprod: str,
    nombre: str,
    descripcion: Optional[str] = None,
    activo: bool = True
) -> Optional[Subproducto]:
    """
    Crea un nuevo subproducto asociado a un producto padre.
    """
    try:
        # Validar que el producto padre exista
        producto_padre = get_producto_by_id(producto_padre_id)
        if not producto_padre:
            print(f"Error al crear subproducto: Producto padre con ID '{producto_padre_id}' no encontrado.")
            return None

        # Validar unicidad de código (aunque la restricción de BD es la última defensa)
        existing_subprod_code = Subproducto.query.filter_by(codigo_subprod=codigo_subprod).first()
        if existing_subprod_code:
            print(f"Error al crear subproducto: Código '{codigo_subprod}' ya existe.")
            return None

        subproducto = Subproducto(
            producto_padre_id=producto_padre_id,
            codigo_subprod=codigo_subprod,
            nombre=nombre,
            descripcion=descripcion,
            activo=activo
        )
        db.session.add(subproducto)
        db.session.commit()
        return subproducto
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear subproducto '{codigo_subprod}': {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear subproducto '{codigo_subprod}': {e}")
        return None

def get_subproducto_by_id(subproducto_id: int) -> Optional[Subproducto]:
    """Obtiene un subproducto por su ID."""
    return Subproducto.query.get(subproducto_id)

def get_all_subproductos(page: int = 1, per_page: int = 10, include_inactive: bool = False):
    """Obtiene todos los subproductos con paginación."""
    query = Subproducto.query.order_by(Subproducto.nombre.asc())
    if not include_inactive:
        query = query.filter_by(activo=True)
    return query.paginate(page=page, per_page=per_page, error_out=False)

def search_subproductos(query: str, page: int = 1, per_page: int = 10):
    """Busca subproductos por código o nombre."""
    search_term = f"%{query}%"
    query = Subproducto.query.filter(
        (Subproducto.codigo_subprod.ilike(search_term)) |
        (Subproducto.nombre.ilike(search_term))
    ).order_by(Subproducto.nombre.asc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def update_subproducto(
    subproducto_id: int,
    producto_padre_id: Optional[str] = None,
    codigo_subprod: Optional[str] = None,
    nombre: Optional[str] = None,
    descripcion: Optional[str] = None,
    activo: Optional[bool] = None
) -> Optional[Subproducto]:
    """
    Actualiza los datos de un subproducto existente.
    """
    subproducto = get_subproducto_by_id(subproducto_id)
    if not subproducto:
        print(f"Error al actualizar subproducto: Subproducto con ID {subproducto_id} no encontrado.")
        return None

    try:
        if producto_padre_id is not None:
            # Validar que el nuevo producto padre exista
            producto_padre = get_producto_by_id(producto_padre_id)
            if not producto_padre:
                print(f"Error al actualizar subproducto {subproducto_id}: Nuevo producto padre con ID '{producto_padre_id}' no encontrado.")
                return None
            subproducto.producto_padre_id = producto_padre_id

        if codigo_subprod is not None:
            # Validar unicidad del código al actualizar (excluyendo el propio subproducto)
            existing_subprod_code = Subproducto.query.filter_by(codigo_subprod=codigo_subprod).filter(Subproducto.id != subproducto_id).first()
            if existing_subprod_code:
                print(f"Error al actualizar subproducto {subproducto_id}: Código '{codigo_subprod}' ya existe.")
                return None
            subproducto.codigo_subprod = codigo_subprod

        if nombre is not None:
            subproducto.nombre = nombre
        if descripcion is not None:
            subproducto.descripcion = descripcion
        if activo is not None:
            subproducto.activo = activo

        db.session.commit()
        return subproducto
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar subproducto {subproducto_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar subproducto {subproducto_id}: {e}")
        return None

def delete_subproducto(subproducto_id: int) -> bool:
    """
    Elimina un subproducto.
    """
    subproducto = get_subproducto_by_id(subproducto_id)
    if not subproducto:
        print(f"Error al eliminar subproducto: Subproducto con ID {subproducto_id} no encontrado.")
        return False

    try:
        # Las cascadas 'all, delete-orphan' en las relaciones (precios, items_pedido)
        # deberían manejar la eliminación de registros relacionados automáticamente.
        # Si hay FKs que impiden la eliminación (ej. items de pedidos finalizados),
        # la BD lanzará un error de integridad. Se debe manejar o cambiar la política (ej. desactivar en lugar de borrar).
        db.session.delete(subproducto)
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al eliminar subproducto {subproducto_id}: No se puede eliminar porque tiene registros asociados (ej. precios, ítems de pedido). Considere desactivarlo en su lugar.")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar subproducto {subproducto_id}: {e}")
        return False

def activate_subproducto(subproducto_id: int) -> Optional[Subproducto]:
    """Activa un subproducto."""
    return update_subproducto(subproducto_id, activo=True)

def deactivate_subproducto(subproducto_id: int) -> Optional[Subproducto]:
    """Desactiva un subproducto."""
    return update_subproducto(subproducto_id, activo=False)


# --- Funciones de Servicio para Modificacion ---

def create_modificacion(
    codigo_modif: str,
    nombre: str,
    descripcion: Optional[str] = None,
    activo: bool = True,
    productos_asociados_ids: Optional[List[str]] = None, # Lista de IDs de Producto
    subproductos_asociados_ids: Optional[List[int]] = None # Lista de IDs de Subproducto
) -> Optional[Modificacion]:
    """
    Crea una nueva modificación y la asocia a productos/subproductos.
    """
    try:
        # Validar unicidad de código (aunque la restricción de BD es la última defensa)
        existing_modif_code = Modificacion.query.filter_by(codigo_modif=codigo_modif).first()
        if existing_modif_code:
            print(f"Error al crear modificación: Código '{codigo_modif}' ya existe.")
            return None

        modificacion = Modificacion(
            codigo_modif=codigo_modif,
            nombre=nombre,
            descripcion=descripcion,
            activo=activo
        )

        # Asociar productos
        if productos_asociados_ids:
            productos = Producto.query.filter(Producto.id.in_(productos_asociados_ids)).all()
            modificacion.productos_asociados.extend(productos)

        # Asociar subproductos
        if subproductos_asociados_ids:
            subproductos = Subproducto.query.filter(Subproducto.id.in_(subproductos_asociados_ids)).all()
            modificacion.subproductos_asociados.extend(subproductos)

        db.session.add(modificacion)
        db.session.commit()
        return modificacion
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear modificación '{codigo_modif}': {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear modificación '{codigo_modif}': {e}")
        return None

def get_modificacion_by_id(modificacion_id: int) -> Optional[Modificacion]:
    """Obtiene una modificación por su ID."""
    return Modificacion.query.get(modificacion_id)

def get_all_modificaciones(page: int = 1, per_page: int = 10, include_inactive: bool = False):
    """Obtiene todas las modificaciones con paginación."""
    query = Modificacion.query.order_by(Modificacion.nombre.asc())
    if not include_inactive:
        query = query.filter_by(activo=True)
    return query.paginate(page=page, per_page=per_page, error_out=False)

def search_modificaciones(query: str, page: int = 1, per_page: int = 10):
    """Busca modificaciones por código o nombre."""
    search_term = f"%{query}%"
    query = Modificacion.query.filter(
        (Modificacion.codigo_modif.ilike(search_term)) |
        (Modificacion.nombre.ilike(search_term))
    ).order_by(Modificacion.nombre.asc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def update_modificacion(
    modificacion_id: int,
    codigo_modif: Optional[str] = None,
    nombre: Optional[str] = None,
    descripcion: Optional[str] = None,
    activo: Optional[bool] = None,
    productos_asociados_ids: Optional[List[str]] = None, # Lista de IDs de Producto (para reemplazar)
    subproductos_asociados_ids: Optional[List[int]] = None # Lista de IDs de Subproducto (para reemplazar)
) -> Optional[Modificacion]:
    """
    Actualiza los datos de una modificación existente y sus asociaciones.
    """
    modificacion = get_modificacion_by_id(modificacion_id)
    if not modificacion:
        print(f"Error al actualizar modificación: Modificación con ID {modificacion_id} no encontrada.")
        return None

    try:
        if codigo_modif is not None:
            # Validar unicidad del código al actualizar (excluyendo la propia modificación)
            existing_modif_code = Modificacion.query.filter_by(codigo_modif=codigo_modif).filter(Modificacion.id != modificacion_id).first()
            if existing_modif_code:
                print(f"Error al actualizar modificación {modificacion_id}: Código '{codigo_modif}' ya existe.")
                return None
            modificacion.codigo_modif = codigo_modif

        if nombre is not None:
            modificacion.nombre = nombre
        if descripcion is not None:
            modificacion.descripcion = descripcion
        if activo is not None:
            modificacion.activo = activo

        # Actualizar asociaciones (reemplazar las existentes)
        if productos_asociados_ids is not None:
            modificacion.productos_asociados = Producto.query.filter(Producto.id.in_(productos_asociados_ids)).all()

        if subproductos_asociados_ids is not None:
            modificacion.subproductos_asociados = Subproducto.query.filter(Subproducto.id.in_(subproductos_asociados_ids)).all()


        db.session.commit()
        return modificacion
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar modificación {modificacion_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar modificación {modificacion_id}: {e}")
        return None

def delete_modificacion(modificacion_id: int) -> bool:
    """
    Elimina una modificación.
    """
    modificacion = get_modificacion_by_id(modificacion_id)
    if not modificacion:
        print(f"Error al eliminar modificación: Modificación con ID {modificacion_id} no encontrada.")
        return False

    try:
        # Las cascadas 'all, delete-orphan' en la relación items_pedido
        # deberían manejar la eliminación de registros relacionados automáticamente.
        # Las asociaciones many-to-many se eliminan automáticamente por SQLAlchemy
        # cuando se elimina el objeto Modificacion si la cascada está configurada correctamente
        # en las relaciones de Modificacion (aunque no se definió cascade en las relaciones many-to-many en models.py,
        # SQLAlchemy por defecto puede manejar la eliminación de las filas de la tabla de asociación).
        # Si hay FKs que impiden la eliminación (ej. items de pedidos finalizados),
        # la BD lanzará un error de integridad. Se debe manejar o cambiar la política (ej. desactivar en lugar de borrar).
        db.session.delete(modificacion)
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al eliminar modificación {modificacion_id}: No se puede eliminar porque tiene registros asociados (ej. ítems de pedido). Considere desactivarla en su lugar.")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar modificación {modificacion_id}: {e}")
        return False

def activate_modificacion(modificacion_id: int) -> Optional[Modificacion]:
    """Activa una modificación."""
    return update_modificacion(modificacion_id, activo=True)

def deactivate_modificacion(modificacion_id: int) -> Optional[Modificacion]:
    """Desactiva una modificación."""
    return update_modificacion(modificacion_id, activo=False)


# --- Funciones de Servicio para Precio ---

def create_precio(
    tipo_cliente_value: str,
    precio_kg: Decimal,
    cantidad_minima_kg: Decimal = Decimal('0.0'),
    etiqueta_promo: Optional[str] = None,
    fecha_inicio_vigencia: Optional[date] = None,
    fecha_fin_vigencia: Optional[date] = None,
    activo: bool = True,
    producto_id: Optional[str] = None, # FK a Producto
    subproducto_id: Optional[int] = None # FK a Subproducto
) -> Optional[Precio]:
    """
    Crea un nuevo registro de precio para un producto O subproducto.
    """
    try:
        # Validar que se especifique UN producto O UN subproducto
        if not ((producto_id is not None and subproducto_id is None) or (producto_id is None and subproducto_id is not None)):
            print("Error al crear precio: Debe especificar un producto O un subproducto, no ambos ni ninguno.")
            return None

        # Validar que el producto/subproducto exista
        if producto_id:
            producto = get_producto_by_id(producto_id)
            if not producto:
                print(f"Error al crear precio: Producto con ID '{producto_id}' no encontrado.")
                return None
        if subproducto_id:
            subproducto = get_subproducto_by_id(subproducto_id)
            if not subproducto:
                print(f"Error al crear precio: Subproducto con ID {subproducto_id} no encontrado.")
                return None

        # Validar unicidad de la combinación (producto/subproducto, tipo_cliente, cantidad_minima_kg)
        # Aunque la restricción de BD es la última defensa
        query = Precio.query.filter_by(
            tipo_cliente=tipo_cliente_value,
            cantidad_minima_kg=cantidad_minima_kg
        )
        if producto_id:
            query = query.filter_by(producto_id=producto_id)
        elif subproducto_id:
            query = query.filter_by(subproducto_id=subproducto_id)

        existing_price = query.first()
        if existing_price:
            print(f"Error al crear precio: Ya existe un precio para esta combinación de producto/subproducto, tipo de cliente y cantidad mínima.")
            return None

        precio = Precio(
            producto_id=producto_id,
            subproducto_id=subproducto_id,
            tipo_cliente=TipoCliente(tipo_cliente_value), # Usar Enum
            precio_kg=precio_kg,
            cantidad_minima_kg=cantidad_minima_kg,
            etiqueta_promo=etiqueta_promo,
            fecha_inicio_vigencia=fecha_inicio_vigencia,
            fecha_fin_vigencia=fecha_fin_vigencia,
            activo=activo
        )
        db.session.add(precio)
        db.session.commit()
        return precio
    except ValueError as e:
        db.session.rollback()
        print(f"Error al crear precio: Valor de Enum no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear precio: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear precio: {e}")
        return None

def get_precio_by_id(precio_id: int) -> Optional[Precio]:
    """Obtiene un registro de precio por su ID."""
    return Precio.query.get(precio_id)

def get_all_precios(page: int = 1, per_page: int = 10, include_inactive: bool = False):
    """Obtiene todos los registros de precios con paginación."""
    query = Precio.query.order_by(Precio.tipo_cliente.asc(), Precio.cantidad_minima_kg.asc())
    if not include_inactive:
        query = query.filter_by(activo=True)
    return query.paginate(page=page, per_page=per_page, error_out=False)

# No se implementa search_precios por query de texto para MVP, se filtra por campos específicos

def update_precio(
    precio_id: int,
    tipo_cliente_value: Optional[str] = None,
    precio_kg: Optional[Decimal] = None,
    cantidad_minima_kg: Optional[Decimal] = None,
    etiqueta_promo: Optional[str] = None,
    fecha_inicio_vigencia: Optional[date] = None,
    fecha_fin_vigencia: Optional[date] = None,
    activo: Optional[bool] = None
    # No se permite cambiar producto_id o subproducto_id después de la creación
) -> Optional[Precio]:
    """
    Actualiza los datos de un registro de precio existente.
    """
    precio = get_precio_by_id(precio_id)
    if not precio:
        print(f"Error al actualizar precio: Precio con ID {precio_id} no encontrado.")
        return None

    try:
        # Validar unicidad de la combinación si cambian tipo_cliente o cantidad_minima_kg
        if tipo_cliente_value is not None or cantidad_minima_kg is not None:
            new_tipo_cliente = tipo_cliente_value if tipo_cliente_value is not None else precio.tipo_cliente.value
            new_cantidad_minima = cantidad_minima_kg if cantidad_minima_kg is not None else precio.cantidad_minima_kg

            query = Precio.query.filter_by(
                tipo_cliente=new_tipo_cliente,
                cantidad_minima_kg=new_cantidad_minima
            ).filter(Precio.id != precio_id) # Excluir el precio actual

            if precio.producto_id:
                query = query.filter_by(producto_id=precio.producto_id)
            elif precio.subproducto_id:
                query = query.filter_by(subproducto_id=precio.subproducto_id)

            existing_price = query.first()
            if existing_price:
                print(f"Error al actualizar precio {precio_id}: Ya existe un precio para esta combinación de producto/subproducto, tipo de cliente y cantidad mínima.")
                return None

        if tipo_cliente_value is not None:
            precio.tipo_cliente = TipoCliente(tipo_cliente_value) # Usar Enum
        if precio_kg is not None:
            precio.precio_kg = precio_kg
        if cantidad_minima_kg is not None:
            precio.cantidad_minima_kg = cantidad_minima_kg
        if etiqueta_promo is not None:
            precio.etiqueta_promo = etiqueta_promo
        if fecha_inicio_vigencia is not None:
            precio.fecha_inicio_vigencia = fecha_inicio_vigencia
        if fecha_fin_vigencia is not None:
            precio.fecha_fin_vigencia = fecha_fin_vigencia
        if activo is not None:
            precio.activo = activo

        db.session.commit()
        return precio
    except ValueError as e:
        db.session.rollback()
        print(f"Error al actualizar precio {precio_id}: Valor de Enum no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar precio {precio_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar precio {precio_id}: {e}")
        return None

def delete_precio(precio_id: int) -> bool:
    """
    Elimina un registro de precio.
    """
    precio = get_precio_by_id(precio_id)
    if not precio:
        print(f"Error al eliminar precio: Precio con ID {precio_id} no encontrado.")
        return False

    try:
        # Si hay ítems de pedido que referencian este precio (aunque no hay FK directa),
        # la eliminación podría causar inconsistencia. Se asume que los ítems de pedido
        # guardan el precio al momento de la venta y no dependen de este registro después.
        db.session.delete(precio)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar precio {precio_id}: {e}")
        return False

def activate_precio(precio_id: int) -> Optional[Precio]:
    """Activa un registro de precio."""
    return update_precio(precio_id, activo=True)

def deactivate_precio(precio_id: int) -> Optional[Precio]:
    """Desactiva un registro de precio."""
    return update_precio(precio_id, activo=False)

# Puedes añadir más funciones de servicio aquí según se necesiten
# Por ejemplo: funciones para obtener modificaciones aplicables a un producto/subproducto específico
# (aunque esto se puede hacer navegando las relaciones del modelo Producto/Subproducto)