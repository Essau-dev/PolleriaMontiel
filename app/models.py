
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

# --- Modelo Usuario ---
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    rol = db.Column(db.String(30), nullable=False, index=True) # 'ADMINISTRADOR', 'CAJERO', etc.
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime, nullable=True)

    # Relaciones (ejemplos, se completarán según Sección 3 del doc)
    # pedidos_registrados = db.relationship('Pedido', foreign_keys='Pedido.usuario_id', backref='usuario_creador', lazy='dynamic')

    def __repr__(self):
        return f'<Usuario {self.username} ({self.rol})>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Helper para roles (se puede mejorar con una tabla de Roles y Permisos)
    def has_role(self, role_name):
        return self.rol == role_name

# --- Modelo Cliente (Ejemplo Inicial) ---
class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, index=True)
    apellidos = db.Column(db.String(150), nullable=True, index=True)
    alias = db.Column(db.String(80), nullable=True, index=True)
    tipo_cliente = db.Column(db.String(50), nullable=False, default='PUBLICO', index=True)
    notas_cliente = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones
    # telefonos = db.relationship('Telefono', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    # direcciones = db.relationship('Direccion', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')
    # pedidos = db.relationship('Pedido', backref='cliente', lazy='dynamic')

    def __repr__(self):
        return f'<Cliente {self.id}: {self.nombre} {self.apellidos or ""}>'

# --- Modelo Producto (Ejemplo Inicial) ---
class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.String(10), primary_key=True) # Código ej: 'PECH'
    nombre = db.Column(db.String(100), nullable=False, unique=True, index=True)
    descripcion = db.Column(db.Text, nullable=True)
    categoria = db.Column(db.String(50), nullable=False, index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)

    # Relaciones
    # subproductos = db.relationship('Subproducto', backref='producto_padre', lazy='dynamic', cascade='all, delete-orphan')
    # precios = db.relationship('Precio', foreign_keys='Precio.producto_id', backref='producto_base', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Producto {self.id}: {self.nombre}>'

# --- Más modelos (Subproducto, Modificacion, Precio, Pedido, etc.) se añadirán aquí ---
# --- basados en la Sección 3 del documento de especificaciones. ---

# Ejemplo de tabla de asociación (si no se usa backref directo en una relación N-M)
# producto_modificacion_association = db.Table('producto_modificacion_association',
#     db.Column('producto_id', db.String(10), db.ForeignKey('productos.id'), primary_key=True),
#     db.Column('modificacion_id', db.Integer, db.ForeignKey('modificaciones.id'), primary_key=True)
# )
