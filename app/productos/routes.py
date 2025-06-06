# Archivo: PolleriaMontiel\app\productos\routes.py

from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (
    Producto, Subproducto, Modificacion, Precio, TipoCliente, RolUsuario
) # Importar modelos y Enums necesarios
from . import productos # Importar el Blueprint
from .forms import ProductoForm, SubproductoForm, ModificacionForm, PrecioForm, CATEGORIAS_PRODUCTO # Importar formularios y categorías
from .services import (
    create_producto, get_producto_by_id, get_all_productos, search_productos,
    update_producto, delete_producto, activate_producto, deactivate_producto,
    create_subproducto, get_subproducto_by_id, get_all_subproductos, search_subproductos,
    update_subproducto, delete_subproducto, activate_subproducto, deactivate_subproducto,
    create_modificacion, get_modificacion_by_id, get_all_modificaciones, search_modificaciones,
    update_modificacion, delete_modificacion, activate_modificacion, deactivate_modificacion,
    create_precio, get_precio_by_id, get_all_precios, update_precio, delete_precio,
    activate_precio, deactivate_precio,
    _get_precio_aplicable # Importar función interna si se necesita en alguna ruta (aunque ya está en pedidos.routes para AJAX)
) # Importar funciones de servicio
from app.utils.decorators import role_required # Importar el decorador de roles
from app.utils.helpers import format_currency, format_date # Importar helpers
from decimal import Decimal # Importar Decimal

# Roles permitidos para la gestión de productos (CRUD completo)
ROLES_PRODUCTOS_ADMIN = [RolUsuario.ADMINISTRADOR]
# Roles permitidos para ver el catálogo (ej. para seleccionar en pedidos)
ROLES_PRODUCTOS_READ = [RolUsuario.ADMINISTRADOR, RolUsuario.CAJERO, RolUsuario.TABLAJERO] # Tablajero podría necesitar ver detalles de modificaciones

# --- Rutas Principales del Módulo Productos ---

@productos.route('/')
@productos.route('/dashboard')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver el catálogo
def dashboard_productos():
    """
    Muestra el dashboard principal del módulo de productos, listando productos principales.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Productos por página
    search_query = request.args.get('q', type=str)
    include_inactive = request.args.get('show_inactive', 'false').lower() == 'true'

    if search_query:
        productos_pagination = search_productos(search_query, page=page, per_page=per_page)
        title = f'Resultados de búsqueda de Productos para "{search_query}"'
    else:
        productos_pagination = get_all_productos(page=page, per_page=per_page, include_inactive=include_inactive)
        title = 'Catálogo de Productos Principales'

    productos_list = productos_pagination.items

    # Necesitarás una plantilla 'productos/dashboard_productos.html'
    return render_template(
        'productos/dashboard_productos.html',
        title=title,
        productos=productos_list,
        pagination=productos_pagination,
        search_query=search_query,
        include_inactive=include_inactive
    )

# --- Rutas para Producto ---

@productos.route('/producto/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede crear productos
def crear_producto():
    """
    Permite crear un nuevo producto principal.
    """
    form = ProductoForm()
    # Las choices de categoría ya están definidas en el formulario

    if form.validate_on_submit():
        # La validación de unicidad de ID y nombre se maneja en el servicio
        nuevo_producto = create_producto(
            id=form.id.data.upper(), # Guardar ID en mayúsculas
            nombre=form.nombre.data,
            categoria=form.categoria.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data
        )

        if nuevo_producto:
            flash(f'Producto "{nuevo_producto.nombre}" ({nuevo_producto.id}) creado exitosamente.', 'success')
            return redirect(url_for('productos.ver_producto', producto_id=nuevo_producto.id))
        else:
            # Si el servicio retorna None, es probable que el ID o nombre ya exista
            # El servicio ya imprime un error detallado
            flash('Error al crear producto. El código o nombre podría ya existir.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/crear_producto.html'
    return render_template('productos/crear_producto.html', title='Crear Nuevo Producto', form=form)


@productos.route('/producto/<string:producto_id>')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver detalles
def ver_producto(producto_id):
    """
    Muestra los detalles de un producto principal específico, incluyendo subproductos, modificaciones y precios.
    """
    producto = get_producto_by_id(producto_id)

    if not producto:
        flash('Producto no encontrado.', 'warning')
        return redirect(url_for('productos.dashboard_productos'))

    # Necesitarás una plantilla 'productos/ver_producto.html'
    return render_template(
        'productos/ver_producto.html',
        title=f'Detalle de Producto: {producto.nombre}',
        producto=producto,
        format_currency=format_currency,
        format_date=format_date
    )


@productos.route('/producto/<string:producto_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede editar productos
def editar_producto(producto_id):
    """
    Permite editar los datos de un producto principal existente.
    """
    producto = get_producto_by_id(producto_id)
    if not producto:
        flash('Producto no encontrado.', 'warning')
        return redirect(url_for('productos.dashboard_productos'))

    form = ProductoForm(obj=producto) # Pre-llenar el formulario

    # Deshabilitar el campo ID en edición
    form.id.render_kw['readonly'] = True
    form.id.validators = [] # Eliminar validadores de unicidad para edición

    if form.validate_on_submit():
        # La validación de unicidad del nombre se maneja en el servicio
        updated_producto = update_producto(
            producto_id=producto.id, # Usar el ID original
            nombre=form.nombre.data,
            categoria=form.categoria.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data
        )

        if updated_producto:
            flash(f'Producto "{updated_producto.nombre}" ({updated_producto.id}) actualizado exitosamente.', 'success')
            return redirect(url_for('productos.ver_producto', producto_id=updated_producto.id))
        else:
            # Si el servicio retorna None, es probable que el nombre ya exista
            # El servicio ya imprime un error detallado
            flash('Error al actualizar producto. El nombre podría ya existir.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/editar_producto.html'
    return render_template('productos/editar_producto.html', title=f'Editar Producto: {producto.nombre}', form=form, producto=producto)


@productos.route('/producto/<string:producto_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede eliminar productos
def eliminar_producto(producto_id):
    """
    Elimina un producto principal. Requiere método POST.
    """
    producto = get_producto_by_id(producto_id)
    if not producto:
        flash('Producto no encontrado.', 'warning')
        return redirect(url_for('productos.dashboard_productos'))

    success = delete_producto(producto_id)

    if success:
        flash(f'Producto "{producto.nombre}" ({producto.id}) eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash(f'Error al eliminar producto "{producto.nombre}" ({producto.id}). Podría tener registros asociados (subproductos, precios, ítems de pedido) que impiden la eliminación. Considere desactivarlo.', 'danger')

    return redirect(url_for('productos.dashboard_productos'))


@productos.route('/producto/<string:producto_id>/activar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede activar productos
def activar_producto(producto_id):
    """
    Activa un producto principal. Requiere método POST.
    """
    producto = activate_producto(producto_id)
    if producto:
        flash(f'Producto "{producto.nombre}" ({producto.id}) activado exitosamente.', 'success')
    else:
        flash(f'Error al activar producto con ID "{producto_id}".', 'danger')

    # Redirigir a la vista de detalle o al dashboard
    return redirect(url_for('productos.dashboard_productos'))


@productos.route('/producto/<string:producto_id>/desactivar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede desactivar productos
def desactivar_producto(producto_id):
    """
    Desactiva un producto principal. Requiere método POST.
    """
    producto = deactivate_producto(producto_id)
    if producto:
        flash(f'Producto "{producto.nombre}" ({producto.id}) desactivado exitosamente.', 'success')
    else:
        flash(f'Error al desactivar producto con ID "{producto_id}".', 'danger')

    # Redirigir a la vista de detalle o al dashboard
    return redirect(url_for('productos.dashboard_productos'))


# --- Rutas para Subproducto ---

@productos.route('/subproductos/')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver subproductos
def listar_subproductos():
    """
    Muestra una lista paginada de subproductos.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Subproductos por página
    search_query = request.args.get('q', type=str)
    include_inactive = request.args.get('show_inactive', 'false').lower() == 'true'

    if search_query:
        subproductos_pagination = search_subproductos(search_query, page=page, per_page=per_page)
        title = f'Resultados de búsqueda de Subproductos para "{search_query}"'
    else:
        subproductos_pagination = get_all_subproductos(page=page, per_page=per_page, include_inactive=include_inactive)
        title = 'Catálogo de Subproductos'

    subproductos_list = subproductos_pagination.items

    # Necesitarás una plantilla 'productos/listar_subproductos.html'
    return render_template(
        'productos/listar_subproductos.html',
        title=title,
        subproductos=subproductos_list,
        pagination=subproductos_pagination,
        search_query=search_query,
        include_inactive=include_inactive
    )


@productos.route('/subproducto/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede crear subproductos
def crear_subproducto():
    """
    Permite crear un nuevo subproducto.
    """
    form = SubproductoForm()

    # Poblar choices de Producto Padre dinámicamente con productos activos
    productos_activos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()
    form.producto_padre_id.choices = [('', 'Seleccionar Producto Padre')] + [(p.id, f'{p.nombre} ({p.id})') for p in productos_activos]

    if form.validate_on_submit():
        # La validación de unicidad de código y existencia de producto padre se maneja en el servicio
        nuevo_subproducto = create_subproducto(
            producto_padre_id=form.producto_padre_id.data,
            codigo_subprod=form.codigo_subprod.data.upper(), # Guardar código en mayúsculas
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data
        )

        if nuevo_subproducto:
            flash(f'Subproducto "{nuevo_subproducto.nombre}" ({nuevo_subproducto.codigo_subprod}) creado exitosamente.', 'success')
            return redirect(url_for('productos.ver_subproducto', subproducto_id=nuevo_subproducto.id))
        else:
            # Si el servicio retorna None, es probable que el código ya exista o el producto padre no sea válido
            # El servicio ya imprime un error detallado
            flash('Error al crear subproducto. El código podría ya existir o el producto padre no es válido.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/crear_subproducto.html'
    return render_template('productos/crear_subproducto.html', title='Crear Nuevo Subproducto', form=form)


@productos.route('/subproducto/<int:subproducto_id>')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver detalles
def ver_subproducto(subproducto_id):
    """
    Muestra los detalles de un subproducto específico, incluyendo su producto padre, modificaciones y precios.
    """
    subproducto = get_subproducto_by_id(subproducto_id)

    if not subproducto:
        flash('Subproducto no encontrado.', 'warning')
        return redirect(url_for('productos.listar_subproductos'))

    # Necesitarás una plantilla 'productos/ver_subproducto.html'
    return render_template(
        'productos/ver_subproducto.html',
        title=f'Detalle de Subproducto: {subproducto.nombre}',
        subproducto=subproducto,
        format_currency=format_currency,
        format_date=format_date
    )


@productos.route('/subproducto/<int:subproducto_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede editar subproductos
def editar_subproducto(subproducto_id):
    """
    Permite editar los datos de un subproducto existente.
    """
    subproducto = get_subproducto_by_id(subproducto_id)
    if not subproducto:
        flash('Subproducto no encontrado.', 'warning')
        return redirect(url_for('productos.listar_subproductos'))

    form = SubproductoForm(obj=subproducto) # Pre-llenar el formulario

    # Poblar choices de Producto Padre dinámicamente con productos activos
    productos_activos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()
    form.producto_padre_id.choices = [('', 'Seleccionar Producto Padre')] + [(p.id, f'{p.nombre} ({p.id})') for p in productos_activos]

    # Asegurar que el producto padre actual esté seleccionado si existe
    if subproducto.producto_padre_id:
        form.producto_padre_id.data = subproducto.producto_padre_id

    if form.validate_on_submit():
        # La validación de unicidad de código y existencia de producto padre se maneja en el servicio
        updated_subproducto = update_subproducto(
            subproducto_id=subproducto.id,
            producto_padre_id=form.producto_padre_id.data,
            codigo_subprod=form.codigo_subprod.data.upper(), # Guardar código en mayúsculas
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data
        )

        if updated_subproducto:
            flash(f'Subproducto "{updated_subproducto.nombre}" ({updated_subproducto.codigo_subprod}) actualizado exitosamente.', 'success')
            return redirect(url_for('productos.ver_subproducto', subproducto_id=updated_subproducto.id))
        else:
            # Si el servicio retorna None, es probable que el código ya exista o el producto padre no sea válido
            # El servicio ya imprime un error detallado
            flash('Error al actualizar subproducto. El código podría ya existir o el producto padre no es válido.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/editar_subproducto.html'
    return render_template('productos/editar_subproducto.html', title=f'Editar Subproducto: {subproducto.nombre}', form=form, subproducto=subproducto)


@productos.route('/subproducto/<int:subproducto_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede eliminar subproductos
def eliminar_subproducto(subproducto_id):
    """
    Elimina un subproducto. Requiere método POST.
    """
    subproducto = get_subproducto_by_id(subproducto_id)
    if not subproducto:
        flash('Subproducto no encontrado.', 'warning')
        return redirect(url_for('productos.listar_subproductos'))

    success = delete_subproducto(subproducto_id)

    if success:
        flash(f'Subproducto "{subproducto.nombre}" ({subproducto.codigo_subprod}) eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash(f'Error al eliminar subproducto "{subproducto.nombre}" ({subproducto.codigo_subprod}). Podría tener registros asociados (precios, ítems de pedido) que impiden la eliminación. Considere desactivarlo.', 'danger')

    return redirect(url_for('productos.listar_subproductos'))


@productos.route('/subproducto/<int:subproducto_id>/activar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede activar subproductos
def activar_subproducto(subproducto_id):
    """
    Activa un subproducto. Requiere método POST.
    """
    subproducto = activate_subproducto(subproducto_id)
    if subproducto:
        flash(f'Subproducto "{subproducto.nombre}" ({subproducto.codigo_subprod}) activado exitosamente.', 'success')
    else:
        flash(f'Error al activar subproducto con ID {subproducto_id}.', 'danger')

    # Redirigir a la vista de detalle o a la lista
    return redirect(url_for('productos.listar_subproductos'))


@productos.route('/subproducto/<int:subproducto_id>/desactivar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede desactivar subproductos
def desactivar_subproducto(subproducto_id):
    """
    Desactiva un subproducto. Requiere método POST.
    """
    subproducto = deactivate_subproducto(subproducto_id)
    if subproducto:
        flash(f'Subproducto "{subproducto.nombre}" ({subproducto.codigo_subprod}) desactivado exitosamente.', 'success')
    else:
        flash(f'Error al desactivar subproducto con ID {subproducto_id}.', 'danger')

    # Redirigir a la vista de detalle o a la lista
    return redirect(url_for('productos.listar_subproductos'))


# --- Rutas para Modificacion ---

@productos.route('/modificaciones/')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver modificaciones
def listar_modificaciones():
    """
    Muestra una lista paginada de modificaciones.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Modificaciones por página
    search_query = request.args.get('q', type=str)
    include_inactive = request.args.get('show_inactive', 'false').lower() == 'true'

    if search_query:
        modificaciones_pagination = search_modificaciones(search_query, page=page, per_page=per_page)
        title = f'Resultados de búsqueda de Modificaciones para "{search_query}"'
    else:
        modificaciones_pagination = get_all_modificaciones(page=page, per_page=per_page, include_inactive=include_inactive)
        title = 'Catálogo de Modificaciones'

    modificaciones_list = modificaciones_pagination.items

    # Necesitarás una plantilla 'productos/listar_modificaciones.html'
    return render_template(
        'productos/listar_modificaciones.html',
        title=title,
        modificaciones=modificaciones_list,
        pagination=modificaciones_pagination,
        search_query=search_query,
        include_inactive=include_inactive
    )


@productos.route('/modificacion/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede crear modificaciones
def crear_modificacion():
    """
    Permite crear una nueva modificación.
    """
    form = ModificacionForm()

    # Para asociar productos/subproductos, la UI necesitará selectores múltiples o de búsqueda.
    # Para MVP, podemos simplificar y no incluir la asociación en el formulario de creación,
    # o usar campos de texto para IDs y procesarlos aquí/servicio.
    # Una mejor UX sería con AJAX en el frontend.
    # Para este backend, asumimos que los IDs de asociación vienen en el request si se usa POST.
    # Si es GET, simplemente mostramos el formulario básico.

    if form.validate_on_submit():
        # Obtener IDs de productos/subproductos asociados del request (si la UI los envía)
        # Esto dependerá de cómo se implemente el formulario en la plantilla
        productos_asociados_ids = request.form.getlist('productos_asociados_ids') # Asume un campo con este nombre
        subproductos_asociados_ids_str = request.form.getlist('subproductos_asociados_ids') # Asume un campo con este nombre
        # Convertir IDs de subproductos a int
        subproductos_asociados_ids = [int(id) for id in subproductos_asociados_ids_str if id.isdigit()]


        # La validación de unicidad de código se maneja en el servicio
        nueva_modificacion = create_modificacion(
            codigo_modif=form.codigo_modif.data.upper(), # Guardar código en mayúsculas
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data,
            productos_asociados_ids=productos_asociados_ids,
            subproductos_asociados_ids=subproductos_asociados_ids
        )

        if nueva_modificacion:
            flash(f'Modificación "{nueva_modificacion.nombre}" ({nueva_modificacion.codigo_modif}) creada exitosamente.', 'success')
            return redirect(url_for('productos.ver_modificacion', modificacion_id=nueva_modificacion.id))
        else:
            # Si el servicio retorna None, es probable que el código ya exista
            # El servicio ya imprime un error detallado
            flash('Error al crear modificación. El código podría ya existir.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/crear_modificacion.html'
    # Si la plantilla necesita la lista de productos/subproductos para los selectores, pásalos aquí
    productos_activos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()
    subproductos_activos = Subproducto.query.filter_by(activo=True).order_by(Subproducto.nombre.asc()).all()

    return render_template(
        'productos/crear_modificacion.html',
        title='Crear Nueva Modificación',
        form=form,
        productos_activos=productos_activos, # Pasar listas para selectores en plantilla
        subproductos_activos=subproductos_activos
    )


@productos.route('/modificacion/<int:modificacion_id>')
@login_required
@role_required(ROLES_PRODUCTOS_READ) # Admin, Cajero, Tablajero pueden ver detalles
def ver_modificacion(modificacion_id):
    """
    Muestra los detalles de una modificación específica, incluyendo a qué productos/subproductos aplica.
    """
    modificacion = get_modificacion_by_id(modificacion_id)

    if not modificacion:
        flash('Modificación no encontrada.', 'warning')
        return redirect(url_for('productos.listar_modificaciones'))

    # Necesitarás una plantilla 'productos/ver_modificacion.html'
    return render_template(
        'productos/ver_modificacion.html',
        title=f'Detalle de Modificación: {modificacion.nombre}',
        modificacion=modificacion
    )


@productos.route('/modificacion/<int:modificacion_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede editar modificaciones
def editar_modificacion(modificacion_id):
    """
    Permite editar los datos de una modificación existente y sus asociaciones.
    """
    modificacion = get_modificacion_by_id(modificacion_id)
    if not modificacion:
        flash('Modificación no encontrada.', 'warning')
        return redirect(url_for('productos.listar_modificaciones'))

    form = ModificacionForm(obj=modificacion) # Pre-llenar el formulario

    # Para editar asociaciones, la UI necesitará mostrar las asociaciones actuales
    # y permitir añadir/quitar. Esto se maneja en la plantilla y se procesa en el POST.

    if form.validate_on_submit():
        # Obtener IDs de productos/subproductos asociados del request (si la UI los envía)
        # Esto dependerá de cómo se implemente el formulario en la plantilla
        productos_asociados_ids = request.form.getlist('productos_asociados_ids') # Asume un campo con este nombre
        subproductos_asociados_ids_str = request.form.getlist('subproductos_asociados_ids') # Asume un campo con este nombre
        # Convertir IDs de subproductos a int
        subproductos_asociados_ids = [int(id) for id in subproductos_asociados_ids_str if id.isdigit()]

        # La validación de unicidad de código se maneja en el servicio
        updated_modificacion = update_modificacion(
            modificacion_id=modificacion.id,
            codigo_modif=form.codigo_modif.data.upper(), # Guardar código en mayúsculas
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            activo=form.activo.data,
            productos_asociados_ids=productos_asociados_ids, # Pasar las listas actualizadas
            subproductos_asociados_ids=subproductos_asociados_ids
        )

        if updated_modificacion:
            flash(f'Modificación "{updated_modificacion.nombre}" ({updated_modificacion.codigo_modif}) actualizada exitosamente.', 'success')
            return redirect(url_for('productos.ver_modificacion', modificacion_id=updated_modificacion.id))
        else:
            # Si el servicio retorna None, es probable que el código ya exista
            # El servicio ya imprime un error detallado
            flash('Error al actualizar modificación. El código podría ya existir.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/editar_modificacion.html'
    # Si la plantilla necesita la lista de productos/subproductos para los selectores, pásalos aquí
    productos_activos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()
    subproductos_activos = Subproducto.query.filter_by(activo=True).order_by(Subproducto.nombre.asc()).all()

    return render_template(
        'productos/editar_modificacion.html',
        title=f'Editar Modificación: {modificacion.nombre}',
        form=form,
        modificacion=modificacion, # Pasar el objeto para mostrar asociaciones actuales
        productos_activos=productos_activos, # Pasar listas para selectores en plantilla
        subproductos_activos=subproductos_activos
    )


@productos.route('/modificacion/<int:modificacion_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede eliminar modificaciones
def eliminar_modificacion(modificacion_id):
    """
    Elimina una modificación. Requiere método POST.
    """
    modificacion = get_modificacion_by_id(modificacion_id)
    if not modificacion:
        flash('Modificación no encontrada.', 'warning')
        return redirect(url_for('productos.listar_modificaciones'))

    success = delete_modificacion(modificacion_id)

    if success:
        flash(f'Modificación "{modificacion.nombre}" ({modificacion.codigo_modif}) eliminada exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash(f'Error al eliminar modificación "{modificacion.nombre}" ({modificacion.codigo_modif}). Podría tener registros asociados (ítems de pedido) que impiden la eliminación. Considere desactivarla.', 'danger')

    return redirect(url_for('productos.listar_modificaciones'))


@productos.route('/modificacion/<int:modificacion_id>/activar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede activar modificaciones
def activar_modificacion(modificacion_id):
    """
    Activa una modificación. Requiere método POST.
    """
    modificacion = activate_modificacion(modificacion_id)
    if modificacion:
        flash(f'Modificación "{modificacion.nombre}" ({modificacion.codigo_modif}) activada exitosamente.', 'success')
    else:
        flash(f'Error al activar modificación con ID {modificacion_id}.', 'danger')

    # Redirigir a la vista de detalle o a la lista
    return redirect(url_for('productos.listar_modificaciones'))


@productos.route('/modificacion/<int:modificacion_id>/desactivar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede desactivar modificaciones
def desactivar_modificacion(modificacion_id):
    """
    Desactiva una modificación. Requiere método POST.
    """
    modificacion = deactivate_modificacion(modificacion_id)
    if modificacion:
        flash(f'Modificación "{modificacion.nombre}" ({modificacion.codigo_modif}) desactivada exitosamente.', 'success')
    else:
        flash(f'Error al desactivar modificación con ID {modificacion_id}.', 'danger')

    # Redirigir a la vista de detalle o a la lista
    return redirect(url_for('productos.listar_modificaciones'))


# --- Rutas para Precio ---

@productos.route('/precios/')
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede gestionar precios
def listar_precios():
    """
    Muestra una lista paginada de registros de precios.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Precios por página
    # No hay búsqueda por texto para precios en MVP, solo listado/filtrado si se implementa
    include_inactive = request.args.get('show_inactive', 'false').lower() == 'true'

    precios_pagination = get_all_precios(page=page, per_page=per_page, include_inactive=include_inactive)
    title = 'Catálogo de Precios'

    precios_list = precios_pagination.items

    # Necesitarás una plantilla 'productos/listar_precios.html'
    return render_template(
        'productos/listar_precios.html',
        title=title,
        precios=precios_list,
        pagination=precios_pagination,
        include_inactive=include_inactive,
        format_currency=format_currency,
        format_date=format_date
    )


@productos.route('/precio/nuevo', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede crear precios
def crear_precio():
    """
    Permite crear un nuevo registro de precio.
    """
    form = PrecioForm()

    # Poblar choices de Producto y Subproducto dinámicamente con activos
    productos_activos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()
    form.producto_id.choices = [('', 'Seleccionar Producto')] + [(p.id, f'{p.nombre} ({p.id})') for p in productos_activos]

    subproductos_activos = Subproducto.query.filter_by(activo=True).order_by(Subproducto.nombre.asc()).all()
    form.subproducto_id.choices = [(0, 'Seleccionar Subproducto')] + [(sp.id, f'{sp.nombre} ({sp.codigo_subprod})') for sp in subproductos_activos]

    # Las choices de Tipo de Cliente ya están definidas en el formulario

    if form.validate_on_submit():
        # La validación de unicidad de la combinación y existencia de producto/subproducto se maneja en el servicio
        nuevo_precio = create_precio(
            producto_id=form.producto_id.data if form.producto_id.data != '' else None, # Convertir '' a None
            subproducto_id=form.subproducto_id.data if form.subproducto_id.data != 0 else None, # Convertir 0 a None
            tipo_cliente_value=form.tipo_cliente.data,
            precio_kg=form.precio_kg.data,
            cantidad_minima_kg=form.cantidad_minima_kg.data,
            etiqueta_promo=form.etiqueta_promo.data,
            fecha_inicio_vigencia=form.fecha_inicio_vigencia.data,
            fecha_fin_vigencia=form.fecha_fin_vigencia.data,
            activo=form.activo.data
        )

        if nuevo_precio:
            flash(f'Precio creado exitosamente para {nuevo_precio.producto_base.nombre if nuevo_precio.producto_id else nuevo_precio.subproducto_base.nombre} ({nuevo_precio.tipo_cliente.name}).', 'success')
            return redirect(url_for('productos.listar_precios')) # Redirigir a la lista de precios
        else:
            # Si el servicio retorna None, es probable que la combinación ya exista o los IDs no sean válidos
            # El servicio ya imprime un error detallado
            flash('Error al crear precio. La combinación de producto/subproducto, tipo de cliente y cantidad mínima podría ya existir o los IDs no son válidos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/crear_precio.html'
    return render_template('productos/crear_precio.html', title='Crear Nuevo Precio', form=form)


@productos.route('/precio/<int:precio_id>/editar', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede editar precios
def editar_precio(precio_id):
    """
    Permite editar un registro de precio existente.
    """
    precio = get_precio_by_id(precio_id)
    if not precio:
        flash('Precio no encontrado.', 'warning')
        return redirect(url_for('productos.listar_precios'))

    form = PrecioForm(obj=precio) # Pre-llenar el formulario

    # Deshabilitar los campos de producto/subproducto en edición
    form.producto_id.render_kw['disabled'] = True
    form.subproducto_id.render_kw['disabled'] = True
    # Asegurar que los datos originales se mantengan si se re-renderiza el form
    form.producto_id.data = precio.producto_id
    form.subproducto_id.data = precio.subproducto_id

    # Poblar choices de Tipo de Cliente (ya están en el formulario)

    if form.validate_on_submit():
        # La validación de unicidad de la combinación (si cambian tipo_cliente o cantidad_minima_kg) se maneja en el servicio
        updated_precio = update_precio(
            precio_id=precio.id,
            tipo_cliente_value=form.tipo_cliente.data,
            precio_kg=form.precio_kg.data,
            cantidad_minima_kg=form.cantidad_minima_kg.data,
            etiqueta_promo=form.etiqueta_promo.data,
            fecha_inicio_vigencia=form.fecha_inicio_vigencia.data,
            fecha_fin_vigencia=form.fecha_fin_vigencia.data,
            activo=form.activo.data
        )

        if updated_precio:
            flash(f'Precio actualizado exitosamente para {updated_precio.producto_base.nombre if updated_precio.producto_id else updated_precio.subproducto_base.nombre} ({updated_precio.tipo_cliente.name}).', 'success')
            return redirect(url_for('productos.listar_precios')) # Redirigir a la lista de precios
        else:
            # Si el servicio retorna None, es probable que la combinación ya exista
            # El servicio ya imprime un error detallado
            flash('Error al actualizar precio. La combinación de tipo de cliente y cantidad mínima podría ya existir para este producto/subproducto.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, renderizar el formulario
    # Necesitarás una plantilla 'productos/editar_precio.html'
    return render_template('productos/editar_precio.html', title=f'Editar Precio ID: {precio.id}', form=form, precio=precio)


@productos.route('/precio/<int:precio_id>/eliminar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede eliminar precios
def eliminar_precio(precio_id):
    """
    Elimina un registro de precio. Requiere método POST.
    """
    precio = get_precio_by_id(precio_id)
    if not precio:
        flash('Precio no encontrado.', 'warning')
        return redirect(url_for('productos.listar_precios'))

    success = delete_precio(precio_id)

    if success:
        flash(f'Precio ID {precio_id} eliminado exitosamente.', 'success')
    else:
        # El servicio ya imprime un error detallado en la consola
        flash(f'Error al eliminar precio ID {precio_id}.', 'danger')

    return redirect(url_for('productos.listar_precios'))


@productos.route('/precio/<int:precio_id>/activar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede activar precios
def activar_precio(precio_id):
    """
    Activa un registro de precio. Requiere método POST.
    """
    precio = activate_precio(precio_id)
    if precio:
        flash(f'Precio ID {precio.id} activado exitosamente.', 'success')
    else:
        flash(f'Error al activar precio con ID {precio_id}.', 'danger')

    # Redirigir a la lista
    return redirect(url_for('productos.listar_precios'))


@productos.route('/precio/<int:precio_id>/desactivar', methods=['POST'])
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin puede desactivar precios
def desactivar_precio(precio_id):
    """
    Desactiva un registro de precio. Requiere método POST.
    """
    precio = deactivate_precio(precio_id)
    if precio:
        flash(f'Precio ID {precio.id} desactivado exitosamente.', 'success')
    else:
        flash(f'Error al desactivar precio con ID {precio_id}.', 'danger')

    # Redirigir a la lista
    return redirect(url_for('productos.listar_precios'))


# --- Rutas AJAX para funcionalidades dinámicas en formularios de Productos ---

@productos.route('/ajax/get_subproducts_by_product/<string:product_id>')
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin necesita esto para formularios de productos
def ajax_get_subproducts_by_product(product_id):
    """
    Endpoint AJAX para obtener subproductos activos asociados a un producto principal.
    Retorna resultados en formato JSON para usar en selectores dinámicos.
    """
    subproductos = Subproducto.query.filter_by(producto_padre_id=product_id, activo=True).order_by(Subproducto.nombre.asc()).all()

    results = []
    # Añadir opción "Seleccionar Subproducto" con valor 0
    results.append({'id': 0, 'text': 'Seleccionar Subproducto'})

    for sp in subproductos:
        results.append({
            'id': sp.id,
            'text': f"{sp.nombre} ({sp.codigo_subprod})"
        })

    return jsonify(results)


@productos.route('/ajax/get_modifications_by_product_or_subproduct')
@login_required
@role_required(ROLES_PRODUCTOS_ADMIN) # Solo Admin necesita esto para formularios de productos
def ajax_get_modifications_by_product_or_subproduct():
    """
    Endpoint AJAX para obtener modificaciones activas aplicables a un producto o subproducto.
    Retorna resultados en formato JSON para usar en selectores dinámicos.
    """
    producto_id = request.args.get('producto_id')
    subproducto_id = request.args.get('subproducto_id', type=int)

    modificaciones = []

    if subproducto_id:
        subproducto = get_subproducto_by_id(subproducto_id)
        if subproducto:
            # Cargar modificaciones aplicables a este subproducto
            modificaciones = subproducto.modificaciones_aplicables.filter_by(activo=True).order_by(Modificacion.nombre.asc()).all()
    elif producto_id:
        producto = get_producto_by_id(producto_id)
        if producto:
            # Cargar modificaciones directas aplicables a este producto
            modificaciones = producto.modificaciones_directas.filter_by(activo=True).order_by(Modificacion.nombre.asc()).all()

    results = []
    # Añadir opción "Ninguna Modificación" con ID 0
    results.append({'id': 0, 'text': 'Ninguna Modificación'})

    for mod in modificaciones:
        results.append({
            'id': mod.id,
            'text': f"{mod.nombre} ({mod.codigo_modif})"
        })

    return jsonify(results)

# Nota: Las rutas AJAX para búsqueda de productos/subproductos y obtención de precio
# aplicable para la toma de pedidos se encuentran en app/pedidos/routes.py
