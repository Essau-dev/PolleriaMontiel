from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from werkzeug.security import generate_password_hash # Importar generate_password_hash
import click # Importar click para comandos CLI
from datetime import datetime # Importar datetime para context processor
from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

from config import config # Importa el diccionario de configuraciones
# Importar helpers
from .utils.helpers import format_currency, format_datetime, format_date, format_pedido_folio

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.session_protection = 'strong' # Protección de sesión
login_manager.login_view = 'auth.login' # Blueprint y ruta para la vista de login
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"

migrate = Migrate() # Descomentar si usas Flask-Migrate

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # REMOVER: config[config_name].init_app(app) # Esta línea es incorrecta

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db) # Inicializar Flask-Migrate

    # Registrar Blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .clientes import clientes as clientes_blueprint
    app.register_blueprint(clientes_blueprint, url_prefix='/clientes')

    from .productos import productos as productos_blueprint
    app.register_blueprint(productos_blueprint, url_prefix='/productos')

    from .pedidos import pedidos as pedidos_blueprint
    app.register_blueprint(pedidos_blueprint, url_prefix='/pedidos')

    from .caja import caja as caja_blueprint
    app.register_blueprint(caja_blueprint, url_prefix='/caja')

    # Context processor para hacer 'config' y 'now' disponibles en todas las plantillas
    @app.context_processor
    def inject_variables():
        return dict(config=app.config, now=datetime.utcnow())

    # Registrar helpers como filtros de Jinja (ya estaba)
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_pedido_folio'] = format_pedido_folio

    # Registrar helpers como funciones globales de Jinja (NUEVO)
    app.jinja_env.globals['format_currency'] = format_currency
    app.jinja_env.globals['format_datetime'] = format_datetime
    app.jinja_env.globals['format_date'] = format_date
    app.jinja_env.globals['format_pedido_folio'] = format_pedido_folio


    # Registrar comandos CLI personalizados
    def register_cli_commands(app):
        @app.cli.command('create-admin')
        @click.argument('username')
        @click.argument('password')
        @click.argument('nombre_completo')
        def create_admin_command(username, password, nombre_completo):
            """Crea un usuario con rol de Administrador."""
            from app.models import Usuario, RolUsuario # Importar dentro de la función para evitar importación circular
            from app import db # Importar db aquí también

            if Usuario.query.filter_by(username=username).first():
                click.echo(f'Error: El usuario "{username}" ya existe.')
                return

            admin_user = Usuario(
                username=username,
                nombre_completo=nombre_completo,
                rol=RolUsuario.ADMINISTRADOR # Usar el Enum
            )
            admin_user.set_password(password)

            db.session.add(admin_user)
            db.session.commit()
            click.echo(f'Usuario Administrador "{username}" creado exitosamente.')

        @app.cli.command('seed-db')
        def seed_db_command():
            """Inicia el proceso de seeding de la base de datos."""
            from app.seed import seed_initial_data # Importar dentro de la función
            click.echo('Iniciando proceso de seeding de la base de datos...')
            try:
                seed_initial_data()
                click.echo('Seeding completado exitosamente.')
            except Exception as e:
                click.echo(f'Error durante el seeding: {e}', err=True)
                # Opcional: db.session.rollback() si hubo un error a mitad del proceso
                raise e # Re-lanzar la excepción para ver el traceback completo

    register_cli_commands(app)

    return app

# Importar modelos y enums después de crear 'db' para evitar problemas de importación circular
# Esto es una práctica común en Flask-SQLAlchemy con la estructura de blueprints
from . import models
