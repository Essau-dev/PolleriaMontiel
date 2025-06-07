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

    # CORRECCIÓN: Renderizar la plantilla de listado correcta
    return render_template(
        'pedidos/listar_pedidos.html', # Cambiado de 'pedidos/dashboard_pedidos.html'
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
    # Llenar selectores dinámicos si es necesario (ej. clientes, repartidores)
    # form.cliente_id.choices = [(c.id, c.get_nombre_completo()) for c in get_all_clients()] # Ejemplo
    # form.repartidor_id.choices = [(u.id, u.nombre_completo) for u in get_users_by_role(RolUsuario.REPARTIDOR)] # Ejemplo

    if form.validate_on_submit():
        # Usar servicio para crear pedido
        nuevo_pedido = create_pedido(
            cliente_id=form.cliente_id.data,
            usuario_id=current_user.id, # El usuario logueado es el creador
            repartidor_id=form.repartidor_id.data,
            direccion_entrega_id=form.direccion_entrega_id.data,
            tipo_venta=form.tipo_venta.data,
            forma_pago=form.forma_pago.data,
            paga_con=form.paga_con.data,
            cambio_entregado=form.cambio_entregado.data,
            costo_envio=form.costo_envio.data,
            notas_pedido=form.notas_pedido.data,
            fecha_entrega_programada=form.fecha_entrega_programada.data,
            requiere_factura=form.requiere_factura.data
            # Los subtotales y total_pedido se calcularán en el servicio o al añadir ítems
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
    Muestra los detalles completos de un pedido específico.
    La visibilidad puede estar restringida por rol.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Lógica de autorización para ver el pedido:
    # Admin y Cajero pueden ver cualquier pedido.
    # Tablajero solo ve pedidos en estado PENDIENTE_PREPARACION o EN_PREPARACION.
    # Repartidor solo ve pedidos asignados a él y en estados de entrega.
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
    Permite editar un pedido existente.
    La capacidad de edición puede estar limitada por el estado del pedido y el rol.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Opcional: Validar si el pedido puede ser modificado por el usuario actual
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = PedidoForm(obj=pedido) # Pre-llenar formulario con datos del pedido
    # Llenar selectores dinámicos si es necesario (ej. clientes, repartidores)
    # form.cliente_id.choices = [(c.id, c.get_nombre_completo()) for c in get_all_clients()] # Ejemplo
    # form.repartidor_id.choices = [(u.id, u.nombre_completo) for u in get_users_by_role(RolUsuario.REPARTIDOR)] # Ejemplo

    if form.validate_on_submit():
        # Usar servicio para actualizar pedido
        updated_pedido = update_pedido(
            pedido_id=pedido.id,
            cliente_id=form.cliente_id.data,
            repartidor_id=form.repartidor_id.data,
            direccion_entrega_id=form.direccion_entrega_id.data,
            tipo_venta=form.tipo_venta.data,
            forma_pago=form.forma_pago.data,
            paga_con=form.paga_con.data,
            cambio_entregado=form.cambio_entregado.data,
            costo_envio=form.costo_envio.data,
            notas_pedido=form.notas_pedido.data,
            fecha_entrega_programada=form.fecha_entrega_programada.data,
            requiere_factura=form.requiere_factura.data
            # Los subtotales y total_pedido se recalcularán en el servicio o al guardar
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
        pedido=pedido, # Pasar el objeto pedido para acceder a sus relaciones (ítems, PAs)
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


@pedidos.route('/<int:pedido_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede eliminar pedidos
def eliminar_pedido(pedido_id):
    """
    Elimina un pedido. Requiere método POST.
    Solo permitido para Administradores y posiblemente restringido por estado.
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
        flash(f'Pedido #{format_pedido_folio(pedido.id)} eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado
        flash(f'Error al eliminar pedido #{format_pedido_folio(pedido.id)}.', 'danger')

    # Redirigir a la lista de pedidos
    return redirect(url_for('pedidos.dashboard_pedidos'))


@pedidos.route('/<int:pedido_id>/cambiar_estado', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles pueden cambiar estados relevantes para ellos
def cambiar_estado_pedido(pedido_id):
    """
    Cambia el estado de un pedido. Requiere método POST.
    La lógica de qué estados son permitidos para cada rol/estado actual
    se maneja en el servicio o aquí antes de llamar al servicio.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    new_estado_value = request.form.get('new_estado')
    if not new_estado_value:
        flash('Estado no especificado.', 'warning')
        return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    try:
        # Convertir el valor string a miembro del Enum EstadoPedido
        new_estado = EstadoPedido[new_estado_value]
        current_estado = pedido.estado_pedido

        # Lógica de autorización y transición de estado:
        # Solo Admin puede cambiar a cualquier estado.
        # Cajero: PENDIENTE_PREPARACION -> EN_PREPARACION, LISTO_PARA_ENTREGA, ASIGNADO_A_REPARTIDOR, CANCELADO_POR_NEGOCIO (si no ha salido)
        # Tablajero: PENDIENTE_PREPARACION -> EN_PREPARACION, EN_PREPARACION -> LISTO_PARA_ENTREGA
        # Repartidor: ASIGNADO_A_REPARTIDOR -> EN_RUTA, EN_RUTA -> ENTREGADO_PENDIENTE_PAGO/PROBLEMA_EN_ENTREGA, ENTREGADO_PENDIENTE_PAGO -> PAGADO
        # Esta lógica detallada se implementaría aquí o en el servicio update_pedido_status
        # Para MVP, asumimos que el servicio valida las transiciones permitidas por rol y estado actual.

        # if not current_user.is_admin():
        #     # Validar transiciones permitidas para roles no-Admin
        #     is_transition_allowed = False
        #     if current_user.is_cajero():
        #         # Lógica de transiciones para Cajero
        #         pass # Implementar aquí
        #     elif current_user.is_tablajero():
        #          # Lógica de transiciones para Tablajero
        #          pass # Implementar aquí
        #     elif current_user.is_repartidor():
        #          # Lógica de transiciones para Repartidor
        #          pass # Implementar aquí
        #
        #     if not is_transition_allowed:
        #         flash(f'No tienes permiso para cambiar el estado del pedido #{format_pedido_folio(pedido.id)} de "{current_estado.value}" a "{new_estado_value}".', 'danger')
        #         return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

        # Si la transición es permitida por rol, llamar al servicio
        updated_pedido = update_pedido_status(pedido.id, new_estado)

        if updated_pedido:
            flash(f'Estado del pedido #{format_pedido_folio(updated_pedido.id)} actualizado a "{updated_pedido.estado_pedido.name.replace("_", " ").title()}".', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash(f'Error al actualizar el estado del pedido #{format_pedido_folio(pedido.id)}.', 'danger')

    except ValueError:
        # Si new_estado_value no es un miembro válido del Enum EstadoPedido
        flash(f'Estado de pedido "{new_estado_value}" no válido.', 'danger')
    except Exception as e:
        flash(f'Error inesperado al cambiar el estado del pedido: {e}', 'danger')


    # Redirigir a la vista del pedido
    return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


@pedidos.route('/<int:pedido_id>/pagar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden procesar pagos
def process_payment_route(pedido_id):
    """
    Muestra formulario para procesar el pago de un pedido (principalmente efectivo)
    o procesa el POST del formulario.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Validar que el pedido esté en un estado que permita el pago
    # if pedido.estado_pedido not in [EstadoPedido.LISTO_PARA_ENTREGA, EstadoPedido.ENTREGADO_PENDIENTE_PAGO]:
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no está en un estado que permita el pago ({pedido.estado_pedido.value}).', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = PaymentForm() # Necesitarás crear este formulario (monto, forma_pago, paga_con, denominaciones)

    if form.validate_on_submit():
        # Usar servicio para procesar el pago
        # El servicio debe manejar la creación del MovimientoCaja y la actualización del estado del pedido
        success = process_pedido_payment(
            pedido_id=pedido.id,
            monto_recibido=form.monto_recibido.data, # O total_pedido si se paga exacto
            forma_pago=form.forma_pago.data,
            paga_con=form.paga_con.data, # Solo si forma_pago es EFECTIVO
            denominaciones_recibidas=form.denominaciones_recibidas.data # Solo si forma_pago es EFECTIVO
        )

        if success:
            flash(f'Pago del pedido #{format_pedido_folio(pedido.id)} procesado exitosamente.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash(f'Error al procesar el pago del pedido #{format_pedido_folio(pedido.id)}. Por favor, verifica los datos.', 'danger')

        return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    # Si es GET, podrías mostrar una página de pago o un modal
    # Para MVP, simplemente redirigimos a la vista del pedido con un mensaje si se accede por GET
    flash('Acceso no permitido. Utiliza el formulario de pago en la vista del pedido.', 'warning')
    return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


@pedidos.route('/<int:pedido_id>/liquidar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PEDIDOS_ENTREGA) # Repartidor, Cajero, Admin pueden liquidar
def process_liquidacion_route(pedido_id):
    """
    Muestra formulario para que el repartidor liquide un pedido a domicilio
    o procesa el POST del formulario.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Validar que el pedido sea a domicilio y esté en un estado liquidable
    liquidable_states = [
        EstadoPedido.ASIGNADO_A_REPARTIDOR,
        EstadoPedido.EN_RUTA,
        EstadoPedido.ENTREGADO_PENDIENTE_PAGO,
        EstadoPedido.PROBLEMA_EN_ENTREGA,
        EstadoPedido.REPROGRAMADO
    ]
    if pedido.tipo_venta != TipoVenta.DOMICILIO or pedido.estado_pedido not in liquidable_states:
         flash(f'El pedido #{format_pedido_folio(pedido.id)} no es a domicilio o no está en un estado liquidable ({pedido.estado_pedido.value}).', 'warning')
         return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = LiquidacionForm() # Necesitarás crear este formulario (monto_recibido, denominaciones)

    if form.validate_on_submit():
        # Usar servicio para procesar la liquidación
        # El servicio debe manejar la creación del MovimientoCaja y la actualización del estado del pedido
        updated_pedido = process_repartidor_liquidacion(
            pedido_id=pedido.id,
            usuario_liquida_id=current_user.id, # El usuario logueado es quien liquida
            monto_recibido_efectivo=form.monto_recibido_efectivo.data,
            denominaciones_recibidas=form.denominaciones_recibidas.data
        )

        if updated_pedido:
            flash(f'Liquidación del pedido #{format_pedido_folio(updated_pedido.id)} procesada exitosamente.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash(f'Error al procesar la liquidación del pedido #{format_pedido_folio(pedido.id)}. Por favor, verifica los datos.', 'danger')

        return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    # Si es GET, podrías mostrar una página de liquidación o un modal
    # Para MVP, simplemente redirigimos a la vista del pedido con un mensaje si se accede por GET
    flash('Acceso no permitido. Utiliza el formulario de liquidación en la vista del pedido.', 'warning')
    return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


# --- Rutas para Ítems de Pedido (usadas típicamente con AJAX o POST desde formulario de edición) ---

@pedidos.route('/<int:pedido_id>/items/nuevo', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden añadir ítems
def add_item_to_pedido(pedido_id):
    """
    Añade un nuevo PedidoItem a un pedido existente.
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
    # se usarían en el frontend para obtener los IDs (producto_id, subproducto_id, modificacion_id)
    # que sí se validan en el formulario y/o servicio.

    if form.validate_on_submit():
        # Usar servicio para añadir ítem
        nuevo_item = add_pedido_item(
            pedido_id=pedido.id,
            producto_id=form.producto_id.data,
            subproducto_id=form.subproducto_id.data,
            modificacion_id=form.modificacion_id.data,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario_venta=form.precio_unitario_venta.data, # Puede venir del form o ser calculado en servicio
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
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/items/<int:item_id>/editar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden editar ítems
def edit_pedido_item(item_id):
    """
    Edita un PedidoItem existente. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
    """
    item = get_pedido_item_by_id(item_id)
    if not item:
        flash('Ítem de pedido no encontrado.', 'warning')
        # Redirigir a dashboard o a la vista del pedido si se conoce
        return redirect(url_for('pedidos.dashboard_pedidos'))

    pedido = item.pedido # Obtener el pedido asociado

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = PedidoItemForm(obj=item) # Pre-llenar formulario con datos del ítem

    if form.validate_on_submit():
        # Usar servicio para actualizar ítem
        updated_item = update_pedido_item(
            item_id=item.id,
            cantidad=form.cantidad.data,
            unidad_medida=form.unidad_medida.data,
            precio_unitario_venta=form.precio_unitario_venta.data, # Puede venir del form o ser calculado en servicio
            notas_item=form.notas_item.data
            # Nota: No se permite cambiar producto/subproducto/modificacion en la edición simple
        )

        if updated_item:
            flash(f'Ítem "{updated_item.descripcion_item_venta}" del pedido #{format_pedido_folio(pedido.id)} actualizado.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al actualizar ítem del pedido. Por favor, verifica los datos.', 'danger')
            # Si la validación del form falla, los errores se adjuntan al form y se re-renderiza la página de edición
            # Si el servicio falla, se muestra el flash y se re-renderiza la página de edición

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/items/<int:item_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden eliminar ítems
def delete_pedido_item_route(item_id):
    """
    Elimina un PedidoItem. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
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
        # El servicio ya imprime un error detallado
        flash('Error al eliminar ítem del pedido.', 'danger')

    # Redirigir a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


# --- Rutas para Productos Adicionales (usadas típicamente con AJAX o POST desde formulario de edición) ---

@pedidos.route('/<int:pedido_id>/pas/nuevo', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden añadir PAs
def add_producto_adicional_to_pedido(pedido_id):
    """
    Añade un nuevo ProductoAdicional a un pedido existente.
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

    form = ProductoAdicionalForm()

    if form.validate_on_submit():
        # Usar servicio para añadir PA
        nuevo_pa = add_producto_adicional(
            pedido_id=pedido.id,
            nombre_pa=form.nombre_pa.data,
            cantidad_pa=form.cantidad_pa.data,
            unidad_medida_pa=form.unidad_medida_pa.data,
            costo_compra_unitario_pa=form.costo_compra_unitario_pa.data,
            precio_venta_unitario_pa=form.precio_venta_unitario_pa.data, # Puede venir del form o ser calculado en servicio
            notas_pa=form.notas_pa.data
        )

        if nuevo_pa:
            flash(f'Producto Adicional "{nuevo_pa.nombre_pa}" añadido al pedido #{format_pedido_folio(pedido.id)}.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al añadir Producto Adicional al pedido. Por favor, verifica los datos.', 'danger')
            # Si la validación del form falla, los errores se adjuntan al form y se re-renderiza la página de edición
            # Si el servicio falla, se muestra el flash y se re-renderiza la página de edición

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/pas/<int:pa_id>/editar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden editar PAs
def edit_producto_adicional(pa_id):
    """
    Edita un ProductoAdicional existente. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        flash('Producto Adicional no encontrado.', 'warning')
        # Redirigir a dashboard o a la vista del pedido si se conoce
        return redirect(url_for('pedidos.dashboard_pedidos'))

    pedido = pa.pedido # Obtener el pedido asociado

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    form = ProductoAdicionalForm(obj=pa) # Pre-llenar formulario con datos del PA

    if form.validate_on_submit():
        # Usar servicio para actualizar PA
        updated_pa = update_producto_adicional(
            pa_id=pa.id,
            nombre_pa=form.nombre_pa.data,
            cantidad_pa=form.cantidad_pa.data,
            unidad_medida_pa=form.unidad_medida_pa.data,
            costo_compra_unitario_pa=form.costo_compra_unitario_pa.data,
            precio_venta_unitario_pa=form.precio_venta_unitario_pa.data, # Puede venir del form o ser calculado en servicio
            notas_pa=form.notas_pa.data
        )

        if updated_pa:
            flash(f'Producto Adicional "{updated_pa.nombre_pa}" del pedido #{format_pedido_folio(pedido.id)} actualizado.', 'success')
        else:
            # El servicio ya imprime un error detallado
            flash('Error al actualizar Producto Adicional del pedido. Por favor, verifica los datos.', 'danger')
            # Si la validación del form falla, los errores se adjuntan al form y se re-renderiza la página de edición
            # Si el servicio falla, se muestra el flash y se re-renderiza la página de edición

    # Redirigir siempre a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


@pedidos.route('/pas/<int:pa_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden eliminar PAs
def delete_producto_adicional_route(pa_id):
    """
    Elimina un ProductoAdicional. Requiere método POST.
    Usado típicamente desde el formulario de edición de pedido.
    """
    pa = get_producto_adicional_by_id(pa_id)
    if not pa:
        flash('Producto Adicional no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos')) # Redirigir a dashboard si no se encuentra

    pedido = pa.pedido # Obtener el pedido asociado

    # Opcional: Validar si el pedido asociado puede ser modificado
    # if not current_user.is_admin() and not pedido.puede_ser_modificado():
    #      flash(f'El pedido #{format_pedido_folio(pedido.id)} no puede ser modificado en estado {pedido.estado_pedido.value}.', 'warning')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))


    success = delete_producto_adicional(pa_id)

    if success:
        flash(f'Producto Adicional eliminado del pedido #{format_pedido_folio(pedido.id)}.', 'success')
    else:
        # El servicio ya imprime un error detallado
        flash('Error al eliminar Producto Adicional del pedido.', 'danger')

    # Redirigir a la página de edición del pedido
    return redirect(url_for('pedidos.editar_pedido', pedido_id=pedido.id))


# --- Rutas AJAX para funcionalidades dinámicas en formularios de Pedido ---

@pedidos.route('/ajax/clientes/buscar', methods=['GET'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden buscar clientes para pedidos
def ajax_buscar_clientes():
    """
    Endpoint AJAX para buscar clientes por nombre, alias o teléfono.
    Usado en el formulario de pedido para autocompletado.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Usar el servicio de búsqueda de clientes
    # Limitar resultados para no sobrecargar
    clientes_encontrados = search_clients(query, page=1, per_page=10).items

    # Formatear resultados para el frontend (ej. Select2, datalist)
    results = []
    for cliente in clientes_encontrados:
        results.append({
            'id': cliente.id,
            'text': f"{cliente.get_nombre_completo()} ({cliente.alias or 'N/A'}) - {cliente.get_telefono_principal().numero_telefono if cliente.get_telefono_principal() else 'Sin Teléfono'}",
            'nombre': cliente.nombre,
            'apellidos': cliente.apellidos,
            'alias': cliente.alias,
            'tipo_cliente': cliente.tipo_cliente.value, # Pasar el valor del Enum
            'telefonos': [{'id': t.id, 'numero': t.numero_telefono, 'tipo': t.tipo_telefono.value, 'principal': t.es_principal} for t in cliente.telefonos],
            'direcciones': [{'id': d.id, 'calle_numero': d.calle_numero, 'colonia': d.colonia, 'ciudad': d.ciudad, 'cp': d.codigo_postal, 'referencias': d.referencias, 'tipo': d.tipo_direccion.value, 'principal': d.es_principal} for d in cliente.direcciones]
        })

    return jsonify(results)


@pedidos.route('/ajax/clientes/<int:client_id>/direcciones', methods=['GET'])
@login_required
@role_required(ROLES_PEDIDOS_RW) # Cajero y Admin pueden obtener direcciones de clientes para pedidos
def ajax_get_direcciones_cliente(client_id):
    """
    Endpoint AJAX para obtener las direcciones de un cliente específico.
    Usado en el formulario de pedido a domicilio para llenar el selector de dirección.
    """
    cliente = get_client_by_id(client_id)
    if not cliente:
        return jsonify([]), 404

    direcciones = cliente.direcciones.all() # Obtener todas las direcciones del cliente

    results = []
    for direccion in direcciones:
        results.append({
            'id': direccion.id,
            'text': f"{direccion.calle_numero}, {direccion.colonia or ''}, {direccion.ciudad} (Principal: {'Sí' if direccion.es_principal else 'No'})",
            'calle_numero': direccion.calle_numero,
            'colonia': direccion.colonia,
            'ciudad': direccion.ciudad,
            'cp': direccion.codigo_postal,
            'referencias': direccion.referencias,
            'tipo': direccion.tipo_direccion.value,
            'principal': direccion.es_principal
        })

    return jsonify(results)


@pedidos.route('/ajax/productos/buscar', methods=['GET'])
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles que toman pedidos pueden buscar productos
def ajax_buscar_productos():
    """
    Endpoint AJAX para buscar productos/subproductos por código o nombre.
    Usado en el formulario de PedidoItem para autocompletado.
    """
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Usar servicios para buscar productos y subproductos activos
    productos_encontrados = search_productos(query, page=1, per_page=10, include_inactive=False).items
    subproductos_encontrados = search_subproductos(query, page=1, per_page=10, include_inactive=False).items

    results = []
    for prod in productos_encontrados:
        results.append({
            'id': f'prod_{prod.id}', # Prefijo para distinguir entre producto y subproducto
            'text': f"{prod.nombre} ({prod.id})",
            'type': 'producto',
            'codigo': prod.id,
            'nombre': prod.nombre
        })
    for subprod in subproductos_encontrados:
         results.append({
            'id': f'subprod_{subprod.id}', # Prefijo para distinguir
            'text': f"{subprod.nombre} ({subprod.codigo_subprod})",
            'type': 'subproducto',
            'codigo': subprod.codigo_subprod,
            'nombre': subprod.nombre,
            'producto_padre_id': subprod.producto_padre_id
        })

    # Opcional: Ordenar resultados por relevancia o alfabéticamente
    return jsonify(results)


@pedidos.route('/ajax/productos/<string:item_type>/<item_id>/modificaciones', methods=['GET'])
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles que toman pedidos pueden ver modificaciones
def ajax_get_modificaciones_aplicables(item_type, item_id):
    """
    Endpoint AJAX para obtener las modificaciones aplicables a un producto o subproducto.
    Usado en el formulario de PedidoItem para llenar el selector de modificación.
    """
    modificaciones = []
    if item_type == 'producto':
        producto = get_producto_by_id(item_id)
        if producto:
            # Obtener modificaciones asociadas directamente al producto
            modificaciones.extend(producto.modificaciones_directas.filter_by(activo=True).all())
            # Opcional: Incluir modificaciones comunes si aplica
            # modificaciones.extend(get_common_modifications())
    elif item_type == 'subproducto':
        subproducto = get_subproducto_by_id(item_id)
        if subproducto:
            # Obtener modificaciones asociadas al subproducto
            modificaciones.extend(subproducto.modificaciones_aplicables.filter_by(activo=True).all())
             # Opcional: Incluir modificaciones comunes si aplica
            # modificaciones.extend(get_common_modifications())

    # Eliminar duplicados si se incluyeron modificaciones comunes
    modificaciones_unicas = list({m.id: m for m in modificaciones}.values())

    results = []
    for mod in modificaciones_unicas:
        results.append({
            'id': mod.id,
            'text': f"{mod.nombre} ({mod.codigo_modif})",
            'codigo': mod.codigo_modif,
            'nombre': mod.nombre
        })

    return jsonify(results)


@pedidos.route('/ajax/precios/aplicable', methods=['GET'])
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles que toman pedidos pueden obtener precios
def ajax_get_precio_aplicable():
    """
    Endpoint AJAX para obtener el precio aplicable de un producto/subproducto
    para un cliente y cantidad dados.
    Usado en el formulario de PedidoItem para calcular el precio unitario.
    """
    item_type = request.args.get('item_type') # 'producto' o 'subproducto'
    item_id = request.args.get('item_id')
    cliente_id = request.args.get('cliente_id', type=int) # Puede ser None para mostrador
    cantidad = request.args.get('cantidad', type=Decimal) # Usar Decimal para precisión

    if not item_type or not item_id or cantidad is None:
        return jsonify({'error': 'Parámetros incompletos.'}), 400

    try:
        # Usar la función de lógica de negocio para obtener el precio
        precio_aplicable = _get_precio_aplicable(
            producto_id=item_id if item_type == 'producto' else None,
            subproducto_id=item_id if item_type == 'subproducto' else None,
            cliente_id=cliente_id,
            cantidad_solicitada=cantidad
        )

        if precio_aplicable is not None:
            return jsonify({'success': True, 'precio_kg': str(precio_aplicable)}) # Convertir Decimal a string para JSON
        else:
            return jsonify({'success': False, 'message': 'Precio no encontrado para esta combinación.'}), 404

    except Exception as e:
        # Loggear el error en el servidor
        print(f"Error en ajax_get_precio_aplicable: {e}")
        return jsonify({'success': False, 'message': 'Error interno al obtener precio.'}), 500


# --- Rutas AJAX para reportes (Opcional para MVP, si se implementan reportes dinámicos) ---

@pedidos.route('/ajax/reportes/pedidos_estadisticas', methods=['POST'])
@login_required
@role_required(ROLES_PEDIDOS_ADMIN) # Solo Admin puede acceder a estadísticas masivas
def ajax_reportes_pedidos_estadisticas():
    """
    Endpoint AJAX para generar estadísticas de pedidos en un rango de fechas.
    """
    data = request.get_json()
    fecha_desde_str = data.get('fecha_desde')
    fecha_hasta_str = data.get('fecha_hasta')

    # Validar y parsear fechas
    try:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d') if fecha_desde_str else None
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d') if fecha_hasta_str else None
        if fecha_hasta: # Incluir todo el día hasta las 23:59:59
             fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59)

        rango_fechas = {'desde': fecha_desde, 'hasta': fecha_hasta}

        # Lógica para obtener estadísticas (ej. conteo por estado, total ventas por tipo venta)
        # Esto requeriría funciones en services.py
        estadisticas = {} # Diccionario con los resultados
        # Ejemplo simple: conteo por estado
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
    Endpoint AJAX para generar un reporte detallado de pedidos en un rango de fechas.
    Podría retornar un archivo (CSV, Excel) o datos JSON.
    """
    data = request.get_json()
    fecha_desde_str = data.get('fecha_desde')
    fecha_hasta_str = data.get('fecha_hasta')

    # Validar y parsear fechas
    try:
        fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d') if fecha_desde_str else None
        fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d') if fecha_hasta_str else None
        if fecha_hasta: # Incluir todo el día hasta las 23:59:59
             fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59)

        rango_fechas = {'desde': fecha_desde, 'hasta': fecha_hasta}

        # Obtener IDs de pedidos que cumplen el rango de fechas
        pedidos_validos = [p.id for p in Pedido.query.filter(Pedido.fecha_creacion >= rango_fechas['desde'], Pedido.fecha_creacion <= rango_fechas['hasta']).all()]

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    if not pedidos_validos:
        return jsonify({'success': False, 'message': 'No se encontraron pedidos válidos para generar reporte.'}), 404

    # Lógica para generar reporte detallado
    # Ejemplo: crear un CSV en memoria con los detalles de los pedidos
    try:
        # Requiere la librería pandas y openpyxl (pip install pandas openpyxl)
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
            items_list = []
            for item in pedido.items:
                items_list.append({
                    'Pedido ID': pedido.id,
                    'Folio Pedido': format_pedido_folio(pedido.id),
                    'Fecha Creacion': format_datetime(pedido.fecha_creacion),
                    'Estado': pedido.estado_pedido.value,
                    'Tipo Venta': pedido.tipo_venta.value,
                    'Cliente': pedido.cliente.get_nombre_completo() if pedido.cliente else 'Mostrador',
                    'Tipo Item': 'Pollo',
                    'Descripcion Item': item.descripcion_item_venta,
                    'Cantidad': item.cantidad,
                    'Unidad Medida': item.unidad_medida,
                    'Precio Unitario Venta': item.precio_unitario_venta,
                    'Subtotal Item': item.subtotal_item,
                    'Notas Item': item.notas_item,
                    'Costo Compra Unitario': item.costo_unitario_item, # Puede ser None
                    'Comision Calculada': None # No aplica a items de pollo
                })
            for pa in pedido.productos_adicionales_pedido:
                 items_list.append({
                    'Pedido ID': pedido.id,
                    'Folio Pedido': format_pedido_folio(pedido.id),
                    'Fecha Creacion': format_datetime(pedido.fecha_creacion),
                    'Estado': pedido.estado_pedido.value,
                    'Tipo Venta': pedido.tipo_venta.value,
                    'Cliente': pedido.cliente.get_nombre_completo() if pedido.cliente else 'Mostrador',
                    'Tipo Item': 'Adicional',
                    'Descripcion Item': pa.nombre_pa,
                    'Cantidad': pa.cantidad_pa,
                    'Unidad Medida': pa.unidad_medida_pa,
                    'Precio Unitario Venta': pa.precio_venta_unitario_pa,
                    'Subtotal Item': pa.subtotal_pa,
                    'Notas Item': pa.notas_pa,
                    'Costo Compra Unitario': pa.costo_compra_unitario_pa, # Puede ser None
                    'Comision Calculada': pa.comision_calculada_pa # Puede ser None
                })
            if items_list:
                dfs.append(pd.DataFrame(items_list))

        if not dfs:
            return jsonify({'success': False, 'message': 'No hay datos de ítems para el rango de fechas.'}), 404

        # Concatenar todos los DataFrames
        reporte_df = pd.concat(dfs, ignore_index=True)

        # Generar archivo Excel en memoria
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        reporte_df.to_excel(writer, index=False, sheet_name='Detalle Pedidos')
        writer.close() # Usar close() en lugar de save() en versiones recientes de pandas/openpyxl

        # Configurar respuesta para descargar archivo
        # from flask import send_file # Asegurarse de importar send_file

        # return send_file(output, download_name='reporte_pedidos.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        # Nota: send_file requiere que el contexto de la aplicación esté activo.
        # Para AJAX, a veces es más simple retornar un enlace a otra ruta que sirva el archivo.
        # Para MVP, podemos simplificar y solo retornar éxito o error.
        # Si se quiere servir el archivo directamente desde AJAX POST, puede requerir ajustes.

        # Para MVP, solo retornamos éxito si el DataFrame se creó
        return jsonify({'success': True, 'message': f'Reporte generado con {len(reporte_df)} filas.'}), 200

    except ImportError:
        return jsonify({'success': False, 'message': 'Librerías de reporte (pandas, openpyxl) no instaladas.'}), 500
    except Exception as e:
        # Loggear el error en el servidor
        print(f"Error al generar reporte detallado: {e}")
        return jsonify({'success': False, 'message': f'Error interno al generar reporte: {e}'}), 500

    # return jsonify({'success': True, 'data': 'Reporte generado exitosamente.'}), 200 # Línea original, reemplazar por la lógica de archivo/datos

# --- Rutas para impresión (Tickets y Comandas) ---

@pedidos.route('/<int:pedido_id>/imprimir/ticket')
@login_required
@role_required(ROLES_PEDIDOS_READ) # Todos los roles que ven pedidos pueden imprimir
def imprimir_ticket(pedido_id):
    """
    Renderiza una plantilla para imprimir el ticket de venta de un pedido.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Validar permisos si es necesario (ej. solo Cajero/Admin imprime tickets finales)
    # if not (current_user.is_admin() or current_user.is_cajero()):
    #      flash('No tienes permiso para imprimir tickets.', 'danger')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    # Necesitarás una plantilla 'pedidos/imprimir_ticket.html'
    return render_template(
        'pedidos/imprimir_ticket.html',
        pedido=pedido,
        config=current_app.config, # Pasar la configuración para nombre del negocio, etc.
        format_currency=format_currency,
        format_datetime=format_datetime,
        format_pedido_folio=format_pedido_folio
    )


@pedidos.route('/<int:pedido_id>/imprimir/comanda')
@login_required
@role_required(ROLES_PEDIDOS_PREPARACION) # Tablajero y Admin pueden imprimir comandas
def imprimir_comanda(pedido_id):
    """
    Renderiza una plantilla para imprimir la comanda de preparación de un pedido.
    """
    pedido = get_pedido_by_id(pedido_id)
    if not pedido:
        flash('Pedido no encontrado.', 'warning')
        return redirect(url_for('pedidos.dashboard_pedidos'))

    # Validar permisos si es necesario (ej. solo Tablajero/Admin imprime comandas)
    # if not (current_user.is_admin() or current_user.is_tablajero()):
    #      flash('No tienes permiso para imprimir comandas.', 'danger')
    #      return redirect(url_for('pedidos.ver_pedido', pedido_id=pedido.id))

    # Necesitarás una plantilla 'pedidos/imprimir_comanda.html'
    return render_template(
        'pedidos/imprimir_comanda.html',
        pedido=pedido,
        config=current_app.config, # Pasar la configuración
        format_datetime=format_datetime,
        format_pedido_folio=format_pedido_folio
    )
