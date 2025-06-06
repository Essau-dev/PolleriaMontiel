
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
# from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

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
    
    # Aquí puedes añadir un contexto para el shell de Flask
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'Usuario': Usuario} # Añade tus modelos aquí

    return app
