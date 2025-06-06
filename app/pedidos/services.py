# Archivo: PolleriaMontiel\app\pedidos\services.py

from app import db # Importar la instancia de SQLAlchemy
from app.models import (
    Pedido, PedidoItem, ProductoAdicional, Cliente, Direccion, Usuario,
    Producto, Subproducto, Modificacion, Precio, Telefono, ConfiguracionSistema,
    MovimientoCaja, # Añadir MovimientoCaja aquí
    TipoVenta, FormaPago, EstadoPedido, TipoMovimientoCaja, RolUsuario, TipoCliente
) # Importar los modelos y Enums necesarios
from app.caja.services import registrar_movimiento_caja, calcular_y_sugerir_cambio_con_denominaciones, registrar_egreso_compra_pa, registrar_ingreso_liquidacion_repartidor # Importar servicios de caja
from app.utils.helpers import format_pedido_folio # Importar helpers
from decimal import Decimal # Importar Decimal para cálculos monetarios precisos
from datetime import datetime, date # Importar datetime y date
from typing import Optional, List, Dict, Any, Tuple, Union
from sqlalchemy.exc import IntegrityError # Para manejar errores de BD
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


def _get_item_description(
    producto_id: Optional[str] = None,
    subproducto_id: Optional[int] = None,
    modificacion_id: Optional[int] = None
) -> str:
    """
    Genera la descripción textual de un PedidoItem. (Lógica de Sección 4.1)
    """
    parts = []
    target_name = "Producto Desconocido"

    if subproducto_id:
        subproducto = Subproducto.query.get(subproducto_id)
        if subproducto:
            target_name = subproducto.nombre
            # Opcional: Añadir nombre del producto padre si es relevante
            # if subproducto.producto_padre:
            #     target_name = f"{subproducto.nombre} ({subproducto.producto_padre.nombre})"
    elif producto_id:
        producto = Producto.query.get(producto_id)
        if producto:
            target_name = producto.nombre

    parts.append(target_name)

    if modificacion_id:
        modificacion = Modificacion.query.get(modificacion_id)
        if modificacion:
            parts.append(modificacion.nombre)

    return ", ".join(parts)


def _recalculate_pedido_totals(pedido: Pedido):
    """
    Recalcula los subtotales y el total general de un pedido. (Lógica de Sección 4.1)
    Actualiza el objeto Pedido en memoria.
    """
    # Asegurarse de que las relaciones estén cargadas si se usa lazy='dynamic' y no se han accedido antes
    # O usar .all() si se necesita la lista completa para sumar
    items = pedido.items.all()
    productos_adicionales = pedido.productos_adicionales_pedido.all()

    pedido.subtotal_productos_pollo = sum(item.subtotal_item for item in items)
    pedido.subtotal_productos_adicionales = sum(pa.subtotal_pa for pa in productos_adicionales)

    # Asegurar que costo_envio y descuento_aplicado no sean None
    costo_envio = pedido.costo_envio if pedido.costo_envio is not None else Decimal('0.0')
    descuento = pedido.descuento_aplicado if pedido.descuento_aplicado is not None else Decimal('0.0')

    pedido.total_pedido = (pedido.subtotal_productos_pollo + pedido.subtotal_productos_adicionales + costo_envio) - descuento
    # Asegurar precisión Decimal
    pedido.total_pedido = round(pedido.total_pedido, 2)


# --- Funciones de Servicio Principales para Pedidos ---

def create_pedido(
    usuario_id: int, # Cajero o Admin que crea el pedido
    tipo_venta_value: str, # Valor del Enum TipoVenta
    cliente_id: Optional[int] = None, # Opcional para mostrador genérico
    direccion_entrega_id: Optional[int] = None, # Requerido para domicilio con cliente
    repartidor_id: Optional[int] = None, # Opcional, se puede asignar después
    forma_pago_value: Optional[str] = None, # Opcional, ej. para pago contra entrega
    notas_pedido: Optional[str] = None,
    fecha_entrega_programada: Optional[datetime] = None,
    requiere_factura: bool = False
) -> Optional[Pedido]:
    """
    Crea un nuevo registro de pedido inicial.
    """
    try:
        # Validar Enums
        tipo_venta_enum = TipoVenta(tipo_venta_value)
        forma_pago_enum = FormaPago(forma_pago_value) if forma_pago_value else None

        # Validar cliente y dirección para domicilio
        if tipo_venta_enum == TipoVenta.DOMICILIO:
            if not cliente_id:
                print("Error al crear pedido: Cliente es requerido para pedidos a domicilio.")
                return None
            if not direccion_entrega_id:
                 print("Error al crear pedido: Dirección de entrega es requerida para pedidos a domicilio.")
                 return None
            # Opcional: Validar que cliente y direccion_entrega_id existan y estén asociados
            cliente = Cliente.query.get(cliente_id)
            direccion = Direccion.query.get(direccion_entrega_id)
            if not cliente or not direccion or direccion.cliente_id != cliente.id:
                 print("Error al crear pedido: Cliente o dirección de entrega no válidos o no asociados.")
                 return None

        # Validar repartidor si se asigna inicialmente
        if repartidor_id:
            repartidor = Usuario.query.get(repartidor_id)
            if not repartidor or not repartidor.is_repartidor():
                 print("Error al crear pedido: Repartidor asignado no válido.")
                 return None

        # Determinar estado inicial basado en tipo de venta y si requiere confirmación
        # Para MVP, asumimos PENDIENTE_PREPARACION si es mostrador o domicilio con cliente/dirección
        # PENDIENTE_CONFIRMACION podría usarse si el flujo lo requiere (ej. pedido por WhatsApp sin confirmar)
        initial_estado = EstadoPedido.PENDIENTE_PREPARACION

        # Generar folio (usando el helper, aunque el modelo también tiene un método)
        # El helper usa el ID, que solo está disponible después de db.session.add + db.session.flush()
        # O se podría generar un folio secuencial antes de guardar si se usa un campo dedicado en el modelo

        pedido = Pedido(
            cliente_id=cliente_id,
            usuario_id=usuario_id,
            repartidor_id=repartidor_id,
            direccion_entrega_id=direccion_entrega_id,
            tipo_venta=tipo_venta_enum,
            forma_pago=forma_pago_enum,
            notas_pedido=notas_pedido,
            fecha_entrega_programada=fecha_entrega_programada,
            requiere_factura=requiere_factura,
            estado_pedido=initial_estado,
            # Los totales se inicializan en 0 por defecto en el modelo
            # paga_con y cambio_entregado son NULL inicialmente
        )

        db.session.add(pedido)
        db.session.commit() # Commit para obtener el ID y poder añadir items/PAs

        # Opcional: Actualizar el campo de folio consecutivo en ConfiguracionSistema si se usa
        # config = ConfiguracionSistema.query.get(1)
        # if config:
        #     config.ultimo_folio_pedido = pedido.id # O un campo de folio separado
        #     db.session.commit()


        return pedido

    except ValueError as e:
        db.session.rollback()
        print(f"Error al crear pedido: Valor de Enum no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al crear pedido: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al crear pedido: {e}")
        return None

def get_pedido_by_id(pedido_id: int) -> Optional[Pedido]:
    """Obtiene un pedido por su ID."""
    # Usar .options(db.joinedload(...)) si necesitas cargar relaciones eager
    return Pedido.query.get(pedido_id)

def get_all_pedidos(page: int = 1, per_page: int = 10, filters: Optional[Dict[str, Any]] = None):
    """
    Obtiene todos los pedidos con paginación y filtros opcionales.
    Filtros pueden incluir: estado, tipo_venta, fecha_desde, fecha_hasta, cliente_id, repartidor_id.
    """
    query = Pedido.query.order_by(Pedido.fecha_creacion.desc())

    if filters:
        if 'estado' in filters and filters['estado']:
            # Permitir filtrar por un solo estado o una lista de estados
            if isinstance(filters['estado'], list):
                query = query.filter(Pedido.estado_pedido.in_([EstadoPedido(s) for s in filters['estado']]))
            else:
                query = query.filter(Pedido.estado_pedido == EstadoPedido(filters['estado']))
        if 'tipo_venta' in filters and filters['tipo_venta']:
             query = query.filter(Pedido.tipo_venta == TipoVenta(filters['tipo_venta']))
        if 'cliente_id' in filters and filters['cliente_id']:
             query = query.filter(Pedido.cliente_id == filters['cliente_id'])
        if 'repartidor_id' in filters and filters['repartidor_id']:
             query = query.filter(Pedido.repartidor_id == filters['repartidor_id'])
        if 'fecha_desde' in filters and filters['fecha_desde']:
             # Asumimos filters['fecha_desde'] es un objeto datetime o date
             query = query.filter(Pedido.fecha_creacion >= filters['fecha_desde'])
        if 'fecha_hasta' in filters and filters['fecha_hasta']:
             # Asumimos filters['fecha_hasta'] es un objeto datetime o date
             # Para incluir todo el día, sumar un día o usar el final del día
             # Si es date, convertir a datetime y añadir 23:59:59
             fecha_hasta_dt = filters['fecha_hasta']
             if isinstance(fecha_hasta_dt, date) and not isinstance(fecha_hasta_dt, datetime):
                 fecha_hasta_dt = datetime.combine(fecha_hasta_dt, datetime.max.time())
             query = query.filter(Pedido.fecha_creacion <= fecha_hasta_dt)
        # Añadir más filtros según se necesite (ej. por total, por items, etc.)


    return query.paginate(page=page, per_page=per_page, error_out=False)

def get_active_pedidos(page: int = 1, per_page: int = 10):
    """
    Obtiene pedidos en estados activos (no finalizados/cancelados) para el dashboard.
    """
    # Definir estados considerados "activos"
    active_states = [
        EstadoPedido.PENDIENTE_CONFIRMACION,
        EstadoPedido.PENDIENTE_PREPARACION,
        EstadoPedido.EN_PREPARACION,
        EstadoPedido.LISTO_PARA_ENTREGA,
        EstadoPedido.ASIGNADO_A_REPARTIDOR,
        EstadoPedido.EN_RUTA,
        EstadoPedido.ENTREGADO_PENDIENTE_PAGO,
        EstadoPedido.PROBLEMA_EN_ENTREGA,
        EstadoPedido.REPROGRAMADO,
    ]
    query = Pedido.query.filter(Pedido.estado_pedido.in_(active_states)).order_by(Pedido.fecha_creacion.asc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def search_pedidos(query: str, page: int = 1, per_page: int = 10):
    """
    Busca pedidos por folio, nombre/alias de cliente, o número de teléfono.
    """
    search_term = f"%{query}%"

    # Buscar por folio (si el folio es el ID, convertir query a int si es posible)
    pedido_by_id = None
    try:
        pedido_id = int(query)
        pedido_by_id = Pedido.query.filter_by(id=pedido_id)
    except ValueError:
        pass # No es un ID numérico

    # Buscar por nombre/alias de cliente (requiere join con Cliente)
    pedidos_by_client_name_alias = Pedido.query.join(Pedido.cliente).filter(
        (Cliente.nombre.ilike(search_term)) |
        (Cliente.apellidos.ilike(search_term)) |
        (Cliente.alias.ilike(search_term))
    )

    # Buscar por número de teléfono (requiere join con Cliente y Telefono)
    pedidos_by_phone = Pedido.query.join(Pedido.cliente).join(Cliente.telefonos).filter(
        Telefono.numero_telefono.ilike(search_term)
    )

    # Combinar resultados
    combined_query = pedidos_by_client_name_alias.union(pedidos_by_phone)
    if pedido_by_id:
        combined_query = combined_query.union(pedido_by_id)

    # Aplicar paginación y ordenación
    pagination = combined_query.order_by(Pedido.fecha_creacion.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return pagination


def update_pedido(
    pedido_id: int,
    cliente_id: Optional[int] = None,
    direccion_entrega_id: Optional[int] = None,
    repartidor_id: Optional[int] = None,
    tipo_venta_value: Optional[str] = None,
    forma_pago_value: Optional[str] = None,
    paga_con: Optional[Decimal] = None,
    cambio_entregado: Optional[Decimal] = None,
    descuento_aplicado: Optional[Decimal] = None,
    costo_envio: Optional[Decimal] = None,
    estado_pedido_value: Optional[str] = None,
    notas_pedido: Optional[str] = None,
    fecha_entrega_programada: Optional[datetime] = None,
    requiere_factura: Optional[bool] = None
) -> Optional[Pedido]:
    """
    Actualiza los datos principales de un pedido existente.
    No actualiza ítems ni PAs directamente.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al actualizar pedido: Pedido con ID {pedido_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido puede ser modificado según su estado actual
    # if not pedido.puede_ser_modificado():
    #      print(f"Error al actualizar pedido {pedido_id}: El pedido no puede ser modificado en estado {pedido.estado_pedido.value}.")
    #      return None

    try:
        if cliente_id is not None:
            pedido.cliente_id = cliente_id
        if direccion_entrega_id is not None:
            pedido.direccion_entrega_id = direccion_entrega_id
        if repartidor_id is not None:
            # Validar repartidor si se asigna
            if repartidor_id != 0: # 0 puede ser el valor para "no asignado" en el formulario
                repartidor = Usuario.query.get(repartidor_id)
                if not repartidor or not repartidor.is_repartidor():
                     print("Error al actualizar pedido: Repartidor asignado no válido.")
                     # No hacer rollback aquí, solo no asignar el repartidor y quizás añadir un error
                     # raise ValueError("Repartidor asignado no válido.") # O lanzar excepción
                     pass # O simplemente no actualizar el campo si es inválido
                else:
                    pedido.repartidor_id = repartidor_id
            else:
                 pedido.repartidor_id = None # Desasignar repartidor si se envía 0

        if tipo_venta_value is not None:
            pedido.tipo_venta = TipoVenta(tipo_venta_value)
        if forma_pago_value is not None:
            pedido.forma_pago = FormaPago(forma_pago_value)
        if paga_con is not None:
            pedido.paga_con = paga_con
        if cambio_entregado is not None:
            pedido.cambio_entregado = cambio_entregado
        if descuento_aplicado is not None:
            pedido.descuento_aplicado = descuento_aplicado
            _recalculate_pedido_totals(pedido) # Recalcular si cambia descuento/costo_envio
        if costo_envio is not None:
            pedido.costo_envio = costo_envio
            _recalculate_pedido_totals(pedido) # Recalcular si cambia descuento/costo_envio
        if estado_pedido_value is not None:
            # Usar una función dedicada para transiciones de estado si hay lógica compleja
            # update_pedido_status(pedido, estado_pedido_value)
            pedido.estado_pedido = EstadoPedido(estado_pedido_value) # Actualización directa para MVP
        if notas_pedido is not None:
            pedido.notas_pedido = notas_pedido
        if fecha_entrega_programada is not None:
            pedido.fecha_entrega_programada = fecha_entrega_programada
        if requiere_factura is not None:
            pedido.requiere_factura = requiere_factura

        # fecha_actualizacion se actualiza automáticamente por onupdate=datetime.utcnow

        db.session.commit()
        return pedido

    except ValueError as e:
        db.session.rollback()
        print(f"Error al actualizar pedido {pedido_id}: Valor de Enum no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al actualizar pedido {pedido_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar pedido {pedido_id}: {e}")
        return None

def delete_pedido(pedido_id: int) -> bool:
    """
    Elimina un pedido y sus ítems/PAs asociados.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al eliminar pedido: Pedido con ID {pedido_id} no encontrado.")
        return False

    # Opcional: Validar si el pedido puede ser eliminado según su estado
    # if pedido.estado_pedido not in [EstadoPedido.PENDIENTE_CONFIRMACION, EstadoPedido.CANCELADO_POR_CLIENTE, EstadoPedido.CANCELADO_POR_NEGOCIO]:
    #      print(f"Error al eliminar pedido {pedido_id}: El pedido no puede ser eliminado en estado {pedido.estado_pedido.value}. Considere cancelarlo.")
    #      return False

    try:
        # Las cascadas 'all, delete-orphan' en las relaciones 'items' y 'productos_adicionales_pedido'
        # deberían eliminar los ítems y PAs automáticamente.
        # Los movimientos de caja asociados podrían necesitar manejo (ej. marcarlos como anulados o eliminarlos si aplica).
        # Para MVP, asumimos que la cascada es suficiente o que los movimientos se manejan por separado si es necesario.
        db.session.delete(pedido)
        db.session.commit()
        return True
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al eliminar pedido {pedido_id}: No se puede eliminar porque tiene registros asociados que impiden la cascada (ej. movimientos de caja no configurados para cascada).")
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar pedido {pedido_id}: {e}")
        return False

def update_pedido_status(pedido_id: int, new_estado_value: str) -> Optional[Pedido]:
    """
    Actualiza el estado de un pedido, aplicando lógica de transición si es necesario.
    Para MVP, es una actualización directa, pero aquí iría la lógica compleja.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al actualizar estado: Pedido con ID {pedido_id} no encontrado.")
        return None

    try:
        new_estado_enum = EstadoPedido(new_estado_value)
        # Aquí iría la lógica para validar si la transición de pedido.estado_pedido a new_estado_enum es válida
        # Por ejemplo:
        # if pedido.estado_pedido == EstadoPedido.EN_RUTA and new_estado_enum == EstadoPedido.PENDIENTE_PREPARACION:
        #     print("Error: No se puede retroceder de EN_RUTA a PENDIENTE_PREPARACION.")
        #     return None

        pedido.estado_pedido = new_estado_enum
        db.session.commit()
        return pedido

    except ValueError as e:
        db.session.rollback()
        print(f"Error al actualizar estado del pedido {pedido_id}: Valor de estado '{new_estado_value}' no válido - {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar estado del pedido {pedido_id}: {e}")
        return None


# --- Funciones de Servicio para PedidoItem ---

def add_pedido_item(
    pedido_id: int,
    usuario_id: int, # Usuario que añade el ítem (para log/auditoría si se necesita)
    producto_id: Optional[str] = None,
    subproducto_id: Optional[int] = None,
    modificacion_id: Optional[int] = None,
    cantidad: Decimal = Decimal('0.0'),
    unidad_medida: str = 'kg',
    precio_unitario_venta: Optional[Decimal] = None, # Opcional, se puede calcular
    notas_item: Optional[str] = None
) -> Optional[PedidoItem]:
    """
    Añade un nuevo PedidoItem a un pedido existente.
    Calcula el precio unitario si no se provee y el subtotal.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al añadir ítem: Pedido con ID {pedido_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido puede ser modificado
    # if not pedido.puede_ser_modificado():
    #      print(f"Error al añadir ítem al pedido {pedido_id}: El pedido no puede ser modificado en estado {pedido.estado_pedido.value}.")
    #      return None

    if cantidad <= Decimal('0.0'):
        print("Error al añadir ítem: La cantidad debe ser positiva.")
        return None

    if not producto_id and not subproducto_id:
         print("Error al añadir ítem: Debe especificar un producto o subproducto.")
         return None

    try:
        # 1. Determinar precio unitario si no se provee
        final_precio_unitario = precio_unitario_venta
        if final_precio_unitario is None:
            # Usar la lógica de obtención de precio aplicable (Sección 4.2)
            final_precio_unitario = _get_precio_aplicable(
                producto_id=producto_id,
                subproducto_id=subproducto_id,
                cliente_id=pedido.cliente_id, # Usar el cliente del pedido
                cantidad_solicitada=cantidad
            )
            if final_precio_unitario is None:
                 print("Error al añadir ítem: No se pudo determinar el precio aplicable.")
                 return None # No se puede añadir el ítem sin precio

        # 2. Generar descripción del ítem (Sección 4.1)
        descripcion_item = _get_item_description(producto_id, subproducto_id, modificacion_id)

        # 3. Calcular subtotal
        subtotal = cantidad * final_precio_unitario
        subtotal = round(subtotal, 2) # Asegurar precisión

        # 4. Crear el PedidoItem
        item = PedidoItem(
            pedido_id=pedido.id,
            producto_id=producto_id,
            subproducto_id=subproducto_id,
            modificacion_id=modificacion_id,
            descripcion_item_venta=descripcion_item,
            cantidad=cantidad,
            unidad_medida=unidad_medida,
            precio_unitario_venta=final_precio_unitario,
            subtotal_item=subtotal,
            notas_item=notas_item
            # costo_unitario_item (opcional, para futuro)
        )

        db.session.add(item)
        db.session.flush() # Para que el ítem tenga ID si es necesario

        # 5. Recalcular totales del pedido
        _recalculate_pedido_totals(pedido)

        db.session.commit()
        return item

    except ValueError as e:
        db.session.rollback()
        print(f"Error al añadir ítem al pedido {pedido_id}: Valor no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al añadir ítem al pedido {pedido_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al añadir ítem al pedido {pedido_id}: {e}")
        return None

def get_pedido_item_by_id(item_id: int) -> Optional[PedidoItem]:
    """Obtiene un PedidoItem por su ID."""
    return PedidoItem.query.get(item_id)

def update_pedido_item(
    item_id: int,
    cantidad: Optional[Decimal] = None,
    unidad_medida: Optional[str] = None,
    precio_unitario_venta: Optional[Decimal] = None,
    notas_item: Optional[str] = None
) -> Optional[PedidoItem]:
    """
    Actualiza un PedidoItem existente. Recalcula subtotal del ítem y totales del pedido.
    No permite cambiar producto/subproducto/modificación.
    """
    item = get_pedido_item_by_id(item_id)
    if not item:
        print(f"Error al actualizar ítem: PedidoItem con ID {item_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not item.pedido.puede_ser_modificado():
    #      print(f"Error al actualizar ítem {item_id}: El pedido asociado no puede ser modificado.")
    #      return None

    try:
        if cantidad is not None:
            if cantidad <= Decimal('0.0'):
                 print("Error al actualizar ítem: La cantidad debe ser positiva.")
                 return None
            item.cantidad = cantidad

        if unidad_medida is not None:
            item.unidad_medida = unidad_medida # Validar si la unidad es compatible con el producto/subproducto?

        if precio_unitario_venta is not None:
            if precio_unitario_venta < Decimal('0.0'):
                 print("Error al actualizar ítem: El precio no puede ser negativo.")
                 return None
            item.precio_unitario_venta = precio_unitario_venta
        # Si no se provee precio_unitario_venta pero cambia la cantidad,
        # ¿deberíamos recalcular el precio basado en la nueva cantidad y tipo de cliente?
        # Para MVP, asumimos que el precio unitario se mantiene a menos que se especifique,
        # o que la UI maneja la actualización del precio unitario si cambia la cantidad.
        # Si se necesita recalcular el precio unitario basado en la nueva cantidad:
        # if cantidad is not None and precio_unitario_venta is None:
        #     item.precio_unitario_venta = _get_precio_aplicable(...) # Necesita acceso a cliente_id, producto/subproducto IDs

        if notas_item is not None:
            item.notas_item = notas_item

        # Recalcular subtotal del ítem
        item.actualizar_subtotal()

        # Recalcular totales del pedido asociado
        _recalculate_pedido_totals(item.pedido)

        db.session.commit()
        return item

    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar PedidoItem {item_id}: {e}")
        return None

def delete_pedido_item(item_id: int) -> bool:
    """
    Elimina un PedidoItem y recalcula los totales del pedido asociado.
    """
    item = get_pedido_item_by_id(item_id)
    if not item:
        print(f"Error al eliminar ítem: PedidoItem con ID {item_id} no encontrado.")
        return False

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not item.pedido.puede_ser_modificado():
    #      print(f"Error al eliminar ítem {item_id}: El pedido asociado no puede ser modificado.")
    #      return False

    pedido = item.pedido # Guardar referencia al pedido antes de eliminar el ítem

    try:
        db.session.delete(item)
        db.session.flush() # Aplicar la eliminación para que _recalculate_pedido_totals vea el cambio

        # Recalcular totales del pedido asociado
        _recalculate_pedido_totals(pedido)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar PedidoItem {item_id}: {e}")
        return False


# --- Funciones de Servicio para ProductoAdicional ---

def add_producto_adicional(
    pedido_id: int,
    usuario_id: int, # Usuario que añade el PA
    nombre_pa: str,
    cantidad_pa: Decimal = Decimal('1.0'),
    unidad_medida_pa: str = 'pieza',
    costo_compra_unitario_pa: Optional[Decimal] = None,
    precio_venta_unitario_pa: Optional[Decimal] = None, # Opcional, se puede calcular
    notas_pa: Optional[str] = None
) -> Optional[ProductoAdicional]:
    """
    Añade un nuevo ProductoAdicional a un pedido existente.
    Calcula el precio de venta y subtotal, incluyendo comisión si aplica.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al añadir PA: Pedido con ID {pedido_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido puede ser modificado
    # if not pedido.puede_ser_modificado():
    #      print(f"Error al añadir PA al pedido {pedido_id}: El pedido no puede ser modificado en estado {pedido.estado_pedido.value}.")
    #      return None

    if cantidad_pa <= Decimal('0.0'):
        print("Error al añadir PA: La cantidad debe ser positiva.")
        return None

    try:
        # 1. Determinar precio de venta unitario y calcular comisión (Sección 4.3)
        final_precio_venta = precio_venta_unitario_pa
        comision_calculada = Decimal('0.0')

        # Si no se provee precio de venta, pero sí costo de compra, calcular precio con comisión
        if final_precio_venta is None and costo_compra_unitario_pa is not None:
            # Obtener configuración de comisión (asumimos una única fila de config)
            config = ConfiguracionSistema.query.get(1)
            limite_sin_comision = config.limite_items_pa_sin_comision if config else 3
            monto_comision_fija = config.monto_comision_fija_pa_extra if config else Decimal('4.0')

            # Contar PAs existentes en el pedido para saber si este nuevo excede el límite
            current_pas_count = pedido.productos_adicionales_pedido.count()

            if current_pas_count >= limite_sin_comision:
                comision_calculada = monto_comision_fija

            final_precio_venta = costo_compra_unitario_pa + comision_calculada
            final_precio_venta = round(final_precio_venta, 2) # Asegurar precisión

        elif final_precio_venta is None and costo_compra_unitario_pa is None:
             print("Error al añadir PA: Debe proporcionar precio de venta o costo de compra.")
             return None # No se puede añadir el PA sin precio

        # Si se provee precio de venta directamente, no calculamos comisión automática para MVP
        # Lógica futura podría recalcular comisión incluso si se da el precio de venta

        # 2. Calcular subtotal
        subtotal = cantidad_pa * final_precio_venta
        subtotal = round(subtotal, 2) # Asegurar precisión

        # 3. Crear el ProductoAdicional
        pa = ProductoAdicional(
            pedido_id=pedido.id,
            nombre_pa=nombre_pa,
            cantidad_pa=cantidad_pa,
            unidad_medida_pa=unidad_medida_pa,
            costo_compra_unitario_pa=costo_compra_unitario_pa,
            precio_venta_unitario_pa=final_precio_venta,
            subtotal_pa=subtotal,
            comision_calculada_pa=comision_calculada,
            notas_pa=notas_pa
        )

        db.session.add(pa)
        db.session.flush() # Para que el PA tenga ID si es necesario

        # 4. Recalcular totales del pedido
        _recalculate_pedido_totals(pedido)

        db.session.commit()
        return pa

    except ValueError as e:
        db.session.rollback()
        print(f"Error al añadir PA al pedido {pedido_id}: Valor no válido - {e}")
        return None
    except IntegrityError as e:
        db.session.rollback()
        print(f"Error de integridad al añadir PA al pedido {pedido_id}: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al añadir PA al pedido {pedido_id}: {e}")
        return None

def get_producto_adicional_by_id(pa_id: int) -> Optional[ProductoAdicional]:
    """Obtiene un ProductoAdicional por su ID."""
    return ProductoAdicional.query.get(pa_id)

def update_producto_adicional(
    pa_id: int,
    nombre_pa: Optional[str] = None,
    cantidad_pa: Optional[Decimal] = None,
    unidad_medida_pa: Optional[str] = None,
    costo_compra_unitario_pa: Optional[Decimal] = None,
    precio_venta_unitario_pa: Optional[Decimal] = None,
    notas_pa: Optional[str] = None
) -> Optional[ProductoAdicional]:
    """
    Actualiza un ProductoAdicional existente. Recalcula subtotal del PA y totales del pedido.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        print(f"Error al actualizar PA: ProductoAdicional con ID {pa_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not pa.pedido.puede_ser_modificado():
    #      print(f"Error al actualizar PA {pa_id}: El pedido asociado no puede ser modificado.")
    #      return None

    try:
        # Bandera para saber si necesitamos recalcular precio de venta/comisión
        recalcular_precio_comision = False

        if nombre_pa is not None:
            pa.nombre_pa = nombre_pa
        if cantidad_pa is not None:
            if cantidad_pa <= Decimal('0.0'):
                 print("Error al actualizar PA: La cantidad debe ser positiva.")
                 return None
            pa.cantidad_pa = cantidad_pa
            recalcular_precio_comision = True # La cantidad puede afectar la comisión si la lógica es por PA
        if unidad_medida_pa is not None:
            pa.unidad_medida_pa = unidad_medida_pa
            recalcular_precio_comision = True # La unidad puede afectar la lógica (ej. MONTO)
        if costo_compra_unitario_pa is not None:
            if costo_compra_unitario_pa < Decimal('0.0'):
                 print("Error al actualizar PA: El costo no puede ser negativo.")
                 return None
            pa.costo_compra_unitario_pa = costo_compra_unitario_pa
            recalcular_precio_comision = True # Cambiar costo afecta precio de venta calculado
        if precio_venta_unitario_pa is not None:
            if precio_venta_unitario_pa < Decimal('0.0'):
                 print("Error al actualizar PA: El precio no puede ser negativo.")
                 return None
            pa.precio_venta_unitario_pa = precio_venta_unitario_pa
            pa.comision_calculada_pa = None # Si se establece precio manual, resetear comisión calculada automática
            # No recalcular precio/comisión si se provee precio de venta directamente
            recalcular_precio_comision = False # Desactivar recalculo automático si se da precio manual
        if notas_pa is not None:
            pa.notas_pa = notas_pa

        # Recalcular precio de venta y comisión si es necesario (si no se dio precio manual)
        if recalcular_precio_comision and pa.costo_compra_unitario_pa is not None:
             # Obtener configuración de comisión
            config = ConfiguracionSistema.query.get(1)
            limite_sin_comision = config.limite_items_pa_sin_comision if config else 3
            monto_comision_fija = config.monto_comision_fija_pa_extra if config else Decimal('4.0')

            # Contar PAs en el pedido (excluyendo este PA si la lógica de comisión es por PA individual)
            # Para MVP, la lógica de comisión es simple: si el *total* de PAs excede el límite,
            # CADA PA *extra* tiene la comisión. Esto es más complejo de recalcular aquí.
            # Una lógica más simple para MVP: si costo_compra_unitario_pa está presente,
            # aplicar la comisión fija si el PA *en sí mismo* es >= al límite (no ideal, pero simple).
            # O, contar todos los PAs *después* de la actualización y aplicar comisión a los que corresponda.
            # Para mantenerlo simple en MVP: si se actualiza costo_compra, recalcular precio con comisión fija si aplica.
            # La lógica de contar PAs para el límite es mejor hacerla al *añadir* PAs.
            # Al actualizar, si se cambia el costo, simplemente aplicar la comisión fija si existe.
            # Si se cambia la cantidad, la comisión *podría* cambiar si la lógica fuera por cantidad total de PAs.
            # Para MVP, asumimos que la comisión fija se aplica si hay costo_compra > 0 y la config existe.
            # Lógica simplificada: si hay costo_compra, aplicar comisión fija.
            if pa.costo_compra_unitario_pa > Decimal('0.0') and config:
                 pa.comision_calculada_pa = config.monto_comision_fija_pa_extra
                 pa.precio_venta_unitario_pa = pa.costo_compra_unitario_pa + pa.comision_calculada_pa
            elif pa.costo_compra_unitario_pa is not None: # Si costo es 0 o None
                 pa.comision_calculada_pa = Decimal('0.0')
                 pa.precio_venta_unitario_pa = pa.costo_compra_unitario_pa # Precio = Costo si no hay comisión

            if pa.precio_venta_unitario_pa is not None:
                 pa.precio_venta_unitario_pa = round(pa.precio_venta_unitario_pa, 2)


        # Recalcular subtotal del PA
        pa.calcular_subtotal_pa()

        # Recalcular totales del pedido asociado
        _recalculate_pedido_totals(pa.pedido)

        db.session.commit()
        return pa

    except ValueError as e:
        db.session.rollback()
        print(f"Error al actualizar PA {pa_id}: Valor no válido - {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al actualizar ProductoAdicional {pa_id}: {e}")
        return None

def delete_producto_adicional(pa_id: int) -> bool:
    """
    Elimina un ProductoAdicional y recalcula los totales del pedido asociado.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        print(f"Error al eliminar PA: ProductoAdicional con ID {pa_id} no encontrado.")
        return False

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not pa.pedido.puede_ser_modificado():
    #      print(f"Error al eliminar PA {pa_id}: El pedido asociado no puede ser modificado.")
    #      return False

    pedido = pa.pedido # Guardar referencia al pedido antes de eliminar el PA

    try:
        db.session.delete(pa)
        db.session.flush() # Aplicar la eliminación para que _recalculate_pedido_totals vea el cambio

        # Recalcular totales del pedido asociado
        _recalculate_pedido_totals(pedido)

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al eliminar ProductoAdicional {pa_id}: {e}")
        return False


# --- Funciones de Servicio para Procesar Pagos y Movimientos de Caja (Sección 5) ---

def process_pedido_payment(
    pedido_id: int,
    usuario_id_cajero: int, # Cajero que procesa el pago
    forma_pago_value: str,
    monto_recibido: Optional[Decimal] = None, # Solo para efectivo
    denominaciones_recibidas: Optional[Dict[Decimal, int]] = None # Solo para efectivo
) -> Optional[Pedido]:
    """
    Procesa el pago de un pedido, registra el movimiento de caja y actualiza el estado del pedido.
    Asume que el pedido ya tiene sus ítems y totales calculados.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al procesar pago: Pedido con ID {pedido_id} no encontrado.")
        return None

    # Opcional: Validar si el pedido está en un estado que permite el pago
    # if pedido.estado_pedido not in [EstadoPedido.LISTO_PARA_ENTREGA, EstadoPedido.ENTREGADO_PENDIENTE_PAGO]:
    #      print(f"Error al procesar pago del pedido {pedido_id}: El pedido no está en un estado válido para pago ({pedido.estado_pedido.value}).")
    #      return None

    try:
        forma_pago_enum = FormaPago(forma_pago_value)

        # Validar monto recibido para efectivo
        if forma_pago_enum == FormaPago.EFECTIVO:
            if monto_recibido is None or monto_recibido < pedido.total_pedido:
                print(f"Error al procesar pago en efectivo: Monto recibido ({monto_recibido}) es insuficiente para el total del pedido ({pedido.total_pedido}).")
                return None
            if denominaciones_recibidas is None:
                 print("Error al procesar pago en efectivo: Se requieren detalles de denominaciones recibidas.")
                 return None

            # Calcular cambio y sugerir denominaciones (Lógica de Sección 4.4)
            cambio_total = monto_recibido - pedido.total_pedido
            # Para MVP, no necesitamos las existencias de caja aquí, solo calcular el cambio
            # La sugerencia de denominaciones se haría en la UI antes de llamar a este servicio
            # Si se necesitara la sugerencia aquí, se llamaría a calcular_y_sugerir_cambio_con_denominaciones
            # y se validaría si el cambio es posible.

            pedido.paga_con = monto_recibido
            pedido.cambio_entregado = cambio_total
            # El egreso del cambio se registra como parte del movimiento de ingreso o como un egreso separado
            # Para MVP, registramos el ingreso total recibido y el egreso del cambio como parte del mismo movimiento de ingreso de venta.

        elif forma_pago_enum in [FormaPago.TARJETA_DEBITO, FormaPago.TARJETA_CREDITO, FormaPago.TRANSFERENCIA_BANCARIA, FormaPago.QR_PAGO]:
            # Para pagos no efectivo, el monto recibido es el total del pedido
            monto_recibido = pedido.total_pedido
            pedido.paga_con = pedido.total_pedido # Opcional, registrar que se pagó el total
            pedido.cambio_entregado = Decimal('0.0') # No hay cambio

        elif forma_pago_enum == FormaPago.CREDITO_INTERNO:
             # No hay movimiento de caja inmediato, solo se registra la forma de pago
             monto_recibido = Decimal('0.0') # O el total del pedido, dependiendo de cómo se quiera registrar
             pedido.paga_con = Decimal('0.0')
             pedido.cambio_entregado = Decimal('0.0')
             # El movimiento de caja (INGRESO) se registrará cuando se pague el crédito

        elif forma_pago_enum == FormaPago.CORTESIA:
             monto_recibido = Decimal('0.0')
             pedido.paga_con = Decimal('0.0')
             pedido.cambio_entregado = Decimal('0.0')
             # No hay movimiento de caja

        elif forma_pago_enum == FormaPago.EFECTIVO_CONTRA_ENTREGA:
             # Este caso se maneja en la liquidación del repartidor (registrar_ingreso_liquidacion_repartidor)
             # No se procesa el pago aquí, solo se registra la forma de pago en create_pedido/update_pedido
             print(f"Advertencia: Intentando procesar pago EFECTIVO_CONTRA_ENTREGA para pedido {pedido_id} en la función process_pedido_payment.")
             # Podríamos permitir registrar el monto esperado aquí si es útil
             # pedido.paga_con = monto_recibido # Monto esperado
             # No registrar movimiento de caja aquí
             pass # No hacer nada más para este caso en esta función

        else:
            print(f"Error al procesar pago: Forma de pago '{forma_pago_value}' no soportada para procesamiento inmediato.")
            return None


        # Registrar Movimiento de Caja (si aplica)
        if forma_pago_enum in [FormaPago.EFECTIVO, FormaPago.TARJETA_DEBITO, FormaPago.TARJETA_CREDITO, FormaPago.TRANSFERENCIA_BANCARIA, FormaPago.QR_PAGO]:
            motivo = f"Venta Pedido {pedido.tipo_venta.name.replace('_', ' ').title()} #{format_pedido_folio(pedido.id)}"
            # Para efectivo, el monto del movimiento es el total del pedido, no el monto recibido
            # El cambio se maneja en el detalle de denominaciones del movimiento
            monto_movimiento = pedido.total_pedido

            movimiento = registrar_movimiento_caja(
                usuario_id=usuario_id_cajero,
                tipo_movimiento=TipoMovimientoCaja.INGRESO.value,
                motivo_movimiento=motivo,
                monto_movimiento=monto_movimiento,
                forma_pago_efectuado=forma_pago_enum.value,
                notas_movimiento=f"Pago de pedido {format_pedido_folio(pedido.id)}",
                pedido_id=pedido.id,
                # Para efectivo, pasar las denominaciones recibidas.
                # El servicio registrar_movimiento_caja manejará el egreso del cambio en el detalle de denominaciones.
                denominaciones_contadas=denominaciones_recibidas if forma_pago_enum == FormaPago.EFECTIVO else None
            )

            if not movimiento:
                print(f"Error al registrar movimiento de caja para pedido {pedido_id}.")
                db.session.rollback() # Rollback si el movimiento de caja falla
                return None

        # Actualizar estado del pedido a PAGADO o ENTREGADO_Y_PAGADO
        # Si es mostrador, pasa a ENTREGADO_Y_PAGADO inmediatamente
        # Si es domicilio y el repartidor liquida, pasa a PAGADO o ENTREGADO_Y_PAGADO
        # Para MVP, simplificamos: si se procesa el pago aquí, el estado final es PAGADO o ENTREGADO_Y_PAGADO
        if pedido.tipo_venta == TipoVenta.MOSTRADOR:
             pedido.estado_pedido = EstadoPedido.ENTREGADO_Y_PAGADO
        elif pedido.tipo_venta == TipoVenta.DOMICILIO and forma_pago_enum != FormaPago.EFECTIVO_CONTRA_ENTREGA:
             # Si se paga antes de la entrega (ej. transferencia previa), puede pasar a PAGADO
             pedido.estado_pedido = EstadoPedido.PAGADO
        elif pedido.tipo_venta == TipoVenta.DOMICILIO and forma_pago_enum == FormaPago.EFECTIVO_CONTRA_ENTREGA:
             # Este caso se maneja en la liquidación del repartidor
             pass # No cambiar estado aquí

        pedido.forma_pago = forma_pago_enum # Asegurar que la forma de pago quede registrada en el pedido

        db.session.commit()
        return pedido

    except ValueError as e:
        db.session.rollback()
        print(f"Error al procesar pago del pedido {pedido_id}: Valor de Enum no válido - {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al procesar pago del pedido {pedido_id}: {e}")
        return None

# --- Funciones relacionadas con el flujo de Repartidores y PAs (Sección 5.3, 4.5) ---

def process_compra_pa_egreso(
    pedido_id: int,
    usuario_id_cajero: int, # Cajero que entrega el dinero
    nombre_pa: str, # Nombre del PA comprado
    costo_compra: Decimal, # Costo total de la compra de ese PA
    denominaciones_usadas: Dict[Decimal, int] # Detalle del efectivo entregado
) -> Optional[MovimientoCaja]:
    """
    Registra el egreso de caja por la compra de un Producto Adicional para un pedido a domicilio.
    Reutiliza el servicio de caja.
    """
    # Validar que el pedido exista y sea a domicilio (opcional)
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al registrar egreso PA: Pedido con ID {pedido_id} no encontrado.")
        return None
    # if pedido.tipo_venta != TipoVenta.DOMICILIO:
    #      print(f"Advertencia: Registrando egreso PA para pedido de tipo {pedido.tipo_venta.value}, esperado DOMICILIO.")

    # Llamar al servicio de caja específico para egresos de PA
    movimiento = registrar_egreso_compra_pa(
        usuario_id_cajero=usuario_id_cajero,
        pedido_id=pedido_id,
        nombre_pa=nombre_pa,
        costo_compra=costo_compra,
        denominaciones_usadas=denominaciones_usadas
    )
    return movimiento


def process_repartidor_liquidacion(
    pedido_id: int,
    usuario_id_repartidor_o_cajero: int, # Usuario que liquida (repartidor) o que recibe (cajero)
    monto_recibido: Decimal, # Monto total de efectivo entregado por el repartidor para este pedido
    denominaciones_recibidas: Dict[Decimal, int] # Detalle del efectivo entregado
) -> Optional[Pedido]:
    """
    Procesa la liquidación de un pedido a domicilio por parte de un repartidor.
    Registra el ingreso de caja y actualiza el estado del pedido.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        print(f"Error al procesar liquidación: Pedido con ID {pedido_id} no encontrado.")
        return None

    # Validar que el pedido sea a domicilio y esté en un estado que permita liquidación
    # (ej. EN_RUTA, ENTREGADO_PENDIENTE_PAGO, PROBLEMA_EN_ENTREGA, ASIGNADO_A_REPARTIDOR)
    liquidable_states = [
        EstadoPedido.ASIGNADO_A_REPARTIDOR,
        EstadoPedido.EN_RUTA,
        EstadoPedido.ENTREGADO_PENDIENTE_PAGO,
        EstadoPedido.PROBLEMA_EN_ENTREGA,
        EstadoPedido.REPROGRAMADO # Si se liquida después de un problema/reprogramación
    ]
    if pedido.tipo_venta != TipoVenta.DOMICILIO or pedido.estado_pedido not in liquidable_states:
         print(f"Error al procesar liquidación del pedido {pedido_id}: El pedido no es a domicilio o no está en un estado liquidable ({pedido.estado_pedido.value}).")
         return None

    if monto_recibido < Decimal('0.0'):
         print("Error al procesar liquidación: El monto recibido no puede ser negativo.")
         return None

    if not denominaciones_recibidas:
         print("Error al procesar liquidación: Se requieren detalles de denominaciones recibidas.")
         return None

    try:
        # Registrar el Movimiento de Caja de INGRESO por la liquidación
        # El monto del movimiento es el efectivo total entregado por el repartidor
        movimiento = registrar_ingreso_liquidacion_repartidor(
            usuario_id_repartidor_o_cajero=usuario_id_repartidor_o_cajero,
            pedido_id=pedido.id,
            monto_recibido=monto_recibido,
            denominaciones_recibidas=denominaciones_recibidas
        )

        if not movimiento:
            print(f"Error al registrar movimiento de liquidación para pedido {pedido_id}.")
            db.session.rollback() # Rollback si el movimiento de caja falla
            return None

        # Actualizar estado del pedido a PAGADO o ENTREGADO_Y_PAGADO
        # Si ya estaba ENTREGADO_PENDIENTE_PAGO, pasa a ENTREGADO_Y_PAGADO
        # Si estaba en otro estado (EN_RUTA, PROBLEMA), pasa a PAGADO (o ENTREGADO_Y_PAGADO si se considera entregado al liquidar)
        # Para MVP, simplificamos: pasa a ENTREGADO_Y_PAGADO si estaba en un estado de entrega/problema, o a PAGADO si no.
        if pedido.estado_pedido in [EstadoPedido.EN_RUTA, EstadoPedido.ENTREGADO_PENDIENTE_PAGO, EstadoPedido.PROBLEMA_EN_ENTREGA, EstadoPedido.REPROGRAMADO]:
             pedido.estado_pedido = EstadoPedido.ENTREGADO_Y_PAGADO
        else:
             pedido.estado_pedido = EstadoPedido.PAGADO # Ej. si se liquida un pedido que nunca salió por algún motivo

        # Opcional: Registrar el monto liquidado en el pedido si es diferente al total_pedido
        # Esto podría ser útil si hay diferencias en la liquidación
        # pedido.monto_liquidado_repartidor = monto_recibido # Necesitaría un campo en el modelo Pedido

        db.session.commit()
        return pedido

    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al procesar liquidación del pedido {pedido_id}: {e}")
        return None

# Puedes añadir más funciones de servicio aquí según se necesiten
# Por ejemplo: funciones para obtener pedidos por repartidor, por cliente, por rango de fechas, etc.