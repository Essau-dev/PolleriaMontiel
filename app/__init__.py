from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from werkzeug.security import generate_password_hash # Importar generate_password_hash
import click # Importar click para comandos CLI
from datetime import datetime # Importar datetime para context processor
from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

from config import config # Importa el diccionario de configuraciones
from .utils.helpers import format_currency, format_datetime, format_date, format_pedido_folio # Importar helpers

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = 'strong' # Protección de sesión
login_manager.login_view = 'auth.login' # Blueprint y ruta para la vista de login
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

migrate = Migrate() # Descomentar si usas Flask-Migrate

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=False) # instance_relative_config=False si config.py está en raíz

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db) # Descomentar si usas Flask-Migrate

    # Registrar Blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .pedidos import pedidos as pedidos_blueprint
    app.register_blueprint(pedidos_blueprint, url_prefix='/pedidos')

    from .caja import caja as caja_blueprint
    app.register_blueprint(caja_blueprint, url_prefix='/caja')

    from .productos import productos as productos_blueprint
    app.register_blueprint(productos_blueprint, url_prefix='/productos')

    from .clientes import clientes as clientes_blueprint
    app.register_blueprint(clientes_blueprint, url_prefix='/clientes')

    # from .utils import utils as utils_blueprint # Eliminar o comentar esta línea
    # app.register_blueprint(utils_blueprint, url_prefix='/utils') # Eliminar o comentar esta línea

    # Registrar context processor para hacer variables globales en plantillas
    @app.context_processor
    def inject_global_variables():
        return dict(
            config=app.config, # Hacer config disponible como 'config'
            now=datetime.utcnow(), # Hacer la fecha/hora actual (UTC) disponible como 'now'
            format_currency=format_currency, # Hacer helper disponible
            format_datetime=format_datetime, # Hacer helper disponible
            format_date=format_date, # Hacer helper disponible
            format_pedido_folio=format_pedido_folio # Hacer helper disponible
            # Añadir otros helpers o variables que se necesiten globalmente
        )


    # Aquí puedes añadir un contexto para el shell de Flask
    @app.shell_context_processor
    def make_shell_context():
        # Importar modelos aquí para que estén disponibles en el shell
        from .models import Usuario, Cliente, Producto, Subproducto, Modificacion, Precio, Pedido, PedidoItem, ProductoAdicional, MovimientoCaja, CorteCaja, ConfiguracionSistema # Importa tus modelos aquí
        return dict(db=db, Usuario=Usuario, Cliente=Cliente, Producto=Producto, Subproducto=Subproducto, Modificacion=Modificacion, Precio=Precio, Pedido=Pedido, PedidoItem=PedidoItem, ProductoAdicional=ProductoAdicional, MovimientoCaja=MovimientoCaja, CorteCaja=CorteCaja, ConfiguracionSistema=ConfiguracionSistema) # Añadir otros modelos según se necesiten

    # Registrar comandos CLI
    register_cli_commands(app)

    return app

def register_cli_commands(app):
    """Registra comandos CLI personalizados con la aplicación Flask."""
    # Ejemplo de comando para crear un usuario administrador inicial
    # Requiere que el modelo Usuario y la función set_password existan
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("password")
    @click.argument("nombre_completo")
    def create_admin_command(username, password, nombre_completo):
        """Crea un usuario administrador."""
        from .models import Usuario, RolUsuario # Importar dentro de la función para evitar importación circular
        admin_role = RolUsuario.ADMINISTRADOR.value # Obtener el valor string del Enum
        user = Usuario.query.filter_by(username=username).first()
        if user:
            click.echo(f"Error: El usuario '{username}' ya existe.")
            return
        user = Usuario(username=username, nombre_completo=nombre_completo, rol=admin_role, activo=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Usuario administrador '{username}' creado exitosamente.")

    # Puedes añadir otros comandos CLI aquí (ej. seed-db)
    @app.cli.command("seed-db")
    def seed_db_command():
        """Puebla la base de datos con datos iniciales (productos, tipos cliente, etc.)."""
        from .seed import seed_initial_data # Asumiendo que tienes un archivo seed.py con esta función
        seed_initial_data()
        click.echo("Base de datos poblada con datos iniciales.")
