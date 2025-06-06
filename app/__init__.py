from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from werkzeug.security import generate_password_hash # Importar generate_password_hash
import click # Importar click para comandos CLI

from config import config # Importa el diccionario de configuraciones

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = 'strong' # Protección de sesión
login_manager.login_view = 'auth.login' # Blueprint y ruta para la vista de login
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

# migrate = Migrate() # Descomentar si usas Flask-Migrate

def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=False) # instance_relative_config=False si config.py está en raíz

    # Cargar configuración
    app.config.from_object(config[config_name])

    # Inicializar extensiones
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    # migrate.init_app(app, db) # Descomentar si usas Flask-Migrate

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

    # Aquí puedes añadir un contexto para el shell de Flask
    @app.shell_context_processor
    def make_shell_context():
        from .models import db, Usuario # Importar modelos dentro del contexto
        return {'db': db, 'Usuario': Usuario} # Añade tus modelos aquí

    # Registrar comandos CLI
    register_cli_commands(app)

    return app

def register_cli_commands(app):
    """Registra comandos CLI personalizados con la aplicación Flask."""
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("password")
    @click.option("--nombre", default="Administrador", help="Nombre completo del administrador.")
    def create_admin_command(username, password, nombre):
        """Crea un usuario administrador inicial."""
        from .models import db, Usuario, RolUsuario # Importar modelos y Enum aquí

        # Asegurarse de que el rol ADMINISTRADOR existe en el Enum
        if RolUsuario.ADMINISTRADOR.value not in [r.value for r in RolUsuario]:
             click.echo("Error: El rol 'ADMINISTRADOR' no está definido en RolUsuario Enum.", err=True)
             return

        user = Usuario.query.filter_by(username=username).first()
        if user:
            click.echo(f"Error: El usuario '{username}' ya existe.", err=True)
        else:
            admin_user = Usuario(
                username=username,
                nombre_completo=nombre,
                rol=RolUsuario.ADMINISTRADOR, # Usar el miembro del Enum
                activo=True
            )
            admin_user.set_password(password)
            db.session.add(admin_user)
            db.session.commit()
            click.echo(f"Usuario administrador '{username}' creado exitosamente.")

    # Puedes añadir más comandos CLI aquí (ej. seed-db, import-data, etc.)
