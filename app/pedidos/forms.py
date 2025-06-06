# Archivo: PolleriaMontiel\app\pedidos\forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, BooleanField, DecimalField, HiddenField, DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, NumberRange
from wtforms.widgets import NumberInput
from app.models import Cliente, Direccion, Usuario, Producto, Subproducto, Modificacion, TipoVenta, FormaPago, EstadoPedido # Importar modelos y Enums
from decimal import Decimal
from datetime import datetime # Para el default de DateTimeLocalField

# Nota: La selección de Producto/Subproducto/Modificacion en PedidoItemForm
# y la selección de Cliente/Direccion/Repartidor en PedidoForm
# a menudo implican lógica dinámica en el frontend (ej. autocompletado, selectores encadenados)
# que no se refleja completamente en la definición estática del formulario WTForms.
# Los campos aquí definidos representan los datos que se enviarán.

class PedidoForm(FlaskForm):
    """
    Formulario para crear o editar un pedido principal.
    """
    # Campo para seleccionar cliente (puede ser autocompletado en UI)
    # En el formulario, podríamos usar un SelectField poblado dinámicamente o un HiddenField con validación
    # Usaremos un campo de texto para búsqueda/autocompletado y un HiddenField para el ID seleccionado
    cliente_search = StringField(
        'Buscar Cliente',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "Nombre, alias o teléfono del cliente"}
    )
    cliente_id = HiddenField(validators=[Optional()]) # Para almacenar el ID del cliente seleccionado

    # Campo para seleccionar dirección de entrega (dinámico basado en cliente_id)
    # Similar al cliente, puede ser un SelectField dinámico o HiddenField
    direccion_entrega_search = StringField(
        'Buscar Dirección de Entrega',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "Dirección del cliente (para domicilio)"}
    )
    direccion_entrega_id = HiddenField(validators=[Optional()]) # Para almacenar el ID de la dirección seleccionada

    # Campo para seleccionar repartidor (si tipo_venta es DOMICILIO)
    # Puede ser un SelectField poblado con usuarios con rol REPARTIDOR
    repartidor_id = SelectField(
        'Repartidor Asignado',
        coerce=int, # Asegura que el valor sea un entero
        validators=[Optional()],
        # Las choices se poblarán dinámicamente en la ruta
        choices=[(0, 'Seleccionar Repartidor')] # Opción por defecto
    )

    tipo_venta = SelectField(
        'Tipo de Venta',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in TipoVenta],
        validators=[DataRequired()]
    )

    forma_pago = SelectField(
        'Forma de Pago Principal',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in FormaPago],
        validators=[Optional()] # Puede ser nulo inicialmente para pago contra entrega
    )

    paga_con = DecimalField(
        'Paga Con (Efectivo)',
        validators=[Optional(), NumberRange(min=Decimal('0.00'), message='El monto debe ser positivo.')],
        render_kw={"placeholder": "Monto recibido"},
        widget=NumberInput(step='0.01')
    )

    # cambio_entregado no es un campo de entrada, se calcula y muestra

    descuento_aplicado = DecimalField(
        'Descuento Aplicado',
        validators=[Optional(), NumberRange(min=Decimal('0.00'), message='El descuento no puede ser negativo.')],
        default=Decimal('0.00'),
        render_kw={"placeholder": "Monto de descuento"},
        widget=NumberInput(step='0.01')
    )

    costo_envio = DecimalField(
        'Costo de Envío',
        validators=[Optional(), NumberRange(min=Decimal('0.00'), message='El costo de envío no puede ser negativo.')],
        default=Decimal('0.00'),
        render_kw={"placeholder": "Costo de envío"},
        widget=NumberInput(step='0.01')
    )

    # Los subtotales y total_pedido no son campos de entrada, se calculan y muestran/guardan

    estado_pedido = SelectField(
        'Estado del Pedido',
        choices=[(choice.value, choice.name.replace('_', ' ').title()) for choice in EstadoPedido],
        validators=[DataRequired()]
        # Las opciones disponibles pueden depender del estado actual y el rol del usuario (lógica en ruta)
    )

    notas_pedido = TextAreaField(
        'Notas del Pedido',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 3, "placeholder": "Observaciones generales del pedido"}
    )

    fecha_entrega_programada = DateTimeLocalField(
        'Fecha y Hora de Entrega Programada',
        validators=[Optional()],
        format='%Y-%m-%dT%H:%M' # Formato compatible con input type="datetime-local"
    )

    requiere_factura = BooleanField('Requiere Factura', default=False)

    submit = SubmitField('Guardar Pedido')

    # Validaciones adicionales (ej. cliente_id es requerido si tipo_venta es DOMICILIO)
    def validate_cliente_id(self, cliente_id):
        if self.tipo_venta.data == TipoVenta.DOMICILIO.value and not cliente_id.data:
            raise ValidationError('Debe seleccionar un cliente para pedidos a domicilio.')
        if cliente_id.data:
            try:
                cliente = Cliente.query.get(int(cliente_id.data))
                if not cliente:
                     raise ValidationError('Cliente seleccionado no válido.')
            except ValueError:
                 raise ValidationError('ID de cliente no válido.')


    def validate_direccion_entrega_id(self, direccion_entrega_id):
        if self.tipo_venta.data == TipoVenta.DOMICILIO.value and not direccion_entrega_id.data:
            raise ValidationError('Debe seleccionar una dirección de entrega para pedidos a domicilio.')
        if direccion_entrega_id.data:
            try:
                direccion = Direccion.query.get(int(direccion_entrega_id.data))
                if not direccion:
                     raise ValidationError('Dirección de entrega seleccionada no válida.')
                # Opcional: Validar que la dirección pertenezca al cliente seleccionado
                # if self.cliente_id.data and direccion.cliente_id != int(self.cliente_id.data):
                #      raise ValidationError('La dirección seleccionada no pertenece al cliente.')
            except ValueError:
                 raise ValidationError('ID de dirección de entrega no válido.')


    def validate_repartidor_id(self, repartidor_id):
        # Validar que si el estado implica asignación, haya un repartidor seleccionado
        estados_con_repartidor = [
            EstadoPedido.ASIGNADO_A_REPARTIDOR.value,
            EstadoPedido.EN_RUTA.value,
            EstadoPedido.ENTREGADO_PENDIENTE_PAGO.value,
            EstadoPedido.PROBLEMA_EN_ENTREGA.value,
            EstadoPedido.REPROGRAMADO.value # Si se reprograma y ya estaba asignado
        ]
        if self.estado_pedido.data in estados_con_repartidor and (not repartidor_id.data or int(repartidor_id.data) == 0):
             raise ValidationError('Debe asignar un repartidor para este estado del pedido.')

        if repartidor_id.data and int(repartidor_id.data) != 0: # 0 es el valor por defecto "Seleccionar"
            try:
                repartidor = Usuario.query.get(int(repartidor_id.data))
                if not repartidor:
                     raise ValidationError('Usuario seleccionado no válido.')
                # Opcional: Validar que el usuario seleccionado sea realmente un repartidor
                # if not repartidor.is_repartidor():
                #      raise ValidationError('Usuario seleccionado no es un repartidor válido.')
            except ValueError:
                 raise ValidationError('ID de repartidor no válido.')


    def validate_forma_pago(self, forma_pago):
        # Opcional: Validar que si el estado es PAGADO, la forma de pago no sea nula
        # if self.estado_pedido.data in [EstadoPedido.PAGADO.value, EstadoPedido.ENTREGADO_Y_PAGADO.value] and not forma_pago.data:
        #      raise ValidationError('Debe especificar la forma de pago para pedidos pagados.')
        pass


class PedidoItemForm(FlaskForm):
    """
    Formulario para añadir o editar un ítem de producto de pollo en un pedido.
    """
    # Campos para seleccionar Producto/Subproducto/Modificacion (dinámicos en UI)
    # Usaremos HiddenFields para los IDs seleccionados y campos de texto para búsqueda/display
    producto_search = StringField(
        'Buscar Producto/Subproducto',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "Código o nombre del producto/subproducto"}
    )
    producto_id = HiddenField(validators=[Optional()]) # ID del Producto base
    subproducto_id = HiddenField(validators=[Optional()]) # ID del Subproducto

    modificacion_search = StringField(
        'Buscar Modificación',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "Modificación (ej. Molida, Para Asar)"}
    )
    modificacion_id = HiddenField(validators=[Optional()]) # ID de la Modificación

    # descripcion_item_venta se genera automáticamente en la lógica de negocio

    cantidad = DecimalField(
        'Cantidad',
        validators=[DataRequired(), NumberRange(min=Decimal('0.001'), message='La cantidad debe ser positiva.')],
        render_kw={"placeholder": "Ej. 1.5"},
        widget=NumberInput(step='0.001') # Permite 3 decimales para kg
    )

    unidad_medida = SelectField(
        'Unidad',
        choices=[('kg', 'kg'), ('pieza', 'pieza'), ('paquete', 'paquete')], # Definir unidades comunes
        validators=[DataRequired()]
    )

    precio_unitario_venta = DecimalField(
        'Precio Unitario',
        validators=[DataRequired(), NumberRange(min=Decimal('0.00'), message='El precio no puede ser negativo.')],
        render_kw={"placeholder": "Precio por unidad"},
        widget=NumberInput(step='0.01')
        # Este campo podría ser de solo lectura si el precio se calcula automáticamente
        # o editable para ajustes manuales (requiere permiso de Admin/Cajero)
    )

    # subtotal_item se calcula automáticamente

    notas_item = TextAreaField(
        'Notas del Ítem',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 2, "placeholder": "Notas específicas para este ítem"}
    )

    submit = SubmitField('Añadir Ítem')

    # Validaciones adicionales (ej. producto_id O subproducto_id es requerido)
    def validate(self):
        if not FlaskForm.validate(self):
            return False

        # Asegurar que se seleccionó un Producto o un Subproducto
        if not self.producto_id.data and not self.subproducto_id.data:
            self.producto_search.errors.append('Debe seleccionar un producto o subproducto.')
            return False

        # Asegurar que no se seleccionaron ambos (si la lógica de negocio lo prohíbe)
        # if self.producto_id.data and self.subproducto_id.data:
        #      # Esto puede ocurrir si la UI permite seleccionar ambos, la lógica de negocio debe manejarlo
        #      # o se añade una validación más compleja aquí si es necesario
        #      pass # Permitimos ambos por ahora si el modelo lo permite, la lógica de negocio refinará

        # Validar que los IDs seleccionados existan en la BD
        if self.producto_id.data:
            producto = Producto.query.get(self.producto_id.data)
            if not producto:
                 self.producto_search.errors.append('Producto seleccionado no válido.')
                 # No retornar False inmediatamente para acumular otros errores
                 # return False

        if self.subproducto_id.data:
            try:
                subproducto = Subproducto.query.get(int(self.subproducto_id.data))
                if not subproducto:
                     self.producto_search.errors.append('Subproducto seleccionado no válido.')
                     # return False
                # Opcional: Validar que el subproducto pertenezca al producto padre si ambos están presentes
                # if self.producto_id.data and subproducto.producto_padre_id != self.producto_id.data:
                #      self.producto_search.errors.append('El subproducto seleccionado no pertenece al producto padre.')
                #      return False
            except ValueError:
                 self.producto_search.errors.append('ID de subproducto no válido.')
                 # return False


        if self.modificacion_id.data:
            try:
                modificacion = Modificacion.query.get(int(self.modificacion_id.data))
                if not modificacion:
                     self.modificacion_search.errors.append('Modificación seleccionada no válida.')
                     # return False
                # Opcional: Validar que la modificación sea aplicable al producto/subproducto seleccionado
                # if self.producto_id.data and modificacion not in producto.modificaciones_directas:
                #      self.modificacion_search.errors.append('La modificación no es aplicable a este producto.')
                #      return False
                # if self.subproducto_id.data and modificacion not in subproducto.modificaciones_aplicables:
                #      self.modificacion_search.errors.append('La modificación no es aplicable a este subproducto.')
                #      return False
            except ValueError:
                 self.modificacion_search.errors.append('ID de modificación no válido.')
                 # return False

        # Retornar True solo si no hay errores después de todas las validaciones
        return len(self.producto_search.errors) == 0 and len(self.modificacion_search.errors) == 0


class ProductoAdicionalForm(FlaskForm):
    """
    Formulario para añadir o editar un producto adicional en un pedido.
    """
    nombre_pa = StringField(
        'Nombre del Producto Adicional',
        validators=[DataRequired(), Length(max=150)],
        render_kw={"placeholder": "Ej. Jitomate, Coca-Cola 600ml"}
    )

    cantidad_pa = DecimalField(
        'Cantidad',
        validators=[DataRequired(), NumberRange(min=Decimal('0.001'), message='La cantidad debe ser positiva.')],
        default=Decimal('1.0'),
        render_kw={"placeholder": "Ej. 1, 0.5"},
        widget=NumberInput(step='0.001')
    )

    unidad_medida_pa = SelectField(
        'Unidad',
        choices=[('kg', 'kg'), ('pieza', 'pieza'), ('litro', 'litro'), ('paquete', 'paquete'), ('MONTO', 'MONTO')], # Definir unidades comunes
        validators=[DataRequired()]
    )

    costo_compra_unitario_pa = DecimalField(
        'Costo de Compra Unitario',
        validators=[Optional(), NumberRange(min=Decimal('0.00'), message='El costo no puede ser negativo.')],
        render_kw={"placeholder": "Costo para la pollería (opcional)"},
        widget=NumberInput(step='0.01')
        # Este campo solo debería ser visible/editable para roles con permiso (ej. Admin, Cajero)
    )

    precio_venta_unitario_pa = DecimalField(
        'Precio de Venta Unitario',
        validators=[DataRequired(), NumberRange(min=Decimal('0.00'), message='El precio no puede ser negativo.')],
        render_kw={"placeholder": "Precio al cliente"},
        widget=NumberInput(step='0.01')
        # Este campo puede ser calculado automáticamente si se ingresa costo_compra_unitario_pa
        # o editable directamente
    )

    # subtotal_pa se calcula automáticamente
    # comision_calculada_pa se calcula automáticamente

    notas_pa = TextAreaField(
        'Notas del PA',
        validators=[Optional(), Length(max=500)],
        render_kw={"rows": 2, "placeholder": "Notas específicas para este PA"}
    )

    submit = SubmitField('Añadir Producto Adicional')

    # Validaciones adicionales (ej. si unidad es MONTO, cantidad_pa debe ser 1)
    def validate_cantidad_pa(self, cantidad_pa):
        if self.unidad_medida_pa.data == 'MONTO' and cantidad_pa.data != Decimal('1.0'):
            raise ValidationError('Si la unidad es MONTO, la cantidad debe ser 1.')

    def validate_precio_venta_unitario_pa(self, precio_venta_unitario_pa):
        # Si la unidad es MONTO, el precio_venta_unitario_pa es el monto total
        if self.unidad_medida_pa.data == 'MONTO' and precio_venta_unitario_pa.data is None:
             raise ValidationError('Debe especificar el monto total para esta unidad.')
