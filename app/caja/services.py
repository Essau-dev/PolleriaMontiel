# Archivo: PolleriaMontiel\app\caja\services.py

from app import db # Importar la instancia de SQLAlchemy
from app.models import (
    MovimientoCaja, CorteCaja, DenominacionCorteCaja, MovimientoDenominacion,
    Usuario, Pedido, TipoMovimientoCaja, FormaPago, EstadoCorteCaja
) # Importar los modelos y Enums necesarios
from app.caja.forms import DENOMINACIONES_MXN_ORDENADAS # Importar la lista de denominaciones
from decimal import Decimal # Importar Decimal para cálculos monetarios precisos
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Union

# --- Funciones de Ayuda Internas ---

def _create_movimiento_denominaciones(movimiento_caja_id: int, denominaciones_contadas: Dict[Decimal, int]):
    """Crea registros MovimientoDenominacion para un movimiento de caja en efectivo."""
    denominacion_records = []
    for valor, cantidad in denominaciones_contadas.items():
        if cantidad > 0:
            denominacion_records.append(MovimientoDenominacion(
                movimiento_caja_id=movimiento_caja_id,
                denominacion_valor=valor,
                cantidad=cantidad
            ))
    if denominacion_records:
        db.session.add_all(denominacion_records)

def _create_corte_denominaciones(corte_caja_id: int, denominaciones_contadas: Dict[Decimal, int]):
    """Crea registros DenominacionCorteCaja para el conteo de un corte de caja."""
    denominacion_records = []
    for valor, cantidad in denominaciones_contadas.items():
        if cantidad > 0:
            denominacion_records.append(DenominacionCorteCaja(
                corte_caja_id=corte_caja_id,
                denominacion_valor=valor,
                cantidad_contada=cantidad,
                total_por_denominacion=valor * Decimal(str(cantidad))
            ))
    if denominacion_records:
        db.session.add_all(denominacion_records)

def _get_total_efectivo_contado(denominaciones_contadas: Dict[Decimal, int]) -> Decimal:
    """Calcula el total de efectivo a partir de un diccionario de denominaciones contadas."""
    total = Decimal('0.00')
    for valor, cantidad in denominaciones_contadas.items():
        total += valor * Decimal(str(cantidad))
    return total

# --- Funciones de Servicio Principales ---

def get_current_open_corte_caja(usuario_id: Optional[int] = None) -> Optional[CorteCaja]:
    """
    Busca el CorteCaja actualmente abierto para un usuario específico o el último abierto.
    Para MVP, asumimos un solo corte abierto a la vez, posiblemente por usuario.
    """
    query = CorteCaja.query.filter_by(estado_corte=EstadoCorteCaja.ABIERTO)
    if usuario_id:
        query = query.filter_by(usuario_id_responsable=usuario_id)
    # Podría haber lógica para determinar el "corte actual" si hay múltiples usuarios/cajas
    # Para MVP, tomamos el último abierto si no se especifica usuario
    corte = query.order_by(CorteCaja.fecha_apertura_periodo.desc()).first()
    return corte

def get_corte_caja_by_id(corte_id: int) -> Optional[CorteCaja]:
    """Obtiene un CorteCaja por su ID."""
    return CorteCaja.query.get(corte_id)

def get_movimientos_for_corte(corte_id: int) -> List[MovimientoCaja]:
    """Obtiene todos los MovimientoCaja asociados a un CorteCaja."""
    return MovimientoCaja.query.filter_by(corte_caja_id=corte_id).all()

def get_all_cortes_caja(page: int = 1, per_page: int = 10):
    """Obtiene todos los CortesCaja con paginación."""
    return CorteCaja.query.order_by(CorteCaja.fecha_cierre_corte.desc()).paginate(page=page, per_page=per_page, error_out=False)


def registrar_movimiento_caja(
    usuario_id: int,
    tipo_movimiento: str, # Valor del Enum TipoMovimientoCaja
    motivo_movimiento: str,
    monto_movimiento: Decimal,
    forma_pago_efectuado: str, # Valor del Enum FormaPago
    notas_movimiento: Optional[str] = None,
    pedido_id: Optional[int] = None,
    denominaciones_contadas: Optional[Dict[Decimal, int]] = None # Solo para efectivo
) -> Optional[MovimientoCaja]:
    """
    Registra un nuevo movimiento de caja (ingreso o egreso).

    Args:
        usuario_id: ID del usuario que registra el movimiento.
        tipo_movimiento: Tipo de movimiento ('INGRESO' o 'EGRESO').
        motivo_movimiento: Descripción del motivo.
        monto_movimiento: Monto del movimiento.
        forma_pago_efectuado: Forma de pago/egreso.
        notas_movimiento: Notas adicionales (opcional).
        pedido_id: ID del pedido asociado (opcional).
        denominaciones_contadas: Diccionario {valor: cantidad} si es efectivo (opcional).

    Returns:
        El objeto MovimientoCaja creado si tiene éxito, None si hay un error.
    """
    try:
        # Validar que el tipo de movimiento y forma de pago sean válidos
        TipoMovimientoCaja(tipo_movimiento)
        FormaPago(forma_pago_efectuado)

        # Buscar el corte de caja abierto actual para asociar el movimiento en tiempo real
        # Esto es una mejora sobre la lógica de asociar al cierre
        current_corte = get_current_open_corte_caja(usuario_id=usuario_id)
        # Si no hay corte abierto, el movimiento no se asocia a un corte por ahora
        corte_caja_id = current_corte.id if current_corte else None

        movimiento = MovimientoCaja(
            usuario_id=usuario_id,
            pedido_id=pedido_id,
            corte_caja_id=corte_caja_id, # Asociar al corte abierto si existe
            tipo_movimiento=TipoMovimientoCaja(tipo_movimiento),
            motivo_movimiento=motivo_movimiento,
            monto_movimiento=monto_movimiento,
            forma_pago_efectuado=FormaPago(forma_pago_efectuado),
            notas_movimiento=notas_movimiento,
            fecha_movimiento=datetime.utcnow()
        )

        db.session.add(movimiento)
        db.session.flush() # Obtener el ID del movimiento antes de commitear

        # Si es efectivo y se proporcionaron denominaciones, registrarlas
        if forma_pago_efectuado == FormaPago.EFECTIVO.value and denominaciones_contadas:
             _create_movimiento_denominaciones(movimiento.id, denominaciones_contadas)

        db.session.commit()
        return movimiento

    except ValueError as e:
        db.session.rollback()
        print(f"Error al registrar movimiento de caja: {e}")
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Error inesperado al registrar movimiento de caja: {e}")
        return None

def realizar_apertura_caja(
    usuario_id_responsable: int,
    saldo_inicial_contado_por_denominaciones: Dict[Decimal, int],
    notas_apertura: Optional[str] = None
) -> Optional[CorteCaja]:
    """
    Registra la apertura de un nuevo periodo de caja.

    Args:
        usuario_id_responsable: ID del usuario que realiza la apertura.
        saldo_inicial_contado_por_denominaciones: Diccionario {valor: cantidad} del efectivo contado.
        notas_apertura: Notas adicionales (opcional).

    Returns:
        El objeto CorteCaja creado si tiene éxito, None si ya hay un corte abierto o hay un error.
    """
    # Validar que no haya ya un corte abierto para este usuario (o globalmente si la lógica es así)
    existing_open_corte = get_current_open_corte_caja(usuario_id=usuario_id_responsable)
    if existing_open_corte:
        print(f"Error: Ya existe un corte de caja abierto (ID: {existing_open_corte.id}) para el usuario {usuario_id_responsable}.")
        return None

    saldo_inicial_efectivo_total = _get_total_efectivo_contado(saldo_inicial_contado_por_denominaciones)

    if saldo_inicial_efectivo_total <= Decimal('0.00'):
         print("Error: El saldo inicial contado debe ser mayor a cero para abrir la caja.")
         return None

    try:
        # Crear el registro CorteCaja
        corte = CorteCaja(
            usuario_id_responsable=usuario_id_responsable,
            fecha_apertura_periodo=datetime.utcnow(),
            # fecha_cierre_corte se deja NULL o se establece al cerrar
            saldo_inicial_efectivo_teorico=saldo_inicial_efectivo_total,
            total_ingresos_efectivo_periodo=Decimal('0.00'), # Inicia en 0
            total_egresos_efectivo_periodo=Decimal('0.00'), # Inicia en 0
            saldo_final_efectivo_teorico=saldo_inicial_efectivo_total, # Teórico inicial = contado inicial
            saldo_final_efectivo_contado=saldo_inicial_efectivo_total, # Contado inicial = teórico inicial
            diferencia_efectivo=Decimal('0.00'), # Inicialmente no hay diferencia
            total_ingresos_tarjeta_periodo=Decimal('0.00'), # Inicia en 0
            total_ingresos_transfer_periodo=Decimal('0.00'), # Inicia en 0
            total_ingresos_otros_periodo=Decimal('0.00'), # Inicia en 0
            estado_corte=EstadoCorteCaja.ABIERTO,
            notas_corte=notas_apertura # Usamos notas_corte para notas_apertura en el modelo
        )

        db.session.add(corte)
        db.session.flush() # Obtener el ID del corte

        # Crear los registros DenominacionCorteCaja para el conteo inicial
        _create_corte_denominaciones(corte.id, saldo_inicial_contado_por_denominaciones)

        # Registrar el MovimientoCaja de Saldo Inicial
        movimiento_inicial = MovimientoCaja(
            usuario_id=usuario_id_responsable,
            corte_caja_id=corte.id, # Asociar al corte recién creado
            tipo_movimiento=TipoMovimientoCaja.INGRESO,
            motivo_movimiento=FormaPago.SALDO_INICIAL_CAJA.name.replace('_', ' ').title(), # Usar el nombre del Enum como motivo
            monto_movimiento=saldo_inicial_efectivo_total,
            forma_pago_efectuado=FormaPago.SALDO_INICIAL_CAJA, # Usar el Enum
            notas_movimiento="Registro automático de saldo inicial al abrir caja.",
            fecha_movimiento=corte.fecha_apertura_periodo # Usar la misma fecha/hora que la apertura
        )
        db.session.add(movimiento_inicial)
        db.session.flush() # Obtener ID del movimiento inicial

        # Crear los MovimientoDenominacion para el movimiento inicial
        _create_movimiento_denominaciones(movimiento_inicial.id, saldo_inicial_contado_por_denominaciones)


        db.session.commit()
        return corte

    except Exception as e:
        db.session.rollback()
        print(f"Error al realizar apertura de caja: {e}")
        return None


def realizar_cierre_de_caja(
    corte_caja_id_actual: int,
    usuario_id_cierre: int,
    efectivo_contado_final_por_denominaciones: Dict[Decimal, int],
    notas_cierre: Optional[str] = None
) -> Optional[CorteCaja]:
    """
    Finaliza un periodo de caja, registra el conteo final y calcula la diferencia.

    Args:
        corte_caja_id_actual: ID del CorteCaja que está ABIERTO.
        usuario_id_cierre: ID del usuario que realiza el cierre.
        efectivo_contado_final_por_denominaciones: Diccionario {valor: cantidad} del efectivo contado al cierre.
        notas_cierre: Notas adicionales (opcional).

    Returns:
        El objeto CorteCaja actualizado si tiene éxito, None si el corte no existe, no está abierto o hay un error.
    """
    corte = get_corte_caja_by_id(corte_caja_id_actual)
    if not corte:
        print(f"Error: No se encontró el corte de caja con ID {corte_caja_id_actual}.")
        return None

    if corte.estado_corte != EstadoCorteCaja.ABIERTO:
        print(f"Error: El corte de caja {corte_caja_id_actual} no está ABIERTO.")
        return None

    saldo_final_efectivo_contado = _get_total_efectivo_contado(efectivo_contado_final_por_denominaciones)

    if saldo_final_efectivo_contado < Decimal('0.00'):
         print("Error: El saldo final contado no puede ser negativo.")
         return None

    try:
        # Calcular totales teóricos del periodo
        # Sumar movimientos de caja asociados a este corte O desde la fecha de apertura
        # Asumimos que los movimientos ya se asociaron al corte al crearse si estaba abierto
        movimientos_periodo = get_movimientos_for_corte(corte.id)

        total_ingresos_efectivo = Decimal('0.00')
        total_egresos_efectivo = Decimal('0.00')
        total_ingresos_tarjeta = Decimal('0.00')
        total_ingresos_transfer = Decimal('0.00')
        total_ingresos_otros = Decimal('0.00') # Para otras formas de pago no efectivo

        for mov in movimientos_periodo:
            if mov.forma_pago_efectuado == FormaPago.EFECTIVO:
                if mov.tipo_movimiento == TipoMovimientoCaja.INGRESO:
                    total_ingresos_efectivo += mov.monto_movimiento
                elif mov.tipo_movimiento == TipoMovimientoCaja.EGRESO:
                    total_egresos_efectivo += mov.monto_movimiento
            elif mov.forma_pago_efectuado == FormaPago.TARJETA_DEBITO or mov.forma_pago_efectuado == FormaPago.TARJETA_CREDITO:
                 if mov.tipo_movimiento == TipoMovimientoCaja.INGRESO:
                     total_ingresos_tarjeta += mov.monto_movimiento
            elif mov.forma_pago_efectuado == FormaPago.TRANSFERENCIA_BANCARIA:
                 if mov.tipo_movimiento == TipoMovimientoCaja.INGRESO:
                     total_ingresos_transfer += mov.monto_movimiento
            # Añadir lógica para otras formas de pago si es necesario

        # El saldo inicial teórico ya está en el registro del corte
        saldo_final_efectivo_teorico = corte.saldo_inicial_efectivo_teorico + total_ingresos_efectivo - total_egresos_efectivo
        diferencia_efectivo = saldo_final_efectivo_contado - saldo_final_efectivo_teorico

        # Actualizar el registro CorteCaja
        corte.fecha_cierre_corte = datetime.utcnow()
        corte.total_ingresos_efectivo_periodo = total_ingresos_efectivo
        corte.total_egresos_efectivo_periodo = total_egresos_efectivo
        corte.saldo_final_efectivo_teorico = saldo_final_efectivo_teorico
        corte.saldo_final_efectivo_contado = saldo_final_efectivo_contado
        corte.diferencia_efectivo = diferencia_efectivo
        corte.total_ingresos_tarjeta_periodo = total_ingresos_tarjeta # Actualizar con totales calculados
        corte.total_ingresos_transfer_periodo = total_ingresos_transfer # Actualizar con totales calculados
        # Actualizar otros totales si aplica

        # Determinar estado del corte
        # Usar un pequeño umbral para considerar "conciliado" si la diferencia es mínima
        umbral_diferencia = Decimal('0.01') # 1 centavo
        if abs(diferencia_efectivo) <= umbral_diferencia:
            corte.estado_corte = EstadoCorteCaja.CERRADO_CONCILIADO
            corte.diferencia_efectivo = Decimal('0.00') # Forzar a 0 si está dentro del umbral
        else:
            corte.estado_corte = EstadoCorteCaja.CERRADO_CON_DIFERENCIA

        corte.notas_corte = notas_cierre # Usar notas_cierre para notas_corte

        # Eliminar conteos de denominaciones anteriores para este corte (si existían, ej. conteos parciales)
        # y crear los nuevos para el conteo final
        corte.detalle_denominaciones_cierre.delete() # Elimina los registros asociados
        _create_corte_denominaciones(corte.id, efectivo_contado_final_por_denominaciones)

        db.session.commit()
        return corte

    except Exception as e:
        db.session.rollback()
        print(f"Error al realizar cierre de caja para corte {corte_caja_id_actual}: {e}")
        return None


def calcular_y_sugerir_cambio_con_denominaciones(
    total_a_pagar: Decimal,
    monto_pagado_por_cliente: Decimal,
    existencias_denominaciones_en_caja: Dict[Decimal, int] # {valor: cantidad}
) -> Dict[str, Union[Decimal, Dict[Decimal, int], str, None]]:
    """
    Calcula el cambio a dar y sugiere denominaciones usando un algoritmo greedy.

    Args:
        total_a_pagar: Monto total del pedido.
        monto_pagado_por_cliente: Monto con el que paga el cliente.
        existencias_denominaciones_en_caja: Diccionario {valor: cantidad} de efectivo disponible.

    Returns:
        Diccionario con 'cambio_total', 'denominaciones_a_entregar', 'mensaje_error'.
    """
    cambio_a_dar = monto_pagado_por_cliente - total_a_pagar
    cambio_a_dar = round(cambio_a_dar, 2) # Redondear para precisión

    if cambio_a_dar < Decimal('0.00'):
        return {'cambio_total': Decimal('0.00'), 'denominaciones_a_entregar': {}, 'mensaje_error': "Monto pagado insuficiente."}

    if cambio_a_dar == Decimal('0.00'):
        return {'cambio_total': Decimal('0.00'), 'denominaciones_a_entregar': {}, 'mensaje_error': None}

    denominaciones_a_entregar: Dict[Decimal, int] = {}
    cambio_restante = cambio_a_dar
    existencias_mutables = existencias_denominaciones_en_caja.copy() # No modificar el dict original

    # Usar la lista ordenada de denominaciones
    for valor_denominacion_actual, _ in DENOMINACIONES_MXN_ORDENADAS:
        valor_decimal = Decimal(str(valor_denominacion_actual)) # Asegurar que sea Decimal
        if cambio_restante >= valor_decimal and existencias_mutables.get(valor_decimal, 0) > 0:
            # Calcular cuántas unidades de esta denominación se necesitan teóricamente
            cantidad_maxima_teorica = int(cambio_restante / valor_decimal)
            # Usar la menor cantidad entre la teórica y la disponible en caja
            cantidad_a_usar = min(cantidad_maxima_teorica, existencias_mutables.get(valor_decimal, 0))

            if cantidad_a_usar > 0:
                denominaciones_a_entregar[valor_decimal] = cantidad_a_usar
                cambio_restante -= Decimal(str(cantidad_a_usar)) * valor_decimal
                cambio_restante = round(cambio_restante, 2) # Redondear después de la resta

    # Verificar si quedó un remanente significativo
    umbral_error_flotante = Decimal('0.01') # Permitir una pequeña tolerancia
    if cambio_restante > umbral_error_flotante:
        return {
            'cambio_total': cambio_a_dar,
            'denominaciones_a_entregar': {}, # No sugerir nada si no se puede dar exacto
            'mensaje_error': f"No se puede dar cambio exacto con las denominaciones disponibles. Faltan: ${cambio_restante:.2f}"
        }
    else:
        # Si el remanente es muy pequeño, se considera que se pudo dar el cambio exacto
        return {
            'cambio_total': cambio_a_dar,
            'denominaciones_a_entregar': denominaciones_a_entregar,
            'mensaje_error': None
        }

# --- Funciones Específicas para Flujo de PAs y Repartidores (Sección 4.5) ---

def registrar_egreso_compra_pa(
    usuario_id_cajero: int,
    pedido_id: int,
    nombre_pa: str,
    costo_compra: Decimal,
    denominaciones_usadas: Dict[Decimal, int] # {valor: cantidad}
) -> Optional[MovimientoCaja]:
    """
    Registra un egreso de caja por la compra de un Producto Adicional para un pedido.
    """
    motivo = f"Compra PA para Pedido #{pedido_id} - {nombre_pa}"
    # El monto del movimiento es el costo de compra
    monto = costo_compra
    forma_pago = FormaPago.EFECTIVO.value # Asumimos efectivo para este egreso

    # Reutilizamos la función general de registro de movimiento
    movimiento = registrar_movimiento_caja(
        usuario_id=usuario_id_cajero,
        tipo_movimiento=TipoMovimientoCaja.EGRESO.value,
        motivo_movimiento=motivo,
        monto_movimiento=monto,
        forma_pago_efectuado=forma_pago,
        pedido_id=pedido_id,
        denominaciones_contadas=denominaciones_usadas # Detalle de billetes/monedas usados
    )
    return movimiento

def registrar_ingreso_liquidacion_repartidor(
    usuario_id_repartidor_o_cajero: int, # Puede ser el repartidor o el cajero que recibe
    pedido_id: int,
    monto_recibido: Decimal,
    denominaciones_recibidas: Dict[Decimal, int] # {valor: cantidad}
) -> Optional[MovimientoCaja]:
    """
    Registra un ingreso de caja por la liquidación de un pedido a domicilio por un repartidor.
    """
    # Podríamos obtener el nombre del repartidor si el usuario_id es el del repartidor
    usuario = Usuario.query.get(usuario_id_repartidor_o_cajero)
    nombre_usuario = usuario.nombre_completo if usuario else "Usuario Desconocido"

    motivo = f"Liquidación Pedido Domicilio #{pedido_id} por {nombre_usuario}"
    # El monto del movimiento es el total de efectivo entregado por el repartidor
    monto = monto_recibido
    forma_pago = FormaPago.EFECTIVO.value # Asumimos efectivo para esta liquidación

    # Reutilizamos la función general de registro de movimiento
    movimiento = registrar_movimiento_caja(
        usuario_id=usuario_id_repartidor_o_cajero,
        tipo_movimiento=TipoMovimientoCaja.INGRESO.value,
        motivo_movimiento=motivo,
        monto_movimiento=monto,
        forma_pago_efectuado=forma_pago,
        pedido_id=pedido_id,
        denominaciones_contadas=denominaciones_recibidas # Detalle de billetes/monedas recibidos
    )
    return movimiento

# Puedes añadir más funciones de servicio aquí según se necesiten
# Por ejemplo: get_movimientos_by_date_range, get_corte_summary, etc.