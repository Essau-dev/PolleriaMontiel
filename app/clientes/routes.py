# Archivo: PolleriaMontiel\app\clientes\routes.py

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db # Aunque las operaciones de BD están en services, a veces db es útil en rutas
from app.models import RolUsuario, TipoCliente, TipoTelefono, TipoDireccion # Importar Enums si se usan en lógica de ruta
from . import clientes # Importar el Blueprint
from .forms import ClienteForm, TelefonoForm, DireccionForm # Importar formularios
from .services import (
    create_client, get_client_by_id, get_all_clients, search_clients,
    update_client, delete_client, activate_client, deactivate_client,
    create_phone_for_client, get_phone_by_id, update_phone, delete_phone, set_principal_phone,
    create_address_for_client, get_address_by_id, update_address, delete_address, set_principal_address
) # Importar funciones de servicio
from app.utils.decorators import role_required # Importar el decorador de roles
from app.utils.helpers import format_currency, format_datetime # Importar helpers para formateo

# Roles permitidos para operaciones de lectura/escritura de clientes
ROLES_CLIENTES_RW = [RolUsuario.CAJERO, RolUsuario.ADMINISTRADOR]
# Roles permitidos para operaciones administrativas de clientes (eliminar, activar/desactivar)
ROLES_CLIENTES_ADMIN = [RolUsuario.ADMINISTRADOR]


@clientes.route('/')
@clientes.route('/listar')
@login_required
@role_required(ROLES_CLIENTES_RW)
def listar_clientes():
    """
    Muestra una lista paginada de clientes activos.
    Permite búsqueda.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Clientes por página
    search_query = request.args.get('q', type=str)

    if search_query:
        clientes_pagination = search_clients(search_query, page=page, per_page=per_page)
        title = f'Resultados de búsqueda para "{search_query}"'
    else:
        clientes_pagination = get_all_clients(page=page, per_page=per_page)
        title = 'Lista de Clientes'

    clientes_list = clientes_pagination.items

    return render_template(
        'clientes/listar_clientes.html',
        title=title,
        clientes=clientes_list,
        pagination=clientes_pagination,
        search_query=search_query # Pasar la query para mantenerla en la paginación
    )

@clientes.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def crear_cliente():
    """
    Permite crear un nuevo cliente.
    """
    form = ClienteForm()
    if form.validate_on_submit():
        # La validación de unicidad del alias se maneja en el servicio
        nuevo_cliente = create_client(
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            alias=form.alias.data,
            tipo_cliente_value=form.tipo_cliente.data,
            notas_cliente=form.notas_cliente.data,
            activo=form.activo.data
        )

        if nuevo_cliente:
            flash(f'Cliente "{nuevo_cliente.nombre} {nuevo_cliente.apellidos or ""}" registrado exitosamente.', 'success')
            # Redirigir a la vista del cliente recién creado
            return redirect(url_for('clientes.ver_cliente', client_id=nuevo_cliente.id))
        else:
            # Si el servicio retorna None, es probable que el alias ya exista
            flash('Error al registrar cliente. El alias podría ya estar en uso.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    return render_template('clientes/crear_cliente.html', title='Registrar Nuevo Cliente', form=form)

@clientes.route('/<int:client_id>')
@login_required
@role_required(ROLES_CLIENTES_RW)
def ver_cliente(client_id):
    """
    Muestra los detalles de un cliente específico, incluyendo teléfonos y direcciones.
    """
    client = get_client_by_id(client_id)

    if not client:
        flash('Cliente no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    # Los teléfonos y direcciones se cargan automáticamente a través de las relaciones definidas en el modelo Cliente
    # client.telefonos (lazy='dynamic') y client.direcciones (lazy='dynamic')

    # Necesitarás una plantilla 'clientes/ver_cliente.html'
    return render_template(
        'clientes/ver_cliente.html',
        title=f'Cliente: {client.nombre} {client.apellidos or ""}',
        client=client,
        format_datetime=format_datetime # Pasar helper para mostrar fecha de registro
        # Puedes pasar formularios vacíos para añadir teléfono/dirección si se usan modales en la vista
        # telefono_form=TelefonoForm(),
        # direccion_form=DireccionForm()
    )

@clientes.route('/<int:client_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def editar_cliente(client_id):
    """
    Permite editar los datos de un cliente existente.
    """
    client = get_client_by_id(client_id)
    if not client:
        flash('Cliente no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    form = ClienteForm(obj=client) # Pre-llenar el formulario con datos del cliente

    if form.validate_on_submit():
        # La validación de unicidad del alias se maneja en el servicio
        updated_client = update_client(
            client_id=client.id,
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            alias=form.alias.data,
            tipo_cliente_value=form.tipo_cliente.data,
            notas_cliente=form.notas_cliente.data,
            activo=form.activo.data
        )

        if updated_client:
            flash(f'Cliente "{updated_client.nombre} {updated_client.apellidos or ""}" actualizado exitosamente.', 'success')
            return redirect(url_for('clientes.ver_cliente', client_id=updated_client.id))
        else:
            # Si el servicio retorna None, es probable que el alias ya exista para otro cliente
            flash('Error al actualizar cliente. El alias podría ya estar en uso por otro cliente.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    return render_template('clientes/editar_cliente.html', title=f'Editar Cliente: {client.nombre}', form=form, client=client)

@clientes.route('/<int:client_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_ADMIN) # Solo Admin puede eliminar
def eliminar_cliente(client_id):
    """
    Elimina un cliente. Requiere método POST.
    """
    client = get_client_by_id(client_id)
    if not client:
        flash('Cliente no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    # Considerar si el cliente tiene pedidos asociados. La FK en Pedido puede impedir la eliminación.
    # El servicio delete_client ya maneja IntegrityError.
    success = delete_client(client_id)

    if success:
        flash('Cliente eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash('Error al eliminar cliente. Podría tener pedidos u otros registros asociados.', 'danger')

    return redirect(url_for('clientes.listar_clientes'))

@clientes.route('/<int:client_id>/activar', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_ADMIN) # Solo Admin puede activar
def activar_cliente(client_id):
    """
    Activa un cliente. Requiere método POST.
    """
    client = activate_client(client_id)
    if client:
        flash(f'Cliente "{client.nombre} {client.apellidos or ""}" activado exitosamente.', 'success')
    else:
        flash('Error al activar cliente o cliente no encontrado.', 'danger')

    # Redirigir a la vista del cliente si existe, o a la lista si no
    if client:
        return redirect(url_for('clientes.ver_cliente', client_id=client.id))
    else:
        return redirect(url_for('clientes.listar_clientes'))


@clientes.route('/<int:client_id>/desactivar', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_ADMIN) # Solo Admin puede desactivar
def desactivar_cliente(client_id):
    """
    Desactiva un cliente. Requiere método POST.
    """
    client = deactivate_client(client_id)
    if client:
        flash(f'Cliente "{client.nombre} {client.apellidos or ""}" desactivado exitosamente.', 'success')
    else:
        flash('Error al desactivar cliente o cliente no encontrado.', 'danger')

    # Redirigir a la vista del cliente si existe, o a la lista si no
    if client:
        return redirect(url_for('clientes.ver_cliente', client_id=client.id))
    else:
        return redirect(url_for('clientes.listar_clientes'))


# --- Rutas para Teléfonos ---

@clientes.route('/<int:client_id>/telefonos/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def crear_telefono(client_id):
    """
    Permite añadir un nuevo número de teléfono a un cliente.
    """
    client = get_client_by_id(client_id)
    if not client:
        flash('Cliente no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    form = TelefonoForm()
    if form.validate_on_submit():
        # La validación de unicidad por cliente_id se maneja en el servicio
        nuevo_telefono = create_phone_for_client(
            client_id=client.id,
            numero_telefono=form.numero_telefono.data,
            tipo_telefono_value=form.tipo_telefono.data,
            es_principal=form.es_principal.data
        )

        if nuevo_telefono:
            flash(f'Teléfono "{nuevo_telefono.numero_telefono}" agregado a {client.nombre}.', 'success')
            return redirect(url_for('clientes.ver_cliente', client_id=client.id))
        else:
            # Si el servicio retorna None, es probable que el número ya exista para este cliente
            flash('Error al agregar teléfono. El número podría ya estar registrado para este cliente.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Necesitarás una plantilla 'clientes/crear_telefono.html'
    return render_template('clientes/crear_telefono.html', title=f'Agregar Teléfono a {client.nombre}', form=form, client=client)


@clientes.route('/telefonos/<int:phone_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def editar_telefono(phone_id):
    """
    Permite editar un número de teléfono existente.
    """
    phone = get_phone_by_id(phone_id)
    if not phone:
        flash('Teléfono no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes')) # Redirigir a lista de clientes si no se encuentra

    client = phone.cliente # Acceder al cliente a través de la relación
    if not client: # Esto no debería pasar si el teléfono existe, pero es buena práctica
         flash('Cliente asociado al teléfono no encontrado.', 'warning')
         return redirect(url_for('clientes.listar_clientes'))

    form = TelefonoForm(obj=phone) # Pre-llenar el formulario

    if form.validate_on_submit():
        # La validación de unicidad por cliente_id (excluyendo el propio teléfono) se maneja en el servicio
        updated_phone = update_phone(
            phone_id=phone.id,
            numero_telefono=form.numero_telefono.data,
            tipo_telefono_value=form.tipo_telefono.data,
            es_principal=form.es_principal.data
        )

        if updated_phone:
            flash(f'Teléfono "{updated_phone.numero_telefono}" actualizado.', 'success')
            return redirect(url_for('clientes.ver_cliente', client_id=client.id))
        else:
            # Si el servicio retorna None, es probable que el número ya exista para este cliente
            flash('Error al actualizar teléfono. El número podría ya estar registrado para este cliente.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Necesitarás una plantilla 'clientes/editar_telefono.html'
    return render_template('clientes/editar_telefono.html', title=f'Editar Teléfono de {client.nombre}', form=form, phone=phone, client=client)


@clientes.route('/telefonos/<int:phone_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_RW) # Cajero y Admin pueden eliminar teléfonos
def eliminar_telefono(phone_id):
    """
    Elimina un número de teléfono. Requiere método POST.
    """
    phone = get_phone_by_id(phone_id)
    if not phone:
        flash('Teléfono no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    client_id = phone.cliente_id # Guardar el ID del cliente antes de eliminar el teléfono

    success = delete_phone(phone_id)

    if success:
        flash('Teléfono eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar teléfono.', 'danger')

    # Redirigir a la vista del cliente
    return redirect(url_for('clientes.ver_cliente', client_id=client_id))


@clientes.route('/telefonos/<int:phone_id>/principal', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_RW) # Cajero y Admin pueden marcar como principal
def marcar_telefono_principal(phone_id):
    """
    Marca un teléfono como principal para su cliente. Requiere método POST.
    """
    phone = get_phone_by_id(phone_id)
    if not phone:
        flash('Teléfono no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    client_id = phone.cliente_id

    success = set_principal_phone(client_id, phone_id)

    if success:
        flash('Teléfono principal actualizado.', 'success')
    else:
        flash('Error al marcar teléfono como principal.', 'danger') # El servicio ya loggea el error

    # Redirigir a la vista del cliente
    return redirect(url_for('clientes.ver_cliente', client_id=client_id))


# --- Rutas para Direcciones ---

@clientes.route('/<int:client_id>/direcciones/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def crear_direccion(client_id):
    """
    Permite añadir una nueva dirección a un cliente.
    """
    client = get_client_by_id(client_id)
    if not client:
        flash('Cliente no encontrado.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    form = DireccionForm()
    if form.validate_on_submit():
        nuevo_direccion = create_address_for_client(
            client_id=client.id,
            calle_numero=form.calle_numero.data,
            colonia=form.colonia.data,
            ciudad=form.ciudad.data,
            codigo_postal=form.codigo_postal.data,
            referencias=form.referencias.data,
            tipo_direccion_value=form.tipo_direccion.data,
            latitud=form.latitud.data,
            longitud=form.longitud.data,
            es_principal=form.es_principal.data
        )

        if nuevo_direccion:
            flash(f'Dirección agregada a {client.nombre}.', 'success')
            return redirect(url_for('clientes.ver_cliente', client_id=client.id))
        else:
            flash('Error al agregar dirección.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Necesitarás una plantilla 'clientes/crear_direccion.html'
    return render_template('clientes/crear_direccion.html', title=f'Agregar Dirección a {client.nombre}', form=form, client=client)


@clientes.route('/direcciones/<int:address_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CLIENTES_RW)
def editar_direccion(address_id):
    """
    Permite editar una dirección existente.
    """
    address = get_address_by_id(address_id)
    if not address:
        flash('Dirección no encontrada.', 'warning')
        return redirect(url_for('clientes.listar_clientes')) # Redirigir a lista de clientes si no se encuentra

    client = address.cliente # Acceder al cliente a través de la relación
    if not client: # Esto no debería pasar si la dirección existe, pero es buena práctica
         flash('Cliente asociado a la dirección no encontrado.', 'warning')
         return redirect(url_for('clientes.listar_clientes'))

    form = DireccionForm(obj=address) # Pre-llenar el formulario

    if form.validate_on_submit():
        updated_address = update_address(
            address_id=address.id,
            calle_numero=form.calle_numero.data,
            colonia=form.colonia.data,
            ciudad=form.ciudad.data,
            codigo_postal=form.codigo_postal.data,
            referencias=form.referencias.data,
            tipo_direccion_value=form.tipo_direccion.data,
            latitud=form.latitud.data,
            longitud=form.longitud.data,
            es_principal=form.es_principal.data
        )

        if updated_address:
            flash('Dirección actualizada.', 'success')
            return redirect(url_for('clientes.ver_cliente', client_id=client.id))
        else:
            flash('Error al actualizar dirección.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Necesitarás una plantilla 'clientes/editar_direccion.html'
    return render_template('clientes/editar_direccion.html', title=f'Editar Dirección de {client.nombre}', form=form, address=address, client=client)


@clientes.route('/direcciones/<int:address_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_RW) # Cajero y Admin pueden eliminar direcciones
def eliminar_direccion(address_id):
    """
    Elimina una dirección. Requiere método POST.
    """
    address = get_address_by_id(address_id)
    if not address:
        flash('Dirección no encontrada.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    client_id = address.cliente_id # Guardar el ID del cliente antes de eliminar la dirección

    success = delete_address(address_id)

    if success:
        flash('Dirección eliminada exitosamente.', 'success')
    else:
        flash('Error al eliminar dirección.', 'danger')

    # Redirigir a la vista del cliente
    return redirect(url_for('clientes.ver_cliente', client_id=client_id))


@clientes.route('/direcciones/<int:address_id>/principal', methods=['POST'])
@login_required
@role_required(ROLES_CLIENTES_RW) # Cajero y Admin pueden marcar como principal
def marcar_direccion_principal(address_id):
    """
    Marca una dirección como principal para su cliente. Requiere método POST.
    """
    address = get_address_by_id(address_id)
    if not address:
        flash('Dirección no encontrada.', 'warning')
        return redirect(url_for('clientes.listar_clientes'))

    client_id = address.cliente_id

    success = set_principal_address(client_id, address_id)

    if success:
        flash('Dirección principal actualizada.', 'success')
    else:
        flash('Error al marcar dirección como principal.', 'danger') # El servicio ya loggea el error

    # Redirigir a la vista del cliente
    return redirect(url_for('clientes.ver_cliente', client_id=client_id))

# Puedes añadir rutas para ver historial de pedidos del cliente aquí si es necesario
# @clientes.route('/<int:client_id>/pedidos')
# @login_required
# @role_required(ROLES_CLIENTES_RW)
# def historial_pedidos_cliente(client_id):
#     client = get_client_by_id(client_id)
#     if not client:
#         flash('Cliente no encontrado.', 'warning')
#         return redirect(url_for('clientes.listar_clientes'))
#     # Obtener pedidos del cliente (usando la relación client.pedidos o un servicio específico)
#     pedidos = client.pedidos.order_by(Pedido.fecha_creacion.desc()).all() # Asumiendo que Pedido está importado
#     return render_template('clientes/historial_pedidos.html', title=f'Historial de Pedidos de {client.nombre}', client=client, pedidos=pedidos)
