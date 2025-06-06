from datetime import datetime
import enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy import UniqueConstraint, CheckConstraint, func, Numeric, Enum

# --- Definición de Enums (basado en Sección 7 de instrucciones) ---
class RolUsuario(enum.Enum):
    ADMINISTRADOR = 'ADMINISTRADOR'
    CAJERO = 'CAJERO'
    TABLAJERO = 'TABLAJERO'
    REPARTIDOR = 'REPARTIDOR'

class TipoCliente(enum.Enum):
    PUBLICO = 'PUBLICO'
    COCINA = 'COCINA'
    LEAL = 'LEAL'
    ALIADO = 'ALIADO'
    MAYOREO = 'MAYOREO'
    EMPLEADO = 'EMPLEADO'
    GENERICO_MOSTRADOR = 'GENERICO_MOSTRADOR'

class TipoTelefono(enum.Enum):
    CELULAR = 'CELULAR'
    WHATSAPP = 'WHATSAPP'
    CASA = 'CASA'
    NEGOCIO = 'NEGOCIO'

class TipoDireccion(enum.Enum):
    CASA = 'CASA'
    NEGOCIO = 'NEGOCIO'
    ENTREGA_PRINCIPAL = 'ENTREGA_PRINCIPAL'

class TipoVenta(enum.Enum):
    MOSTRADOR = 'MOSTRADOR'
    DOMICILIO = 'DOMICILIO'

class FormaPago(enum.Enum):
    EFECTIVO = 'EFECTIVO'
    TARJETA_DEBITO = 'TARJETA_DEBITO'
    TARJETA_CREDITO = 'TARJETA_CREDITO'
    TRANSFERENCIA_BANCARIA = 'TRANSFERENCIA_BANCARIA'
    QR_PAGO = 'QR_PAGO'
    CREDITO_INTERNO = 'CREDITO_INTERNO'
    CORTESIA = 'CORTESIA'
    PAGO_MULTIPLE = 'PAGO_MULTIPLE'
    GASTO_INTERNO_CAJA = 'GASTO_INTERNO_CAJA'
    AJUSTE_INGRESO_CAJA = 'AJUSTE_INGRESO_CAJA'
    AJUSTE_EGRESO_CAJA = 'AJUSTE_EGRESO_CAJA'
    SALDO_INICIAL_CAJA = 'SALDO_INICIAL_CAJA'
    RETIRO_EFECTIVO_CAJA = 'RETIRO_EFECTIVO_CAJA'
    EFECTIVO_CONTRA_ENTREGA = 'EFECTIVO_CONTRA_ENTREGA'


class EstadoPedido(enum.Enum):
    PENDIENTE_CONFIRMACION = 'PENDIENTE_CONFIRMACION'
    PENDIENTE_PREPARACION = 'PENDIENTE_PREPARACION'
    EN_PREPARACION = 'EN_PREPARACION'
    LISTO_PARA_ENTREGA = 'LISTO_PARA_ENTREGA'
    ASIGNADO_A_REPARTIDOR = 'ASIGNADO_A_REPARTIDOR'
    EN_RUTA = 'EN_RUTA'
    ENTREGADO_PENDIENTE_PAGO = 'ENTREGADO_PENDIENTE_PAGO'
    ENTREGADO_Y_PAGADO = 'ENTREGADO_Y_PAGADO'
    PAGADO = 'PAGADO' # Estado general de pago completado
    PROBLEMA_EN_ENTREGA = 'PROBLEMA_EN_ENTREGA'
    REPROGRAMADO = 'REPROGRAMADO'
    CANCELADO_POR_CLIENTE = 'CANCELADO_POR_CLIENTE'
    CANCELADO_POR_NEGOCIO = 'CANCELADO_POR_NEGOCIO'

class TipoMovimientoCaja(enum.Enum):
    INGRESO = 'INGRESO'
    EGRESO = 'EGRESO'

class EstadoCorteCaja(enum.Enum):
    ABIERTO = 'ABIERTO'
    CERRADO_CONCILIADO = 'CERRADO_CONCILIADO'
    CERRADO_CON_DIFERENCIA = 'CERRADO_CON_DIFERENCIA'

# --- Modelo Usuario ---
@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario dado su ID para Flask-Login."""
    # user_id viene como string, convertir a int
    if user_id is not None:
        return Usuario.query.get(int(user_id))
    return None

class Usuario(UserMixin, db.Model):
    """
    Almacena la información de los empleados que pueden acceder y operar el sistema.
    """
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    rol = db.Column(Enum(RolUsuario), nullable=False, index=True) # Usar Enum
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime, nullable=True)

    # Relaciones (completadas según Sección 3.1)
    pedidos_registrados = db.relationship('Pedido', foreign_keys='Pedido.usuario_id', back_populates='usuario_creador', lazy='dynamic')
    pedidos_asignados_repartidor = db.relationship('Pedido', foreign_keys='Pedido.repartidor_id', back_populates='repartidor_asignado', lazy='dynamic')
    movimientos_caja_registrados = db.relationship('MovimientoCaja', back_populates='usuario_responsable', lazy='dynamic')
    cortes_caja_realizados = db.relationship('CorteCaja', back_populates='usuario_responsable_corte', lazy='dynamic')


    def __repr__(self):
        return f'<Usuario {self.username} - Rol: {self.rol.value}>' # Usar .value para el Enum

    # Métodos sugeridos (Sección 3.1)
    def set_password(self, password):
        """Genera y establece el hash de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    # Métodos helper para verificar roles (Sección 3.1)
    def is_admin(self):
        return self.rol == RolUsuario.ADMINISTRADOR

    def is_cajero(self):
        return self.rol == RolUsuario.CAJERO

    def is_tablajero(self):
        return self.rol == RolUsuario.TABLAJERO

    def is_repartidor(self):
        return self.rol == RolUsuario.REPARTIDOR


# --- Modelo Cliente ---
class Cliente(db.Model):
    """
    Almacena la información de los clientes de Pollería Montiel.
    """
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    apellidos = db.Column(db.String(150), nullable=True, index=True)
    alias = db.Column(db.String(80), nullable=True, index=True)
    tipo_cliente = db.Column(Enum(TipoCliente), nullable=False, default=TipoCliente.PUBLICO, index=True) # Usar Enum
    notas_cliente = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones (completadas según Sección 3.2)
    telefonos = db.relationship('Telefono', back_populates='cliente', lazy='dynamic', cascade='all, delete-orphan')
    direcciones = db.relationship('Direccion', back_populates='cliente', lazy='dynamic', cascade='all, delete-orphan')
    pedidos = db.relationship('Pedido', back_populates='cliente', lazy='dynamic')

    def __repr__(self):
        return f'<Cliente {self.id}: {self.nombre} {self.apellidos or ""}>'

    # Métodos sugeridos (Sección 3.2)
    def get_nombre_completo(self):
        """Retorna nombre y apellidos concatenados."""
        if self.apellidos:
            return f"{self.nombre} {self.apellidos}"
        return self.nombre

    def get_telefono_principal(self):
        """Retorna el teléfono marcado como principal."""
        # Asumiendo que solo uno puede ser principal por lógica de aplicación
        return self.telefonos.filter_by(es_principal=True).first()

    def get_direccion_principal(self):
        """Retorna la dirección marcada como principal."""
        # Asumiendo que solo una puede ser principal por lógica de aplicación
        return self.direcciones.filter_by(es_principal=True).first()


# --- Modelo Telefono (Sección 3.3) ---
class Telefono(db.Model):
    """
    Almacena los números de teléfono asociados a un cliente.
    """
    __tablename__ = 'telefonos_cliente'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False, index=True)
    numero_telefono = db.Column(db.String(20), nullable=False, index=True)
    tipo_telefono = db.Column(Enum(TipoTelefono), nullable=False, default=TipoTelefono.CELULAR, index=True) # Usar Enum
    es_principal = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # Relaciones
    cliente = db.relationship('Cliente', back_populates='telefonos')

    # Constraints
    __table_args__ = (
        UniqueConstraint('cliente_id', 'numero_telefono', name='uq_cliente_numero_telefono'),
    )

    def __repr__(self):
        return f'<Telefono {self.id}: {self.numero_telefono} ({self.tipo_telefono.value}) - Cliente {self.cliente_id}>' # Usar .value


# --- Modelo Direccion (Sección 3.4) ---
class Direccion(db.Model):
    """
    Almacena las direcciones asociadas a un cliente.
    """
    __tablename__ = 'direcciones_cliente'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False, index=True)
    calle_numero = db.Column(db.String(200), nullable=False)
    colonia = db.Column(db.String(100), nullable=True, index=True)
    ciudad = db.Column(db.String(100), nullable=False, index=True)
    codigo_postal = db.Column(db.String(10), nullable=True, index=True)
    referencias = db.Column(db.Text, nullable=True)
    tipo_direccion = db.Column(Enum(TipoDireccion), nullable=False, default=TipoDireccion.CASA, index=True) # Usar Enum
    latitud = db.Column(Numeric(10, 7), nullable=True) # Usar Numeric para precisión
    longitud = db.Column(Numeric(10, 7), nullable=True) # Usar Numeric para precisión
    es_principal = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # Relaciones
    cliente = db.relationship('Cliente', back_populates='direcciones')

    def __repr__(self):
        return f'<Direccion {self.id}: {self.calle_numero}, {self.colonia}, {self.ciudad} - Cliente {self.cliente_id}>'


# --- Modelo Producto (Sección 3.5) ---
class Producto(db.Model):
    """
    Catálogo de los productos principales de pollo.
    """
    __tablename__ = 'productos'
    id = db.Column(db.String(10), primary_key=True) # Código ej: 'PECH'
    nombre = db.Column(db.String(100), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(50), nullable=False, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones (completadas según Sección 3.5)
    subproductos = db.relationship('Subproducto', back_populates='producto_padre', lazy='dynamic', cascade='all, delete-orphan')
    modificaciones_directas = db.relationship('Modificacion', secondary='producto_modificacion_association', back_populates='productos_asociados', lazy='dynamic')
    precios = db.relationship('Precio', foreign_keys='Precio.producto_id', back_populates='producto_base', lazy='dynamic', cascade='all, delete-orphan')
    items_pedido = db.relationship('PedidoItem', foreign_keys='PedidoItem.producto_id', back_populates='producto', lazy='dynamic')


    def __repr__(self):
        return f'<Producto {self.id}: {self.nombre}>'


# --- Modelo Subproducto (Sección 3.6) ---
class Subproducto(db.Model):
    """
    Partes o derivados específicos de un Producto principal, o "Especiales".
    """
    __tablename__ = 'subproductos'
    id = db.Column(db.Integer, primary_key=True)
    producto_padre_id = db.Column(db.String(10), db.ForeignKey('productos.id'), nullable=False, index=True)
    codigo_subprod = db.Column(db.String(15), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones
    producto_padre = db.relationship('Producto', back_populates='subproductos')
    modificaciones_aplicables = db.relationship('Modificacion', secondary='subproducto_modificacion_association', back_populates='subproductos_asociados', lazy='dynamic')
    precios = db.relationship('Precio', foreign_keys='Precio.subproducto_id', back_populates='subproducto_base', lazy='dynamic', cascade='all, delete-orphan')
    items_pedido = db.relationship('PedidoItem', back_populates='subproducto', lazy='dynamic') # <-- Asegurar que sea 'subproducto' aquí


    def __repr__(self):
        return f'<Subproducto {self.id}: {self.nombre} ({self.codigo_subprod}) - Padre: {self.producto_padre_id}>'


# --- Tablas de Asociación para Modificaciones (Many-to-Many) (Sección 3.7) ---
producto_modificacion_association = db.Table('producto_modificacion_association',
    db.Column('producto_id', db.String(10), db.ForeignKey('productos.id'), primary_key=True),
    db.Column('modificacion_id', db.Integer, db.ForeignKey('modificaciones.id'), primary_key=True)
)

subproducto_modificacion_association = db.Table('subproducto_modificacion_association',
    db.Column('subproducto_id', db.Integer, db.ForeignKey('subproductos.id'), primary_key=True),
    db.Column('modificacion_id', db.Integer, db.ForeignKey('modificaciones.id'), primary_key=True)
)


# --- Modelo Modificacion (Sección 3.7) ---
class Modificacion(db.Model):
    """
    Diferentes preparaciones, cortes o presentaciones aplicables a productos/subproductos.
    """
    __tablename__ = 'modificaciones'
    id = db.Column(db.Integer, primary_key=True)
    codigo_modif = db.Column(db.String(20), nullable=False, unique=True, index=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones
    productos_asociados = db.relationship('Producto', secondary='producto_modificacion_association', back_populates='modificaciones_directas', lazy='dynamic')
    subproductos_asociados = db.relationship('Subproducto', secondary='subproducto_modificacion_association', back_populates='modificaciones_aplicables', lazy='dynamic')
    items_pedido = db.relationship('PedidoItem', back_populates='modificacion_aplicada', lazy='dynamic')


    def __repr__(self):
        return f'<Modificacion {self.id}: {self.nombre} ({self.codigo_modif})>'


# --- Modelo Precio (Sección 3.8) ---
class Precio(db.Model):
    """
    Define el precio de un Producto o Subproducto por tipo de cliente y cantidad mínima.
    """
    __tablename__ = 'precios'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.String(10), db.ForeignKey('productos.id'), nullable=True, index=True)
    subproducto_id = db.Column(db.Integer, db.ForeignKey('subproductos.id'), nullable=True, index=True)
    tipo_cliente = db.Column(Enum(TipoCliente), nullable=False, index=True) # Usar Enum
    precio_kg = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric para precios
    cantidad_minima_kg = db.Column(Numeric(10, 3), nullable=False, default=0.0, index=True) # Usar Numeric para cantidades
    etiqueta_promo = db.Column(db.String(100), nullable=True)
    fecha_inicio_vigencia = db.Column(db.Date, nullable=True, index=True)
    fecha_fin_vigencia = db.Column(db.Date, nullable=True, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones
    producto_base = db.relationship('Producto', foreign_keys=[producto_id], back_populates='precios')
    subproducto_base = db.relationship('Subproducto', foreign_keys=[subproducto_id], back_populates='precios')

    # Constraints
    __table_args__ = (
        CheckConstraint('(producto_id IS NOT NULL AND subproducto_id IS NULL) OR (producto_id IS NULL AND subproducto_id IS NOT NULL)', name='chk_precio_target'),
        UniqueConstraint('producto_id', 'tipo_cliente', 'cantidad_minima_kg', name='uq_precio_prod'),
        UniqueConstraint('subproducto_id', 'tipo_cliente', 'cantidad_minima_kg', name='uq_precio_subprod')
    )

    def __repr__(self):
        target = f'Prod:{self.producto_id}' if self.producto_id else f'Subprod:{self.subproducto_id}'
        return f'<Precio {self.id}: {target} - Cliente: {self.tipo_cliente.value} - Min: {self.cantidad_minima_kg}kg - ${self.precio_kg:.2f}/kg>' # Usar .value


# --- Modelo Pedido (Sección 3.9) ---
class Pedido(db.Model):
    """
    Registra cada transacción de venta o solicitud de productos.
    """
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True) # Cajero/Admin que registra
    repartidor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True, index=True) # Repartidor asignado
    direccion_entrega_id = db.Column(db.Integer, db.ForeignKey('direcciones_cliente.id'), nullable=True, index=True)
    tipo_venta = db.Column(Enum(TipoVenta), nullable=False, index=True) # Usar Enum
    forma_pago = db.Column(Enum(FormaPago), nullable=True, index=True) # Usar Enum
    paga_con = db.Column(Numeric(10, 2), nullable=True) # Usar Numeric
    cambio_entregado = db.Column(Numeric(10, 2), nullable=True) # Usar Numeric
    subtotal_productos_pollo = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    subtotal_productos_adicionales = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    descuento_aplicado = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    costo_envio = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    total_pedido = db.Column(Numeric(10, 2), nullable=False, default=0.0, index=True) # Usar Numeric
    estado_pedido = db.Column(Enum(EstadoPedido), nullable=False, default=EstadoPedido.PENDIENTE_CONFIRMACION, index=True) # Usar Enum
    notas_pedido = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    fecha_actualizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    fecha_entrega_programada = db.Column(db.DateTime, nullable=True, index=True)
    requiere_factura = db.Column(db.Boolean, nullable=False, default=False)

    # Relaciones
    cliente = db.relationship('Cliente', back_populates='pedidos')
    usuario_creador = db.relationship('Usuario', foreign_keys=[usuario_id], back_populates='pedidos_registrados')
    repartidor_asignado = db.relationship('Usuario', foreign_keys=[repartidor_id], back_populates='pedidos_asignados_repartidor')
    direccion_entrega = db.relationship('Direccion') # Relación simple, no back_populates en Direccion
    items = db.relationship('PedidoItem', back_populates='pedido', lazy='dynamic', cascade='all, delete-orphan')
    productos_adicionales_pedido = db.relationship('ProductoAdicional', back_populates='pedido', lazy='dynamic', cascade='all, delete-orphan')
    movimientos_caja_asociados = db.relationship('MovimientoCaja', back_populates='pedido_asociado', lazy='dynamic')

    def __repr__(self):
        return f'<Pedido {self.id} - Estado: {self.estado_pedido.value} - Total: ${self.total_pedido:.2f}>' # Usar .value

    # Métodos sugeridos (Sección 3.9)
    def calcular_totales(self):
        """Recalcula los subtotales y el total general del pedido."""
        self.subtotal_productos_pollo = sum(item.subtotal_item for item in self.items)
        self.subtotal_productos_adicionales = sum(pa.subtotal_pa for pa in self.productos_adicionales_pedido)
        # Asegurar que costo_envio y descuento_aplicado no sean None si se usan
        costo_envio = self.costo_envio if self.costo_envio is not None else Numeric('0.0')
        descuento = self.descuento_aplicado if self.descuento_aplicado is not None else Numeric('0.0')
        self.total_pedido = (self.subtotal_productos_pollo + self.subtotal_productos_adicionales + costo_envio) - descuento

    def puede_ser_modificado(self):
        """Determina si el pedido puede ser modificado según su estado."""
        # Lógica para determinar si el pedido puede ser modificado
        # Por ejemplo, no se puede modificar si ya está EN_RUTA, ENTREGADO, CANCELADO, etc.
        estados_no_modificables = [
            EstadoPedido.EN_RUTA,
            EstadoPedido.ENTREGADO_PENDIENTE_PAGO,
            EstadoPedido.ENTREGADO_Y_PAGADO,
            EstadoPedido.PAGADO,
            EstadoPedido.PROBLEMA_EN_ENTREGA,
            EstadoPedido.CANCELADO_POR_CLIENTE,
            EstadoPedido.CANCELADO_POR_NEGOCIO
        ]
        return self.estado_pedido not in estados_no_modificables

    def generar_folio_display(self):
        """Genera un folio formateado para mostrar al usuario."""
        # Implementar lógica para generar folio formateado (ej. PM-000123)
        # Podría usar el id o un campo de folio separado si se necesita un formato específico no secuencial
        return f"PM-{self.id:06d}" # Ejemplo simple usando el ID


# --- Modelo PedidoItem (Sección 3.10) ---
class PedidoItem(db.Model):
    """
    Detalla cada producto de pollo incluido en un Pedido.
    """
    __tablename__ = 'pedido_items'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False, index=True)
    producto_id = db.Column(db.String(10), db.ForeignKey('productos.id'), nullable=True, index=True)
    subproducto_id = db.Column(db.Integer, db.ForeignKey('subproductos.id'), nullable=True, index=True)
    modificacion_id = db.Column(db.Integer, db.ForeignKey('modificaciones.id'), nullable=True, index=True)
    descripcion_item_venta = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(Numeric(10, 3), nullable=False) # Usar Numeric para cantidades
    unidad_medida = db.Column(db.String(10), nullable=False, default='kg')
    precio_unitario_venta = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric para precios
    subtotal_item = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric para subtotales
    costo_unitario_item = db.Column(Numeric(10, 2), nullable=True) # Opcional, usar Numeric

    # Relaciones
    pedido = db.relationship('Pedido', back_populates='items')
    producto = db.relationship('Producto', foreign_keys=[producto_id], back_populates='items_pedido')
    # CORRECCIÓN: Eliminar lazy='dynamic' de la relación many-to-one
    subproducto = db.relationship('Subproducto', foreign_keys=[subproducto_id], back_populates='items_pedido')
    modificacion_aplicada = db.relationship('Modificacion', back_populates='items_pedido')

    # Constraints
    __table_args__ = (
        # CheckConstraint actualizado para permitir solo producto_id O subproducto_id
        CheckConstraint('(producto_id IS NOT NULL AND subproducto_id IS NULL) OR (producto_id IS NULL AND subproducto_id IS NOT NULL)', name='chk_pedidoitem_target'),
        # La lógica para asegurar que si subproducto_id está presente, producto_id sea su padre, se maneja en la aplicación.
    )

    def __repr__(self):
        return f'<PedidoItem {self.id} - Pedido {self.pedido_id}: {self.descripcion_item_venta} x {self.cantidad} {self.unidad_medida}>'

    # Métodos sugeridos (Sección 3.10)
    def actualizar_subtotal(self):
        """Recalcula el subtotal del ítem."""
        # Asegurarse de que cantidad y precio_unitario_venta son Numeric antes de multiplicar
        cantidad = self.cantidad if self.cantidad is not None else Numeric('0.0')
        precio = self.precio_unitario_venta if self.precio_unitario_venta is not None else Numeric('0.0')
        self.subtotal_item = cantidad * precio


# --- Modelo ProductoAdicional (Sección 3.11) ---
class ProductoAdicional(db.Model):
    """
    Registra ítems que no forman parte del catálogo de pollo principal añadidos a un pedido.
    """
    __tablename__ = 'pedido_productos_adicionales'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False, index=True)
    nombre_pa = db.Column(db.String(150), nullable=False, index=True)
    cantidad_pa = db.Column(Numeric(10, 3), nullable=False, default=1.0) # Usar Numeric
    unidad_medida_pa = db.Column(db.String(20), nullable=False)
    costo_compra_unitario_pa = db.Column(Numeric(10, 2), nullable=True) # Costo para la pollería, usar Numeric
    precio_venta_unitario_pa = db.Column(Numeric(10, 2), nullable=False) # Precio al cliente, usar Numeric
    subtotal_pa = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    comision_calculada_pa = db.Column(Numeric(10, 2), nullable=True) # Monto de comisión aplicado, usar Numeric
    notas_pa = db.Column(db.Text, nullable=True)

    # Relaciones
    pedido = db.relationship('Pedido', back_populates='productos_adicionales_pedido')

    def __repr__(self):
        return f'<ProductoAdicional {self.id} - Pedido {self.pedido_id}: {self.nombre_pa} x {self.cantidad_pa} {self.unidad_medida_pa}>'

    # Métodos sugeridos (Sección 3.11)
    def calcular_subtotal_pa(self):
        """Recalcula el subtotal del producto adicional."""
        # Asegurarse de que cantidad_pa y precio_venta_unitario_pa son Numeric antes de multiplicar
        cantidad = self.cantidad_pa if self.cantidad_pa is not None else Numeric('0.0')
        precio = self.precio_venta_unitario_pa if self.precio_venta_unitario_pa is not None else Numeric('0.0')
        self.subtotal_pa = cantidad * precio


# --- Modelo MovimientoCaja (Sección 3.12) ---
class MovimientoCaja(db.Model):
    """
    Registra todas las entradas (ingresos) y salidas (egresos) de dinero de la caja.
    """
    __tablename__ = 'movimientos_caja'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=True, index=True)
    corte_caja_id = db.Column(db.Integer, db.ForeignKey('cortes_caja.id'), nullable=True, index=True)
    tipo_movimiento = db.Column(Enum(TipoMovimientoCaja), nullable=False, index=True) # Usar Enum
    motivo_movimiento = db.Column(db.String(255), nullable=False)
    monto_movimiento = db.Column(Numeric(10, 2), nullable=False, index=True) # Usar Numeric
    forma_pago_efectuado = db.Column(Enum(FormaPago), nullable=False, index=True) # Usar Enum
    fecha_movimiento = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    notas_movimiento = db.Column(db.Text, nullable=True)

    # Relaciones
    usuario_responsable = db.relationship('Usuario', back_populates='movimientos_caja_registrados')
    pedido_asociado = db.relationship('Pedido', back_populates='movimientos_caja_asociados')
    corte_caja_asignado = db.relationship('CorteCaja', back_populates='movimientos_del_corte')
    detalle_denominaciones = db.relationship('MovimientoDenominacion', back_populates='movimiento_caja_padre', lazy='dynamic', cascade='all, delete-orphan') # Solo si forma_pago_efectuado es 'EFECTIVO'

    def __repr__(self):
        return f'<MovimientoCaja {self.id}: {self.tipo_movimiento.value} ${self.monto_movimiento:.2f} - {self.motivo_movimiento}>' # Usar .value


# --- Modelo MovimientoDenominacion (Sección 3.13) ---
class MovimientoDenominacion(db.Model):
    """
    Detalla la cantidad de cada billete y moneda involucrada en un MovimientoCaja realizado en efectivo.
    """
    __tablename__ = 'movimiento_denominaciones'
    id = db.Column(db.Integer, primary_key=True)
    movimiento_caja_id = db.Column(db.Integer, db.ForeignKey('movimientos_caja.id'), nullable=False, index=True)
    denominacion_valor = db.Column(Numeric(10, 2), nullable=False, index=True) # Usar Numeric
    cantidad = db.Column(db.Integer, nullable=False) # Número de billetes/monedas

    # Relaciones
    movimiento_caja_padre = db.relationship('MovimientoCaja', back_populates='detalle_denominaciones')

    # Constraints
    __table_args__ = (
        UniqueConstraint('movimiento_caja_id', 'denominacion_valor', name='uq_movimiento_denominacion_detalle'),
    )

    def __repr__(self):
        return f'<MovDenom {self.id}: Mov {self.movimiento_caja_id} - ${self.denominacion_valor:.2f} x {self.cantidad}>'


# --- Modelo CorteCaja (Sección 3.14) ---
class CorteCaja(db.Model):
    """
    Registra el resultado de un arqueo o corte de caja.
    """
    __tablename__ = 'cortes_caja'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id_responsable = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha_apertura_periodo = db.Column(db.DateTime, nullable=False, index=True)
    fecha_cierre_corte = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    saldo_inicial_efectivo_teorico = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    total_ingresos_efectivo_periodo = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    total_egresos_efectivo_periodo = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    saldo_final_efectivo_teorico = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    saldo_final_efectivo_contado = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric
    diferencia_efectivo = db.Column(Numeric(10, 2), nullable=False, index=True) # Usar Numeric
    total_ingresos_tarjeta_periodo = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    total_ingresos_transfer_periodo = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    total_ingresos_otros_periodo = db.Column(Numeric(10, 2), nullable=False, default=0.0) # Usar Numeric
    # CORRECCIÓN: Cambiar EstadoCaja.ABIERTO a EstadoCorteCaja.ABIERTO
    estado_corte = db.Column(Enum(EstadoCorteCaja), nullable=False, default=EstadoCorteCaja.ABIERTO, index=True) # Usar Enum
    notas_corte = db.Column(db.Text, nullable=True)

    # Relaciones
    usuario_responsable_corte = db.relationship('Usuario', back_populates='cortes_caja_realizados')
    movimientos_del_corte = db.relationship('MovimientoCaja', back_populates='corte_caja_asignado', lazy='dynamic')
    detalle_denominaciones_cierre = db.relationship('DenominacionCorteCaja', back_populates='corte_caja_padre', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CorteCaja {self.id}: Fecha Cierre: {self.fecha_cierre_corte.strftime("%Y-%m-%d %H:%M")} - Diferencia: ${self.diferencia_efectivo:.2f}>'


# --- Modelo DenominacionCorteCaja (Sección 3.15) ---
class DenominacionCorteCaja(db.Model):
    """
    Detalla el conteo físico de cada billete y moneda al momento de realizar un CorteCaja.
    """
    __tablename__ = 'corte_caja_denominaciones'
    id = db.Column(db.Integer, primary_key=True)
    corte_caja_id = db.Column(db.Integer, db.ForeignKey('cortes_caja.id'), nullable=False, index=True)
    denominacion_valor = db.Column(Numeric(10, 2), nullable=False, index=True) # Usar Numeric
    cantidad_contada = db.Column(db.Integer, nullable=False)
    total_por_denominacion = db.Column(Numeric(10, 2), nullable=False) # Usar Numeric

    # Relaciones
    corte_caja_padre = db.relationship('CorteCaja', back_populates='detalle_denominaciones_cierre')

    # Constraints
    __table_args__ = (
        UniqueConstraint('corte_caja_id', 'denominacion_valor', name='uq_corte_denominacion_detalle'),
    )

    def __repr__(self):
        return f'<DenomCorte {self.id}: Corte {self.corte_caja_id} - ${self.denominacion_valor:.2f} x {self.cantidad_contada}>'


# --- Modelo ConfiguracionSistema (Sección 3.16) ---
class ConfiguracionSistema(db.Model):
    """
    Almacena parámetros y configuraciones globales del sistema.
    Diseñado como una tabla con una única fila.
    """
    __tablename__ = 'configuracion_sistema'
    id = db.Column(db.Integer, primary_key=True, default=1) # Siempre 1 para una única fila
    nombre_negocio = db.Column(db.String(150), nullable=False, default='Pollería Montiel')
    direccion_negocio = db.Column(db.String(255), nullable=True)
    telefono_negocio = db.Column(db.String(50), nullable=True)
    rfc_negocio = db.Column(db.String(13), nullable=True)
    limite_items_pa_sin_comision = db.Column(db.Integer, nullable=False, default=3)
    monto_comision_fija_pa_extra = db.Column(Numeric(10, 2), nullable=False, default=4.0) # Usar Numeric
    mensaje_whatsapp_confirmacion = db.Column(db.Text, nullable=True, default='Hola {{cliente_nombre}}! Tu pedido #{{pedido_id}} de Pollería Montiel ha sido confirmado. Total: ${{pedido_total}}. Gracias!')
    porcentaje_iva = db.Column(Numeric(5, 2), nullable=False, default=16.0) # Usar Numeric para porcentaje
    permitir_venta_sin_stock = db.Column(db.Boolean, nullable=False, default=True)
    ultimo_folio_pedido = db.Column(db.Integer, nullable=False, default=0)

    # Constraints
    __table_args__ = (
        CheckConstraint('id = 1', name='chk_single_row_config'), # Asegura que solo haya una fila
    )

    def __repr__(self):
        return f'<ConfiguracionSistema id={self.id}>'
