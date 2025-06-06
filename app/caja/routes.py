# Archivo: PolleriaMontiel\app\caja\routes.py

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db # Aunque las operaciones de BD están en services, a veces db es útil en rutas
from app.models import RolUsuario, TipoMovimientoCaja, FormaPago, EstadoCorteCaja # Importar Enums si se usan en lógica de ruta
from . import caja # Importar el Blueprint
from .forms import MovimientoCajaForm, AperturaCajaForm, CierreCajaForm # Importar formularios
from .services import (
    get_current_open_corte_caja, realizar_apertura_caja, realizar_cierre_de_caja,
    registrar_movimiento_caja, get_all_cortes_caja, get_corte_caja_by_id,
    get_movimientos_for_corte
) # Importar funciones de servicio
from app.utils.decorators import role_required # Importar el decorador de roles
from app.utils.helpers import format_currency, format_datetime # Importar helpers para formateo
from decimal import Decimal # Importar Decimal

# Roles permitidos para la mayoría de las operaciones de caja
ROLES_CAJA = [RolUsuario.CAJERO, RolUsuario.ADMINISTRADOR]

@caja.route('/')
@caja.route('/dashboard')
@login_required
@role_required(ROLES_CAJA)
def dashboard_caja():
    """
    Muestra el dashboard de caja con el estado actual del corte abierto
    y los movimientos recientes.
    """
    # Obtener el corte de caja abierto para el usuario actual
    # Para MVP, asumimos que cada usuario Cajero/Admin tiene su propio corte o gestiona uno global
    # Aquí buscamos el último corte abierto, idealmente asociado al usuario si la lógica lo requiere
    corte_abierto = get_current_open_corte_caja(usuario_id=current_user.id)
    # Si no se encuentra un corte abierto para el usuario, buscar el último abierto en general
    if not corte_abierto and current_user.rol == RolUsuario.ADMINISTRADOR.value:
         corte_abierto = get_current_open_corte_caja() # Admin puede ver el último abierto global

    movimientos_recientes = []
    if corte_abierto:
        # Obtener movimientos asociados a este corte
        movimientos_recientes = get_movimientos_for_corte(corte_abierto.id)
        # Ordenar por fecha descendente
        movimientos_recientes.sort(key=lambda m: m.fecha_movimiento, reverse=True)
    else:
        # Si no hay corte abierto, mostrar algunos movimientos recientes generales (opcional)
        # movimientos_recientes = MovimientoCaja.query.order_by(MovimientoCaja.fecha_movimiento.desc()).limit(20).all()
        pass # Para MVP, solo mostramos movimientos del corte abierto

    return render_template(
        'caja/dashboard_caja.html',
        title='Dashboard de Caja',
        corte_abierto=corte_abierto,
        movimientos_recientes=movimientos_recientes,
        format_currency=format_currency, # Pasar helper a la plantilla
        format_datetime=format_datetime # Pasar helper a la plantilla
    )

@caja.route('/apertura', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CAJA)
def apertura_caja():
    """
    Permite al usuario realizar la apertura de un nuevo periodo de caja.
    """
    # Verificar si ya hay un corte abierto para este usuario
    corte_abierto = get_current_open_corte_caja(usuario_id=current_user.id)
    if corte_abierto:
        flash(f'Ya tienes un corte de caja abierto (ID: {corte_abierto.id}). Debes cerrarlo antes de abrir uno nuevo.', 'warning')
        return redirect(url_for('caja.dashboard_caja'))

    form = AperturaCajaForm()
    if form.validate_on_submit():
        # Recopilar las denominaciones contadas del formulario
        denominaciones_contadas = form.get_denominaciones_contadas()

        # Llamar al servicio para realizar la apertura
        nuevo_corte = realizar_apertura_caja(
            usuario_id_responsable=current_user.id,
            saldo_inicial_contado_por_denominaciones=denominaciones_contadas,
            notas_apertura=form.notas_apertura.data
        )

        if nuevo_corte:
            flash(f'Apertura de caja realizada con éxito. Saldo inicial: {format_currency(nuevo_corte.saldo_inicial_efectivo_teorico)}', 'success')
            return redirect(url_for('caja.dashboard_caja'))
        else:
            # El servicio ya imprime un error, aquí mostramos un flash genérico
            flash('Error al realizar la apertura de caja. Por favor, verifica los datos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    return render_template('caja/apertura_caja.html', title='Apertura de Caja', form=form)

@caja.route('/cierre/<int:corte_id>', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CAJA)
def cierre_caja(corte_id):
    """
    Permite al usuario realizar el cierre de un periodo de caja abierto.
    """
    corte = get_corte_caja_by_id(corte_id)

    # Validar que el corte exista y esté abierto
    if not corte:
        flash('Corte de caja no encontrado.', 'warning')
        return redirect(url_for('caja.dashboard_caja'))

    if corte.estado_corte != EstadoCorteCaja.ABIERTO:
        flash(f'El corte de caja {corte.id} ya está cerrado.', 'warning')
        return redirect(url_for('caja.ver_corte', corte_id=corte.id)) # Redirigir a ver corte si ya está cerrado

    # Validar que el usuario actual sea el responsable del corte o un Admin
    if corte.usuario_id_responsable != current_user.id and current_user.rol != RolUsuario.ADMINISTRADOR.value:
         flash('No tienes permiso para cerrar este corte de caja.', 'danger')
         return redirect(url_for('caja.dashboard_caja'))


    form = CierreCajaForm()
    if form.validate_on_submit():
        # Recopilar las denominaciones contadas del formulario
        efectivo_contado_final = form.get_denominaciones_contadas()

        # Llamar al servicio para realizar el cierre
        corte_cerrado = realizar_cierre_de_caja(
            corte_caja_id_actual=corte.id,
            usuario_id_cierre=current_user.id,
            efectivo_contado_final_por_denominaciones=efectivo_contado_final,
            notas_cierre=form.notas_cierre.data
        )

        if corte_cerrado:
            flash(f'Corte de caja {corte_cerrado.id} realizado con éxito. Diferencia: {format_currency(corte_cerrado.diferencia_efectivo)}', 'success')
            return redirect(url_for('caja.ver_corte', corte_id=corte_cerrado.id)) # Redirigir a ver el corte cerrado
        else:
            # El servicio ya imprime un error, aquí mostramos un flash genérico
            flash('Error al realizar el cierre de caja. Por favor, verifica los datos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    # Si es GET o validación falla, mostrar el formulario
    # Opcional: Calcular y mostrar el saldo teórico actual en la plantilla GET
    movimientos_periodo = get_movimientos_for_corte(corte.id)
    total_ingresos_efectivo = sum(m.monto_movimiento for m in movimientos_periodo if m.tipo_movimiento == TipoMovimientoCaja.INGRESO and m.forma_pago_efectuado == FormaPago.EFECTIVO)
    total_egresos_efectivo = sum(m.monto_movimiento for m in movimientos_periodo if m.tipo_movimiento == TipoMovimientoCaja.EGRESO and m.forma_pago_efectuado == FormaPago.EFECTIVO)
    saldo_teorico_actual = corte.saldo_inicial_efectivo_teorico + total_ingresos_efectivo - total_egresos_efectivo


    return render_template(
        'caja/cierre_caja.html',
        title=f'Cierre de Caja #{corte.id}',
        form=form,
        corte=corte,
        saldo_teorico_actual=saldo_teorico_actual,
        format_currency=format_currency
    )


@caja.route('/movimiento', methods=['GET', 'POST'])
@login_required
@role_required(ROLES_CAJA)
def registrar_movimiento():
    """
    Permite registrar un movimiento de caja general (ingreso o egreso).
    """
    form = MovimientoCajaForm()
    if form.validate_on_submit():
        # Nota: Este formulario no captura denominaciones para movimientos generales en MVP
        # Si se necesitara, habría que modificar el formulario y esta lógica

        movimiento = registrar_movimiento_caja(
            usuario_id=current_user.id,
            tipo_movimiento=form.tipo_movimiento.data,
            motivo_movimiento=form.motivo_movimiento.data,
            monto_movimiento=form.monto_movimiento.data,
            forma_pago_efectuado=form.forma_pago_efectuado.data,
            notas_movimiento=form.notas_movimiento.data,
            pedido_id=None # Los movimientos generales no están asociados a un pedido específico
            # denominaciones_contadas=None # No se capturan en este formulario
        )

        if movimiento:
            flash(f'Movimiento de caja registrado con éxito: {movimiento.tipo_movimiento.name} de {format_currency(movimiento.monto_movimiento)}', 'success')
            return redirect(url_for('caja.dashboard_caja')) # O a una lista de movimientos
        else:
            flash('Error al registrar el movimiento de caja. Por favor, verifica los datos.', 'danger')
            # Mantener al usuario en la página con el formulario pre-llenado y errores

    return render_template('caja/registrar_movimiento.html', title='Registrar Movimiento de Caja', form=form)


@caja.route('/cortes')
@login_required
@role_required(RolUsuario.ADMINISTRADOR) # Solo Admin puede listar todos los cortes
def listar_cortes():
    """
    Muestra una lista paginada de todos los cortes de caja históricos.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Cortes por página
    cortes_pagination = get_all_cortes_caja(page=page, per_page=per_page)
    cortes = cortes_pagination.items

    return render_template(
        'caja/listar_cortes.html',
        title='Historial de Cortes de Caja',
        cortes=cortes,
        pagination=cortes_pagination,
        format_currency=format_currency,
        format_datetime=format_datetime
    )

@caja.route('/cortes/<int:corte_id>')
@login_required
@role_required(RolUsuario.ADMINISTRADOR) # Solo Admin puede ver detalles de cualquier corte
def ver_corte(corte_id):
    """
    Muestra los detalles de un corte de caja específico.
    """
    corte = get_corte_caja_by_id(corte_id)

    if not corte:
        flash('Corte de caja no encontrado.', 'warning')
        return redirect(url_for('caja.listar_cortes'))

    # Obtener movimientos y detalles de denominaciones para este corte
    movimientos = get_movimientos_for_corte(corte.id)
    # Los detalles de denominaciones ya están cargados en corte.detalle_denominaciones_cierre

    # Calcular totales por forma de pago para mostrar en el detalle
    totales_por_forma_pago = {}
    for forma_pago in FormaPago:
        total = sum(m.monto_movimiento for m in movimientos if m.tipo_movimiento == TipoMovimientoCaja.INGRESO and m.forma_pago_efectuado == forma_pago)
        if total > Decimal('0.00'):
            totales_por_forma_pago[forma_pago.name.replace('_', ' ').title()] = total

    # Calcular total contado por denominación para mostrar en el detalle
    conteo_final_denominaciones = {d.denominacion_valor: d.cantidad_contada for d in corte.detalle_denominaciones_cierre}


    return render_template(
        'caja/ver_corte.html',
        title=f'Detalle Corte de Caja #{corte.id}',
        corte=corte,
        movimientos=movimientos,
        totales_por_forma_pago=totales_por_forma_pago,
        conteo_final_denominaciones=conteo_final_denominaciones,
        format_currency=format_currency,
        format_datetime=format_datetime
    )

# Puedes añadir más rutas aquí según se necesiten
# Por ejemplo: ruta para listar movimientos generales, ruta para ajustes (solo Admin)
