# Archivo: PolleriaMontiel\app\pedidos\routes.py

from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file # Importar jsonify y send_file para respuestas AJAX
from flask_login import login_required, current_user
from app import db
from app.models import (
    Pedido, PedidoItem, ProductoAdicional, Cliente, Direccion, Usuario,
    Producto, Subproducto, Modificacion, Precio, Telefono, ConfiguracionSistema,
    MovimientoCaja,
    TipoVenta, FormaPago, EstadoPedido, TipoMovimientoCaja, RolUsuario, TipoCliente
) # Importar todos los modelos y Enums necesarios
from . import pedidos # Importar el Blueprint
from .forms import PedidoForm, PedidoItemForm, ProductoAdicionalForm # Importar formularios
from .services import (
    create_pedido, get_pedido_by_id, get_all_pedidos, search_pedidos, get_active_pedidos,
    update_pedido, delete_pedido, update_pedido_status,
    add_pedido_item, get_pedido_item_by_id, update_pedido_item, delete_pedido_item,
    add_producto_adicional, get_producto_adicional_by_id, update_producto_adicional, delete_producto_adicional,
    process_pedido_payment, process_compra_pa_egreso, process_repartidor_liquidacion,
    _get_precio_aplicable # Importar función interna para AJAX de precio
) # Importar funciones de servicio
from app.utils.decorators import role_required # Importar el decorador de roles
from app.utils.helpers import format_currency, format_datetime, format_pedido_folio # Importar helpers
from decimal import Decimal # Importar Decimal
from datetime import datetime, date # Importar datetime y date
from sqlalchemy.orm import joinedload # Para cargar relaciones eager si es necesario
import json # Para manejar JSON en peticiones AJAX

# Roles permitidos para diferentes operaciones de pedidos
ROLES_PEDIDOS_RW = [RolUsuario.CAJERO, RolUsuario.ADMINISTRADOR] # Crear, ver, editar (limitado para Cajero)
ROLES_PEDIDOS_ADMIN = [RolUsuario.ADMINISTRADOR] # Eliminar, editar sin restricciones
ROLES_PEDIDOS_READ = [RolUsuario.CAJERO, RolUsuario.ADMINISTRADOR, RolUsuario.TABLAJERO, RolUsuario.REPARTIDOR] # Ver lista/detalle (con filtros/restricciones)
ROLES_PEDIDOS_PREPARACION = [RolUsuario.TABLAJERO, RolUsuario.ADMINISTRADOR] # Ver/actualizar estado de preparación
ROLES_PEDIDOS_ENTREGA = [RolUsuario.REPARTIDOR, RolUsuario.ADMINISTRADOR, RolUsuario.CAJERO] # Ver/actualizar estado de entrega, liquidar (Cajero/Admin pueden recibir liquidación)

# --- Rutas Principales de Pedidos ---

@pedidos.route('/')
@pedidos.route('/dashboard')
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles pueden ver algún dashboard de pedidos
def dashboard_pedidos():
    """
    Muestra el dashboard de pedidos activos o relevantes para el usuario actual.
    La vista y los filtros aplicados dependen del rol.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Pedidos por página
    search_query = request.args.get('q', type=str)
    filters = {} # Diccionario para filtros dinámicos

    # Lógica para filtrar pedidos según el rol del usuario
    if current_user.is_admin() or current_user.is_cajero():
        # Admin y Cajero ven todos los pedidos activos por defecto, o pueden buscar/filtrar
        if search_query:
            pedidos_pagination = search_pedidos(search_query, page=page, per_page=per_page)
            title = f'Resultados de búsqueda de Pedidos para "{search_query}"'
        else:
            # Mostrar pedidos activos por defecto para Cajeros/Admin en el dashboard
            pedidos_pagination = get_active_pedidos(page=page, per_page=per_page)
            title = 'Pedidos Activos'
            # Permitir filtros adicionales desde la UI si se implementan (ej. por estado, tipo venta)
            # filters['estado'] = request.args.get('estado', type=str)
            # filters['tipo_venta'] = request.args.get('tipo_venta', type=str)
            # pedidos_pagination = get_all_pedidos(page=page, per_page=per_page, filters=filters)

    elif current_user.is_tablajero():
        # Tablajero solo ve pedidos pendientes de preparación o en preparación
        filters['estado'] = [EstadoPedido.PENDIENTE_PREPARACION.value, EstadoPedido.EN_PREPARACION.value]
        # Podría filtrar por pedidos del día actual si es relevante
        # filters['fecha_desde'] = datetime.combine(date.today(), datetime.min.time())
        pedidos_pagination = get_all_pedidos(page=page, per_page=per_page, filters=filters)
        title = 'Pedidos Pendientes de Preparación'

    elif current_user.is_repartidor():
        # Repartidor solo ve pedidos asignados a él y en estados de entrega
        filters['repartidor_id'] = current_user.id
        filters['estado'] = [
            EstadoPedido.ASIGNADO_A_REPARTIDOR.value,
            EstadoPedido.EN_RUTA.value,
            EstadoPedido.ENTREGADO_PENDIENTE_PAGO.value,
            EstadoPedido.PROBLEMA_EN_ENTREGA.value,
            EstadoPedido.REPROGRAMADO.value
        ]
        pedidos_pagination = get_all_pedidos(page=page, per_page=per_page, filters=filters)
        title = f'Mis Pedidos Asignados ({current_user.nombre_completo})'

    else:
        # Otros roles (si los hubiera) o caso por defecto
        pedidos_pagination = None # No mostrar pedidos por defecto
        title = 'Pedidos'
        flash('No tienes permisos para ver pedidos.', 'warning')


    pedidos_list = pedidos_pagination.items if pedidos_pagination else []

    # Necesitarás una plantilla 'pedidos/dashboard_pedidos.html'
    return render_template(
        'pedidos/dashboard_pedidos.html',
        title=title,
        pedidos=pedidos_list,
        pagination=pedidos_pagination,
        search_query=search_query,
        format_currency=format_currency,
        format_datetime=format_datetime,
        format_pedido_folio=format_pedido_folio,
        EstadoPedido=EstadoPedido # Pasar el Enum para lógica en plantilla
    )


@pedidos.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden crear pedidos
def crear_pedido():
    """
    Permite crear un nuevo pedido.
    """
    form = PedidoForm()

    # Poblar choices dinámicos si es necesario (ej. Repartidores)
    # Asumiendo que necesitas una lista de usuarios con rol REPARTIDOR
    repartidores = Usuario.query.filter_by(rol=RolUsuario.REPARTIDOR, activo=True).order_by(Usuario.nombre_completo).all()
    # Añadir opción "Seleccionar Repartidor" con valor 0
    form.repartidor_id.choices = [(0, 'Seleccionar Repartidor')] + [(r.id, r.nombre_completo) for r in repartidores]

    if form.validate_on_submit():
        # Obtener el ID del usuario actual (cajero/admin)
        usuario_id_creador = current_user.id

        # Convertir 0 de repartidor_id a None si no se seleccionó uno
        repartidor_id_selected = form.repartidor_id.data if form.repartidor_id.data != 0 else None

        nuevo_pedido = create_pedido(
            usuario_id=usuario_id_creador,
            tipo_venta_value=form.tipo_venta.data,
            cliente_id=form.cliente_id.data if form.cliente_id.data else None, # None si no se seleccionó cliente
            direccion_entrega_id=form.direccion_entrega_id.data if form.direccion_entrega_id.data else None, # None si no se seleccionó dirección
            repartidor_id=repartidor_id_selected,
            forma_pago_value=form.forma_pago.data if form.forma_pago.data else None, # None si no se seleccionó forma de pago
            notas_pedido=form.notas_pedido.data,
            fecha_entrega_programada=form.fecha_entrega_programada.data,
            requiere_factura=form.requiere_factura.data
            # paga_con y cambio_entregado se manejan en el proceso de pago, no en la creación inicial
            # subtotales y total_pedido se calculan al añadir ítems
        )

        if nuevo_pedido:
            flash(f'Pedido #{format_pedido_folio(nuevo_pedido.id)} creado exitosamente.', 'success')
            # Redirigir a la vista de edición del pedido para añadir ítems
            return redirect(url_for('pedidos.editar_pedido', pedido_id=nuevo_pedido.id))
        else:
            # El servicio ya imprime un error detallado
            flash('Error al crear pedido. Por favor, verifica los datos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'pedidos/crear_pedido.html'
    return render_template('pedidos/crear_pedido.html', title='Crear Nuevo Pedido', form=form)


@pedidos.route('/<int:pedido_id>')
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles pueden ver detalles de pedidos relevantes
def ver_pedido(pedido_id):
    """
    Muestra los detalles de un pedido específico.
    La visibilidad de ciertos datos puede depender del rol.
    """
    pedido = get_pedido_by_id(pedido_id)

    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Lógica de autorización más granular:
    # - Admin/Cajero: Pueden ver cualquier pedido.
    # - Tablajero: Solo ve pedidos en estados de preparación.
    # - Repartidor: Solo ve pedidos asignados a él y en estados de entrega.
    # Si el usuario no es Admin/Cajero, verificar si el pedido es relevante para su rol
    if not (current_user.is_admin() or current_user.is_cajero()):
        is_relevant = False
        if current_user.is_tablajero() and pedido.estado_pedido in [EstadoPedido.PENDIENTE_PREPARACION, EstadoPedido.EN_PREPARACION]:
            is_relevant = True
        if current_user.is_repartidor() and pedido.repartidor_id == current_user.id and pedido.estado_pedido in [
            EstadoPedido.ASIGNADO_A_REPARTIDOR, EstadoPedido.EN_RUTA, EstadoPedido.ENTREGADO_PENDIENTE_PAGO,
            EstadoPedido.PROBLEMA_EN_ENTREGA, EstadoPedido.REPROGRAMADO
        ]:
            is_relevant = True

        if not is_relevant:
            flash('No tienes permiso para ver los detalles de este pedido.', 'danger')
            return redirect(url_for('pedidos.dashboard_pedidos'))


    # Necesitarás una plantilla 'pedidos/ver_pedido.html'
    return render_template(
        'pedidos/ver_pedido.html',
        title=f'Pedido #{format_pedido_folio(pedido.id)}',
        pedido=pedido,
        format_currency=format_currency,
        format_datetime=format_datetime,
        format_pedido_folio=format_pedido_folio,
        EstadoPedido=EstadoPedido, # Pasar Enum
        TipoVenta=TipoVenta, # Pasar Enum
        FormaPago=FormaPago # Pasar Enum
        # Puedes pasar formularios vacíos para añadir ítems/PAs si se usan modales en la vista
        # item_form=PedidoItemForm(),
        # pa_form=ProductoAdicionalForm()
    )


@pedidos.route('/<int:pedido_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden editar pedidos
def editar_pedido(pedido_id):
    """
    Permite editar los datos principales de un pedido existente y gestionar sus ítems/PAs.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Opcional: Validar si el usuario actual tiene permiso para editar este pedido en su estado actual
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser editado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = PedidoForm(obj=pedido) # Pre-llenar el formulario principal

    # Poblar choices dinámicos (Repartidores)
    repartidores = Usuario.query.filter_by(rol=RolUsuario.REPARTIDOR, activo=True).order_by(Usuario.nombre_completo).all()
    form.repartidor_id.choices = [(0, 'Seleccionar Repartidor')] + [(r.id, r.nombre_completo) for r in repartidores]

    # Si el pedido ya tiene un repartidor asignado, asegurarse de que esté seleccionado en el formulario
    if pedido.repartidor_id:
         form.repartidor_id.data = pedido.repartidor_id
    else:
         form.repartidor_id.data = 0 # Asegurar que el valor por defecto sea 0 si no hay repartidor

    # Pre-llenar campos de búsqueda de cliente/dirección si el pedido tiene cliente/direccion
    if pedido.cliente:
        form.cliente_id.data = pedido.cliente.id
        form.cliente_search.data = pedido.cliente.get_nombre_completo() # O alias
        # Si el cliente tiene múltiples direcciones, la UI necesitará cargar las opciones dinámicas
        # Para MVP, solo mostramos la dirección actual si existe
        if pedido.direccion_entrega:
             form.direccion_entrega_id.data = pedido.direccion_entrega.id
             form.direccion_entrega_search.data = f"{pedido.direccion_entrega.calle_numero}, {pedido.direccion_entrega.colonia}" # Formato simple


    # Formularios para añadir ítems/PAs (se pueden usar en la misma plantilla con modales o secciones)
    item_form = PedidoItemForm()
    pa_form = ProductoAdicionalForm()

    if form.validate_on_submit():
        # Convertir 0 de repartidor_id a None si no se seleccionó uno
        repartidor_id_selected = form.repartidor_id.data if form.repartidor_id.data != 0 else None

        updated_pedido = update_pedido(
            pedido_id=pedido.id,
            cliente_id=form.cliente_id.data if form.cliente_id.data else None,
            direccion_entrega_id=form.direccion_entrega_id.data if form.direccion_entrega_id.data else None,
            repartidor_id=repartidor_id_selected,
            tipo_venta_value=form.tipo_venta.data,
            forma_pago_value=form.forma_pago.data if form.forma_pago.data else None,
            paga_con=form.paga_con.data,
            # cambio_entregado se calcula en el servicio de pago
            descuento_aplicado=form.descuento_aplicado.data,
            costo_envio=form.costo_envio.data,
            estado_pedido_value=form.estado_pedido.data,
            notas_pedido=form.notas_pedido.data,
            fecha_entrega_programada=form.fecha_entrega_programada.data,
            requiere_factura=form.requiere_factura.data
        )

        if updated_pedido:
            flash(f'Pedido #{format_pedido_folio(updated_pedido.id)} actualizado exitosamente.', 'success')
            return redirect(url_for('pedidos.ver_pedido', pedido_id=updated_pedido.id))
        else:
            # El servicio ya imprime un error detallado
            flash('Error al actualizar pedido. Por favor, verifica los datos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'pedidos/editar_pedido.html'
    return render_template(
        'pedidos/editar_pedido.html',
        title=f'Editar Pedido #{format_pedido_folio(pedido.id)}',
        form=form,
        item_form=item_form, # Pasar formularios de ítems/PAs
        pa_form=pa_form,
        pedido=pedido, # Pasar el objeto pedido para mostrar ítems actuales, etc.
        format_currency=format_currency,
        format_datetime=format_datetime,
        format_pedido_folio=format_pedido_folio,
        EstadoPedido=EstadoPedido, # Pasar Enum
        TipoVenta=TipoVenta, # Pasar Enum
        FormaPago=FormaPago # Pasar Enum
    )


@pedidos.route('/<int:pedido_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede eliminar pedidos
def eliminar_pedido(pedido_id):
    """
    Elimina un pedido. Requiere método POST.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Opcional: Validar si el pedido puede ser eliminado según su estado
    # if pedido.estado_pedido not in [EstadoPedido.PENDIENTE_CONFIRMACION, EstadoPedido.CANCELADO_POR_CLIENTE, EstadoPedido.CANCELADO_POR_NEGOCIO]:
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser eliminado en estado {pedido.estado_pedido.value}. Considere cancelarlo.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


    success = delete_pedido(pedido_id)

    if success:
        flash(f'Pedido #{format_pedido_folio(pedido_id)} eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash(f'Error al eliminar pedido #{format_pedido_folio(pedido_id)}. Podría tener registros asociados que impiden la eliminación.', 'danger')

    return redirect(url_for('pedidos.dashboard_pedidos'))


# --- Rutas para PedidoItem (asociadas a un pedido) ---

@pedidos.route('/<int:pedido_id>/items/nuevo', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden añadir ítems
def add_item_to_pedido(pedido_id):
    """
    Añade un PedidoItem a un pedido existente. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Opcional: Validar si el pedido puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


    form = PedidoItemForm()
    # Nota: Los campos de búsqueda (producto_search, modificacion_search) no se validan aquí,
    # solo los hidden fields (producto_id, subproducto_id, modificacion_id)
    # La validación de existencia de IDs y aplicabilidad se hace en el servicio o en la validación del form.
    # Asegurarse de que el form.validate() incluya las validaciones personalizadas.

    if form.validate_on_submit():
        # Obtener el ID del usuario actual (para auditoría si se necesita en el servicio)
        usuario_id_accion = current_user.id

        nuevo_item = add_pedido_item(
            pedido_id=pedido.id,
            usuario_id=usuario_id_accion,
            producto_id=form.producto_id.data if form.producto_id.data else None,
            subproducto_id=form.subproducto_id.data if form.subproducto_id.data else None,
            modificacion_id=form.modificacion_id.data if form.modificacion_id.data else None,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario_venta=form.precio_unitario_venta.data, # Usar el precio del form (puede ser calculado en UI o manual)
            notas_item=form.notas_item.data
        )

        if nuevo_item:
            flash(f'Ítem "{nuevo_item.descripcion_item_venta}" añadido al pedido #{format_pedido_folio(pedido.id)}.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al añadir ítem al pedido. Por favor, verifica los datos.', 'danger')
            # Si la validación del form falla, los errores se adjuntan al form y se re-renderiza la página de edición
            # Si el servicio falla, se muestra el flash y se re-renderiza la página de edición

    # Redirigir siempre a la página de edición del pedido, incluso si falla la validación del form
    # Los errores del form se mostrarán en la plantilla si se renderiza con el form
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/items/<int:item_id>/editar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden editar ítems
def edit_pedido_item(item_id):
    """
    Edita un PedidoItem existente. Requiere método POST.
    Usado típicamente desde un modal o formulario en la página de edición de pedido.
    """
    item = get_pedido_item_by_id(item_id)
    if not item:
        flash('Ítem de pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos')) # Redirigir a dashboard si no se encuentra

    pedido = item.pedido # Obtener el pedido asociado

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


    form = PedidoItemForm(obj=item) # Pre-llenar el formulario con datos del ítem
    # Nota: Los campos de búsqueda (producto_search, modificacion_search) no se usan para editar,
    # solo se actualizan cantidad, unidad, precio, notas.
    # Deshabilitar o ocultar campos de producto/subproducto/modificación en la plantilla de edición de ítem.

    if form.validate_on_submit():
        updated_item = update_pedido_item(
            item_id=item.id,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario_venta=form.precio_unitario_venta.data,
            notas_item=form.notas_item.data
        )

        if updated_item:
            flash(f'Ítem "{updated_item.descripcion_item_venta}" actualizado en pedido #{format_pedido_folio(pedido.id)}.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al actualizar ítem del pedido. Por favor, verifica los datos.', 'danger')
            # Si la validación del form falla, los errores se adjuntan al form.
            # Si el servicio falla, se muestra el flash.

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/items/<int:item_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden eliminar ítems
def delete_pedido_item_route(item_id):
    """
    Elimina un PedidoItem. Requiere método POST.
    """
    item = get_pedido_item_by_id(item_id)
    if not item:
        flash('Ítem de pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos')) # Redirigir a dashboard si no se encuentra

    pedido = item.pedido # Obtener el pedido asociado

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


    success = delete_pedido_item(item_id)

    if success:
        flash(f'Ítem eliminado del pedido #{format_pedido_folio(pedido.id)}.', 'success')
    else:
        flash('Error al eliminar ítem del pedido.', 'danger') # El servicio ya imprime el error

    # Redirigir a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


# --- Rutas para ProductoAdicional (asociadas a un pedido) ---

@pedidos.route('/<int:pedido_id>/pas/nuevo', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden añadir PAs
def add_pa_to_pedido(pedido_id):
    """
    Añade un ProductoAdicional a un pedido existente. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    form = ProductoAdicionalForm()

    if form.validate_on_submit():
        nuevo_pa = add_producto_adicional(
            pedido_id=pedido.id,
            producto_id=form.producto_id.data if form.producto_id.data else None,
            subproducto_id=form.subproducto_id.data if form.subproducto_id.data else None,
            modificacion_id=form.modificacion_id.data if form.modificacion_id.data else None,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario=form.precio_unitario.data, # Usar el precio del form
            notas_pa=form.notas_pa.data
        )

        if nuevo_pa:
            flash(f'Producto Adicional "{nuevo_pa.descripcion_producto_adicional}" añadido al pedido #{format_pedido_folio(pedido.id)}.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al añadir producto adicional al pedido. Por favor, verifica los datos.', 'danger')

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/pas/<int:pa_id>/editar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden editar PAs
def edit_producto_adicional(pa_id):
    """
    Edita un ProductoAdicional existente. Requiere método POST.
    Usado típicamente desde un modal o formulario en la página de edición de pedido.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        flash('Producto adicional no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos')) # Redirigir a dashboard si no se encuentra

    pedido = pa.pedido # Obtener el pedido asociado

    form = ProductoAdicionalForm(obj=pa) # Pre-llenar el formulario con datos del PA

    if form.validate_on_submit():
        updated_pa = update_producto_adicional(
            pa_id=pa.id,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario=form.precio_unitario.data,
            notas_pa=form.notas_pa.data
        )

        if updated_pa:
            flash(f'Producto Adicional "{updated_pa.descripcion_producto_adicional}" actualizado en pedido #{format_pedido_folio(pedido.id)}.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al actualizar producto adicional del pedido. Por favor, verifica los datos.', 'danger')

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/pas/<int:pa_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden eliminar PAs
def delete_producto_adicional_route(pa_id):
    """
    Elimina un ProductoAdicional. Requiere método POST.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        flash('Producto adicional no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos')) # Redirigir a dashboard si no se encuentra

    pedido = pa.pedido # Obtener el pedido asociado

    success = delete_producto_adicional(pa_id)

    if success:
        flash(f'Producto Adicional eliminado del pedido #{format_pedido_folio(pedido.id)}.', 'success')
    else:
        flash('Error al eliminar producto adicional del pedido.', 'danger') # El servicio ya imprime el error

    # Redirigir a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


# --- Rutas para acciones masivas en pedidos (AJAX) ---

@pedidos.route('/ajax/pedidos/actualizar_estados', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede actualizar estados masivos
def ajax_actualizar_estados_pedidos():
    """
    Actualiza el estado de múltiples pedidos seleccionados. Requiere método POST.
    Usado típicamente para cambios masivos desde el dashboard.
    """
    data = request.get_json() # Obtener datos JSON de la petición AJAX

    if not data or 'pedido_ids' not in data or 'nuevo_estado' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400

    pedido_ids = data['pedido_ids']
    nuevo_estado = data['nuevo_estado']

    # Validar que al menos un ID de pedido sea válido
    pedidos_validos = [pid for pid in pedido_ids if get_pedido_by_id(pid) is not None]
    if not pedidos_validos:
        return jsonify({'success': False, 'message': 'No se encontraron pedidos válidos para actualizar.'}), 404

    # Lógica adicional de negocio puede ir aquí (ej. notificar a usuarios, registrar auditoría, etc.)

    # Actualizar estado masivamente
    for pedido_id in pedidos_validos:
        update_pedido_status(pedido_id, nuevo_estado)

    return jsonify({'success': True, 'message': f'Estados de {len(pedidos_validos)} pedidos actualizados a "{nuevo_estado}".'}), 200


@pedidos.route('/ajax/pedidos/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede eliminar pedidos masivamente
def ajax_eliminar_pedidos():
    """
    Elimina múltiples pedidos seleccionados. Requiere método POST.
    Usado típicamente para eliminaciones masivas desde el dashboard.
    """
    data = request.get_json() # Obtener datos JSON de la petición AJAX

    if not data or 'pedido_ids' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400

    pedido_ids = data['pedido_ids']

    # Validar que al menos un ID de pedido sea válido
    pedidos_validos = [pid for pid in pedido_ids if get_pedido_by_id(pid) is not None]
    if not pedidos_validos:
        return jsonify({'success': False, 'message': 'No se encontraron pedidos válidos para eliminar.'}), 404

    # Eliminar pedidos válidos
    for pedido_id in pedidos_validos:
        delete_pedido(pedido_id)

    return jsonify({'success': True, 'message': f'{len(pedidos_validos)} pedidos eliminados.'}), 200


# --- Rutas para reportes y estadísticas (AJAX) ---

@pedidos.route('/ajax/reportes/pedidos_estadisticas', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede acceder a estadísticas masivas
def ajax_reportes_pedidos_estadisticas():
    """
    Genera estadísticas sobre pedidos (totales, por estado, por usuario, etc.).
    Requiere método POST.
    Usado típicamente para generar reportes en el dashboard.
    """
    data = request.get_json() # Obtener datos JSON de la petición AJAX

    if not data or 'rango_fechas' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400

    rango_fechas = data['rango_fechas']

    # Lógica para generar estadísticas
    # Ejemplo: contar pedidos por estado en el rango de fechas
    estadisticas = {}
    try:
        pedidos_filtrados = Pedido.query.filter(Pedido.fecha_creacion >= rango_fechas['desde'], Pedido.fecha_creacion <= rango_fechas['hasta']).all()
        for pedido in pedidos_filtrados:
            estado = pedido.estado_pedido
            if estado not in estadisticas:
                estadisticas[estado] = 0
            estadisticas[estado] += 1
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({'success': True, 'data': estadisticas}), 200


@pedidos.route('/ajax/reportes/pedidos_detalle', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede acceder a detalles masivos
def ajax_reportes_pedidos_detalle():
    """
    Genera un reporte detallado de pedidos (con ítems y PAs).
    Requiere método POST.
    Usado típicamente para generar reportes descargables (CSV, Excel, etc.).
    """
    data = request.get_json() # Obtener datos JSON de la petición AJAX

    if not data or 'pedido_ids' not in data:
        return jsonify({'success': False, 'message': 'Datos inválidos.'}), 400

    pedido_ids = data['pedido_ids']

    # Validar que al menos un ID de pedido sea válido
    pedidos_validos = [pid for pid in pedido_ids if get_pedido_by_id(pid) is not None]
    if not pedidos_validos:
        return jsonify({'success': False, 'message': 'No se encontraron pedidos válidos para generar reporte.'}), 404

    # Lógica para generar reporte detallado
    # Ejemplo: crear un CSV en memoria con los detalles de los pedidos
    try:
        import pandas as pd
        from io import BytesIO

        # Obtener datos de los pedidos válidos
        pedidos_data = Pedido.query.filter(Pedido.id.in_(pedidos_validos)).options(
            joinedload(Pedido.items),
            joinedload(Pedido.productos_adicionales)
        ).all()

        # Crear un DataFrame por cada pedido con sus ítems y PAs
        dfs = []
        for pedido in pedidos_data:
            df_items = pd.DataFrame([{
                'Producto': item.producto.nombre,
                'Cantidad': item.cantidad,
                'Precio Unitario': item.precio_unitario_venta,
                'Subtotal': item.subtotal
            } for item in pedido.items])

            df_pas = pd.DataFrame([{
                'Producto Adicional': pa.producto.nombre,
                'Cantidad': pa.cantidad,
                'Precio Unitario': pa.precio_unitario,
                'Subtotal': pa.subtotal
            } for pa in pedido.productos_adicionales])

            # Combinar ítems y PAs en un solo DataFrame
            df_pedido = pd.concat([df_items, df_pas], axis=0, ignore_index=True)
            df_pedido['Pedido ID'] = pedido.id
            dfs.append(df_pedido)

        # Concatenar todos los DataFrames de pedidos en uno solo
        df_final = pd.concat(dfs, axis=0, ignore_index=True)

        # Guardar como archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name='Pedidos', index=False)
            # Formato opcional: ajustar ancho de columnas, formato de celdas, etc.
            workbook = writer.book
            worksheet = writer.sheets['Pedidos']
            worksheet.set_column('A:A', 30) # Ancho columna Producto
            worksheet.set_column('B:B', 10) # Ancho columna Cantidad
            worksheet.set_column('C:C', 15) # Ancho columna Precio Unitario
            worksheet.set_column('D:D', 10) # Ancho columna Subtotal
            worksheet.set_column('E:E', 30) # Ancho columna Producto Adicional
            worksheet.set_column('F:F', 10) # Ancho columna Cantidad PA
            worksheet.set_column('G:G', 15) # Ancho columna Precio Unitario PA
            worksheet.set_column('H:H', 10) # Ancho columna Subtotal PA
            # Formato de moneda para columnas de precio y subtotal
            currency_format = workbook.add_format({'num_format': '$#,##0.00'})
            worksheet.set_column('C:D', None, currency_format)
            worksheet.set_column('G:H', None, currency_format)

        output.seek(0)
        return send_file(output, attachment_filename='reporte_pedidos.xlsx', as_attachment=True)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    return jsonify({'success': True, 'data': 'Reporte generado exitosamente.'}), 200
