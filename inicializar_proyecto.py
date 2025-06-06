import os
import stat

# Nombre del directorio raíz del proyecto
NOMBRE_PROYECTO = "PolleriaMontiel"

# Estructura de directorios y archivos
# (directorio, [lista_de_subdirectorios], [lista_de_archivos_a_crear])
ESTRUCTURA_PROYECTO = {
    NOMBRE_PROYECTO: {
        "dirs": [
            "app",
            "migrations" # Para Flask-Migrate en el futuro
        ],
        "files": [
            "run.py",
            "config.py",
            "requirements.txt",
            ".gitignore",
            "README.md"
        ],
        "app": {
            "dirs": [
                "static",
                "templates",
                "auth",
                "pedidos",
                "caja",
                "productos",
                "clientes",
                "utils",
                "main" # Un blueprint general para rutas como index
            ],
            "files": [
                "__init__.py", # Para convertir app en un paquete (donde se crea la app Flask)
                "models.py",
                "forms.py" # Formularios globales, si aplican
            ],
            "static": {
                "dirs": ["css", "js", "img"],
                "files": [],
                "css": {"dirs": [], "files": ["estilo.css"]},
                "js": {"dirs": ["modulos_js"], "files": ["main.js"]},
                "img": {"dirs": [], "files": []} # Vacío por ahora
            },
            "templates": {
                "dirs": [
                    "auth",
                    "layouts",
                    "pedidos",
                    "caja",
                    "productos",
                    "clientes",
                    "shared",
                    "main" # Para plantillas del blueprint main
                ],
                "files": [], # No hay archivos directamente en templates/
                "layouts": {"dirs": [], "files": ["base.html", "_nav.html", "_footer.html"]},
                "shared": {"dirs": [], "files": ["_form_field.html"]},
                "main": {"dirs": [], "files": ["index.html"]}, # Plantilla de ejemplo
                "auth": {"dirs": [], "files": ["login.html", "registro_usuario.html"]},
            },
            "auth": {"dirs": [], "files": ["__init__.py", "routes.py", "forms.py"]}, # models.py opcional aquí si centralizado
            "pedidos": {"dirs": [], "files": ["__init__.py", "routes.py", "forms.py"]},
            "caja": {"dirs": [], "files": ["__init__.py", "routes.py", "forms.py"]},
            "productos": {"dirs": [], "files": ["__init__.py", "routes.py", "forms.py"]},
            "clientes": {"dirs": [], "files": ["__init__.py", "routes.py", "forms.py"]},
            "utils": {"dirs": [], "files": ["__init__.py", "helpers.py", "decorators.py"]},
            "main": {"dirs": [], "files": ["__init__.py", "routes.py"]},
        }
    }
}

# --- Contenido para los archivos ---

CONTENIDO_RUN_PY = """
from app import create_app, db
from app.models import Usuario # Importa tus modelos aquí a medida que los crees
# from flask_migrate import Migrate # Descomentar si usas Flask-Migrate

app = create_app()
# migrate = Migrate(app, db) # Descomentar si usas Flask-Migrate

# Ejemplo de cómo podrías añadir un usuario admin inicial (más adelante esto iría en un comando CLI o seed)
# @app.cli.command("create_admin")
# def create_admin_user():
#     \"\"\"Crea un usuario administrador inicial.\"\"\"
#     from werkzeug.security import generate_password_hash
#     if not Usuario.query.filter_by(username="admin").first():
#         admin_user = Usuario(
#             username="admin",
#             password_hash=generate_password_hash("adminpass"), # Cambiar en producción
#             nombre_completo="Administrador del Sistema",
#             rol="ADMINISTRADOR",
#             activo=True
#         )
#         db.session.add(admin_user)
#         db.session.commit()
#         print("Usuario administrador 'admin' creado.")
#     else:
#         print("Usuario administrador 'admin' ya existe.")


if __name__ == '__main__':
    app.run(debug=True) # debug=True solo para desarrollo
"""

CONTENIDO_CONFIG_PY = """
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # Busca el .env en el directorio raíz del proyecto

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una_clave_secreta_muy_dificil_de_adivinar' # CAMBIAR EN PRODUCCIÓN
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db') # Ruta a la BD dentro del dir 'PolleriaMontiel'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuraciones adicionales de la aplicación (ejemplos)
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['tu_email@example.com']

    # Polleria Montiel - Configuraciones específicas (se podrían mover a la BD más adelante)
    NOMBRE_NEGOCIO = "Pollería Montiel"
    LIMITE_ITEMS_PA_SIN_COMISION = 3
    MONTO_COMISION_FIJA_PA_EXTRA = 4.0
    # ... más configuraciones como plantillas de mensajes, etc.

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False # True para ver las consultas SQL generadas

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # BD en memoria para tests
    WTF_CSRF_ENABLED = False # Deshabilitar CSRF para tests de formularios

class ProductionConfig(Config):
    DEBUG = False
    # Asegúrate de configurar DATABASE_URL y SECRET_KEY en el entorno de producción
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # Ej: PostgreSQL
    # Considerar otras configuraciones de seguridad y rendimiento para producción

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
"""

CONTENIDO_APP_INIT_PY = """
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
"""

CONTENIDO_MODELS_PY = """
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
"""

CONTENIDO_REQUIREMENTS_TXT = """
Flask>=2.0.0 # O la versión que prefieras, ej. 3.0.0
SQLAlchemy>=1.4.0 # O la versión que prefieras, ej. 2.0
Flask-SQLAlchemy>=2.5.0
Flask-WTF>=1.0.0
Flask-Login>=0.5.0
python-dotenv>=0.19.0
Werkzeug>=2.0.0 # Para hashing, aunque Flask lo incluye

# Para desarrollo (opcional pero recomendado):
# flake8
# black
# Flask-Migrate # Si decides usarlo para migraciones de BD
"""

CONTENIDO_GITIGNORE = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
# db.sqlite3 # Comentado para que se incluya en el MVP si es necesario
# db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache
app.db # Nombre de nuestra BD SQLite
*.sqlite3 # Cualquier otra BD sqlite

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# PEP 582; __pypackages__
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype
.pytype/
"""

CONTENIDO_ESTILO_CSS = """
/* app/static/css/estilo.css */

/*
  Pollería Montiel - Estilos Principales
  Metodología: BEM-like y clases de utilidad.
  Enfoque: Mobile First.
*/

/* 1. Variables CSS Globales */
:root {
    /* Colores Principales */
    --rojo-principal: #D32F2F; /* Un rojo oscuro y apetitoso */
    --rojo-secundario: #FFCDD2; /* Un rojo más claro para acentos */
    --amarillo-principal: #FFA000; /* Amarillo/Naranja para llamadas a la acción o destacados */
    --amarillo-secundario: #FFECB3;

    /* Colores Neutros */
    --gris-oscuro: #212121;   /* Para texto principal */
    --gris-medio: #757575;    /* Para texto secundario, bordes sutiles */
    --gris-claro: #BDBDBD;    /* Para bordes, divisores */
    --gris-muy-claro: #f5f5f5; /* Para fondos de sección, inputs (ligeramente más cálido que EEEEEE) */
    --blanco: #FFFFFF;
    --negro: #000000;

    /* Colores Semánticos (Alertas, Estados) */
    --verde-exito: #388E3C;
    --verde-exito-fondo: #C8E6C9;
    --azul-info: #1976D2;
    --azul-info-fondo: #BBDEFB;
    --amarillo-advertencia: #FBC02D; /* Un amarillo más brillante para advertencia */
    --amarillo-advertencia-texto: #5d4a0b; /* Texto oscuro para contraste en fondo amarillo */
    --amarillo-advertencia-fondo: #FFF9C4;
    --rojo-error: #D32F2F;
    --rojo-error-fondo: #FFCDD2;

    /* Tipografía */
    --fuente-principal: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    --fuente-base-size: 16px;
    --line-height-base: 1.6;

    /* Espaciado (sistema de espaciado 8pt) */
    --espacio-xxs: 0.25rem; /* 4px */
    --espacio-xs: 0.5rem;  /* 8px */
    --espacio-s: 0.75rem;  /* 12px */
    --espacio-m: 1rem;     /* 16px */
    --espacio-l: 1.5rem;   /* 24px */
    --espacio-xl: 2rem;    /* 32px */
    --espacio-xxl: 3rem;   /* 48px */

    /* Bordes */
    --border-radius-sm: 0.25rem; /* 4px */
    --border-radius-md: 0.5rem;  /* 8px */
    --border-width: 1px;
    --border-color: var(--gris-claro);

    /* Sombras */
    --sombra-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --sombra-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --sombra-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);

    /* Breakpoints (Mobile First) */
    --breakpoint-sm: 576px;
    --breakpoint-md: 768px;
    --breakpoint-lg: 992px;
    --breakpoint-xl: 1200px;

    /* Z-indexes */
    --z-index-dropdown: 1000;
    --z-index-sticky: 1020;
    --z-index-fixed: 1030;
    --z-index-modal-backdrop: 1040;
    --z-index-modal: 1050;
    --z-index-popover: 1060;
    --z-index-tooltip: 1070;
}

/* 2. Reseteo Básico y Estilos Globales */
*,
*::before,
*::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: var(--fuente-base-size);
    line-height: var(--line-height-base);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    scroll-behavior: smooth;
}

body {
    font-family: var(--fuente-principal);
    color: var(--gris-oscuro);
    background-color: var(--blanco);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

main {
    flex-grow: 1;
    padding-top: var(--espacio-l); /* Espacio para el header fijo si se usa */
    padding-bottom: var(--espacio-l);
}

a {
    color: var(--rojo-principal);
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
    color: #A72525;
}

img, video, svg {
    max-width: 100%;
    height: auto;
    display: block;
}

/* 3. Clases de Utilidad Básicas */
.container {
    width: 100%;
    padding-right: var(--espacio-m);
    padding-left: var(--espacio-m);
    margin-right: auto;
    margin-left: auto;
}
@media (min-width: var(--breakpoint-sm)) { .container { max-width: 540px; } }
@media (min-width: var(--breakpoint-md)) { .container { max-width: 720px; } }
@media (min-width: var(--breakpoint-lg)) { .container { max-width: 960px; } }
@media (min-width: var(--breakpoint-xl)) { .container { max-width: 1140px; } }

.text-center { text-align: center !important; }
.text-right { text-align: right !important; }
.text-left { text-align: left !important; }

.d-none { display: none !important; }
.d-block { display: block !important; }
.d-flex { display: flex !important; }
.d-inline-block { display: inline-block !important; }
.flex-column { flex-direction: column !important; }
.justify-content-center { justify-content: center !important; }
.justify-content-between { justify-content: space-between !important; }
.align-items-center { align-items: center !important; }
.align-items-start { align-items: flex-start !important; }
.flex-grow-1 { flex-grow: 1 !important; }

.w-100 { width: 100% !important; }
.h-100 { height: 100% !important; }

/* Clases de espaciado (ejemplo) */
.mt-0 { margin-top: 0 !important; } .mt-xxs { margin-top: var(--espacio-xxs) !important; } .mt-xs { margin-top: var(--espacio-xs) !important; } .mt-s { margin-top: var(--espacio-s) !important; } .mt-m { margin-top: var(--espacio-m) !important; } .mt-l { margin-top: var(--espacio-l) !important; } .mt-xl { margin-top: var(--espacio-xl) !important; } .mt-xxl { margin-top: var(--espacio-xxl) !important; }
.mb-0 { margin-bottom: 0 !important; } .mb-xxs { margin-bottom: var(--espacio-xxs) !important; } .mb-xs { margin-bottom: var(--espacio-xs) !important; } .mb-s { margin-bottom: var(--espacio-s) !important; } .mb-m { margin-bottom: var(--espacio-m) !important; } .mb-l { margin-bottom: var(--espacio-l) !important; } .mb-xl { margin-bottom: var(--espacio-xl) !important; } .mb-xxl { margin-bottom: var(--espacio-xxl) !important; }
.ml-auto { margin-left: auto !important; }
.mr-auto { margin-right: auto !important; }
/* Añadir más para p (padding), pl, pr, pt, pb, mx, my, px, py */

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.required-indicator::after {
    content: '*';
    color: var(--rojo-principal);
    margin-left: var(--espacio-xxs);
}

/* 4. Estilos para Componentes (Ejemplos iniciales) */

/* Botones */
.btn {
    display: inline-block;
    font-weight: 500; /* Ligeramente más bold */
    line-height: var(--line-height-base);
    color: var(--gris-oscuro);
    text-align: center;
    vertical-align: middle;
    cursor: pointer;
    user-select: none;
    background-color: transparent;
    border: var(--border-width) solid transparent;
    padding: var(--espacio-xs) var(--espacio-m); /* Más padding horizontal */
    font-size: 0.95rem;
    border-radius: var(--border-radius-sm);
    transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}
.btn:hover {
    text-decoration: none;
}
.btn:focus, .btn.focus {
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(211, 47, 47, 0.25); /* Sombra de foco roja */
}
.btn:disabled, .btn.disabled {
    opacity: 0.65;
    cursor: not-allowed;
}

.btn--primary {
    color: var(--blanco);
    background-color: var(--rojo-principal);
    border-color: var(--rojo-principal);
}
.btn--primary:hover {
    color: var(--blanco);
    background-color: #A72525;
    border-color: #9E2020;
}
.btn--primary:focus, .btn--primary.focus {
    box-shadow: 0 0 0 0.2rem rgba(211, 47, 47, 0.5);
}

.btn--secondary {
    color: var(--rojo-principal);
    background-color: var(--blanco);
    border-color: var(--rojo-principal);
}
.btn--secondary:hover {
    color: var(--blanco);
    background-color: var(--rojo-principal);
    border-color: var(--rojo-principal);
}

.btn--success { color: var(--blanco); background-color: var(--verde-exito); border-color: var(--verde-exito); }
.btn--success:hover { background-color: #2E7D32; border-color: #2E7D32; }
.btn--info { color: var(--blanco); background-color: var(--azul-info); border-color: var(--azul-info); }
.btn--info:hover { background-color: #1565C0; border-color: #1565C0; }
.btn--warning { color: var(--amarillo-advertencia-texto); background-color: var(--amarillo-advertencia); border-color: var(--amarillo-advertencia); }
.btn--warning:hover { background-color: #F9A825; border-color: #F9A825; }
.btn--danger { color: var(--blanco); background-color: var(--rojo-error); border-color: var(--rojo-error); }
.btn--danger:hover { background-color: #A72525; border-color: #A72525; }

.btn--sm { padding: var(--espacio-xxs) var(--espacio-s); font-size: 0.8rem; }
.btn--lg { padding: var(--espacio-s) var(--espacio-l); font-size: 1.1rem; }

.btn-block { display: block; width: 100%; }

/* Formularios */
.form-group {
    margin-bottom: var(--espacio-m);
}

.form-label {
    display: inline-block;
    margin-bottom: var(--espacio-xs);
    font-weight: 500;
}

.form-control {
    display: block;
    width: 100%;
    padding: var(--espacio-xs) var(--espacio-s);
    font-size: 1rem;
    font-weight: 400;
    line-height: var(--line-height-base);
    color: var(--gris-oscuro);
    background-color: var(--blanco);
    background-clip: padding-box;
    border: var(--border-width) solid var(--border-color);
    border-radius: var(--border-radius-sm);
    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}
.form-control:focus {
    border-color: var(--rojo-principal);
    outline: 0;
    box-shadow: 0 0 0 0.2rem rgba(211, 47, 47, 0.25);
}
.form-control::placeholder {
    color: var(--gris-medio);
    opacity: 1;
}
.form-control:disabled, .form-control[readonly] {
    background-color: var(--gris-muy-claro);
    opacity: 1;
}
/* Para validación */
.form-control.is-invalid { border-color: var(--rojo-error); }
.form-control.is-valid { border-color: var(--verde-exito); }
.invalid-feedback { display: none; width: 100%; margin-top: .25rem; font-size: .875em; color: var(--rojo-error); }
.valid-feedback { display: none; width: 100%; margin-top: .25rem; font-size: .875em; color: var(--verde-exito); }
.is-invalid ~ .invalid-feedback, .is-invalid ~ .invalid-tooltip { display: block; }
.is-valid ~ .valid-feedback, .is-valid ~ .valid-tooltip { display: block; }


/* Alertas (Mensajes Flash) */
.alert {
    position: relative;
    padding: var(--espacio-m); /* Más padding */
    margin-bottom: var(--espacio-m);
    border: var(--border-width) solid transparent;
    border-radius: var(--border-radius-sm);
    box-shadow: var(--sombra-sm);
}
.alert-heading {
    color: inherit;
    font-weight: 500;
    margin-bottom: var(--espacio-xs);
}
.alert--success {
    color: #145214; /* Texto más oscuro para mejor contraste */
    background-color: var(--verde-exito-fondo);
    border-color: var(--verde-exito);
}
.alert--error {
    color: #7f1d1d;
    background-color: var(--rojo-error-fondo);
    border-color: var(--rojo-error);
}
.alert--info {
    color: #0c5460;
    background-color: var(--azul-info-fondo);
    border-color: var(--azul-info);
}
.alert--warning {
    color: var(--amarillo-advertencia-texto);
    background-color: var(--amarillo-advertencia-fondo);
    border-color: var(--amarillo-advertencia);
}

/* Layouts */
.site-header {
    background-color: var(--rojo-principal);
    color: var(--blanco);
    padding: var(--espacio-s) 0; /* Un poco menos de padding */
    /* box-shadow: var(--sombra-md); */
    /* position: sticky; top: 0; z-index: var(--z-index-sticky); */ /* Header fijo si se desea */
}
.site-header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.site-header__logo {
    font-size: 1.75rem; /* Un poco más grande */
    font-weight: 700; /* Más bold */
    color: var(--blanco);
    text-decoration: none;
}
.site-header__logo:hover {
    color: var(--amarillo-principal);
}
.site-header__nav ul {
    list-style: none;
    display: flex;
    gap: var(--espacio-m);
    margin: 0; /* Resetear margen de ul */
}
.site-header__nav a {
    color: var(--blanco);
    font-weight: 500;
    padding: var(--espacio-xs) 0;
    border-bottom: 2px solid transparent;
    transition: color 0.2s ease, border-bottom-color 0.2s ease;
}
.site-header__nav a:hover,
.site-header__nav a.active { /* Clase 'active' para la página actual */
    color: var(--amarillo-principal);
    text-decoration: none;
    /* border-bottom-color: var(--amarillo-principal); */
}

.site-footer {
    background-color: var(--gris-muy-claro);
    color: var(--gris-medio);
    padding: var(--espacio-l) 0;
    margin-top: auto; /* Empuja el footer hacia abajo */
    text-align: center;
    font-size: 0.9rem;
    border-top: var(--border-width) solid var(--border-color);
}

/* Tablas (Básico) */
.table {
    width: 100%;
    margin-bottom: var(--espacio-m);
    color: var(--gris-oscuro);
    border-collapse: collapse;
}
.table th,
.table td {
    padding: var(--espacio-s);
    vertical-align: top;
    border-top: var(--border-width) solid var(--border-color);
}
.table thead th {
    vertical-align: bottom;
    border-bottom: 2px solid var(--border-color);
    text-align: left;
    font-weight: 600;
}
.table tbody + tbody {
    border-top: 2px solid var(--border-color);
}
.table-striped tbody tr:nth-of-type(odd) {
    background-color: rgba(0,0,0,.03);
}
.table-hover tbody tr:hover {
    background-color: rgba(0,0,0,.05);
}

/* Cards */
.card {
    position: relative;
    display: flex;
    flex-direction: column;
    min-width: 0;
    word-wrap: break-word;
    background-color: var(--blanco);
    background-clip: border-box;
    border: var(--border-width) solid var(--border-color);
    border-radius: var(--border-radius-md);
    margin-bottom: var(--espacio-m);
    box-shadow: var(--sombra-sm);
}
.card__header {
    padding: var(--espacio-s) var(--espacio-m);
    margin-bottom: 0;
    background-color: rgba(0,0,0,.03);
    border-bottom: var(--border-width) solid var(--border-color);
    font-size: 1.1rem;
    font-weight: 500;
}
.card__header:first-child {
    border-radius: calc(var(--border-radius-md) - var(--border-width)) calc(var(--border-radius-md) - var(--border-width)) 0 0;
}
.card__body {
    flex: 1 1 auto;
    padding: var(--espacio-m);
}
.card__footer {
    padding: var(--espacio-s) var(--espacio-m);
    background-color: rgba(0,0,0,.03);
    border-top: var(--border-width) solid var(--border-color);
}
.card__footer:last-child {
    border-radius: 0 0 calc(var(--border-radius-md) - var(--border-width)) calc(var(--border-radius-md) - var(--border-width));
}
.card__title {
    margin-bottom: var(--espacio-s);
    font-size: 1.25rem;
    font-weight: 600;
}
.card__subtitle {
    margin-top: calc(-1 * var(--espacio-s) / 2);
    margin-bottom: 0;
    font-weight: 400;
    color: var(--gris-medio);
}

/* Utilidades específicas de la aplicación */
.precio {
    font-weight: bold;
    color: var(--rojo-principal);
}

/* Estados de pedido (ejemplo) */
.estado-pedido {
    padding: var(--espacio-xxs) var(--espacio-xs);
    border-radius: var(--border-radius-sm);
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
    color: var(--blanco);
    display: inline-block;
}
.estado-pedido--pendiente { background-color: var(--amarillo-principal); color: var(--amarillo-advertencia-texto);}
.estado-pedido--en-preparacion { background-color: var(--azul-info); }
.estado-pedido--listo { background-color: #FF8F00; } /* Naranja */
.estado-pedido--en-ruta { background-color: #5E35B1; } /* Morado */
.estado-pedido--entregado { background-color: var(--verde-exito); }
.estado-pedido--cancelado { background-color: var(--rojo-error); }


/* Estilos para mobile (si se necesitan overrides específicos, aunque la idea es que Mobile First ya lo cubra) */
@media (max-width: calc(var(--breakpoint-md) - 1px)) {
    .site-header__nav {
        /* Aquí podrías implementar un menú hamburguesa */
        /* display: none; */ /* Ejemplo simplista */
    }
    .site-header .container {
        /* flex-direction: column; */ /* Si el logo y nav se apilan */
        /* align-items: flex-start; */
    }
}

"""

CONTENIDO_MAIN_JS = """
// app/static/js/main.js
console.log("Pollería Montiel JS Cargado!");

// Lógica de UI global puede ir aquí
// Ejemplo: Manejo de menú hamburguesa en móvil, etc.

document.addEventListener('DOMContentLoaded', function () {
    // Ejemplo: Cerrar mensajes flash después de un tiempo
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        // Si no es un error persistente, quitarlo después de 5 segundos
        if (!alert.classList.contains('alert--error')) {
            setTimeout(function() {
                // alert.style.display = 'none'; // O una animación de fade-out
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 7000); // 7 segundos
        }
        // Añadir un botón de cierre manual si no existe
        if (!alert.querySelector('.close-alert')) {
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '×'; // Símbolo de 'x'
            closeButton.className = 'close-alert'; // Para estilizarlo
            closeButton.style.cssText = `
                position: absolute;
                top: 5px;
                right: 10px;
                background: transparent;
                border: none;
                font-size: 1.5rem;
                font-weight: bold;
                color: inherit;
                opacity: 0.7;
                cursor: pointer;
            `;
            closeButton.onmouseover = () => closeButton.style.opacity = '1';
            closeButton.onmouseout = () => closeButton.style.opacity = '0.7';
            closeButton.onclick = function() {
                // alert.style.display = 'none';
                 if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            };
            alert.appendChild(closeButton);
        }
    });

    // Más listeners de eventos o inicializaciones aquí
});

// Funciones helper de JS (ejemplos)
function mostrarSpinner(elementoPadre) {
    // Lógica para mostrar un indicador de carga
    const spinner = document.createElement('div');
    spinner.className = 'spinner'; // Estilizar .spinner en CSS
    spinner.textContent = 'Cargando...';
    if (elementoPadre) {
        elementoPadre.appendChild(spinner);
    }
    return spinner;
}

function ocultarSpinner(spinnerElement) {
    if (spinnerElement && spinnerElement.parentNode) {
        spinnerElement.parentNode.removeChild(spinnerElement);
    }
}

// Para peticiones Fetch (AJAX)
async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'), // Si usas CSRF token en meta
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: response.statusText }));
            throw new Error(errorData.message || `Error HTTP: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error en fetchData:', error);
        // Mostrar un mensaje de error al usuario, ej. con un mensaje flash dinámico
        mostrarMensajeFlash(`Error: ${error.message}`, 'error');
        throw error;
    }
}

function mostrarMensajeFlash(mensaje, categoria = 'info', contenedorId = 'flash-container') {
    // Esta función necesitaría un div con id="flash-container" en base.html
    // o podrías crear dinámicamente el contenedor de alertas.
    // Por simplicidad, aquí solo logueamos y asumimos que los mensajes flash del backend son suficientes por ahora.
    console.log(`FLASH [${categoria}]: ${mensaje}`);
    const flashContainer = document.getElementById(contenedorId) || document.querySelector('main.container');
    if(flashContainer){
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert--${categoria}`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.textContent = mensaje;
        // Añadir botón de cierre
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.className = 'close-alert';
        closeButton.style.cssText = `position: absolute; top: 5px; right: 10px; background: transparent; border: none; font-size: 1.5rem; cursor: pointer;`;
        closeButton.onclick = () => alertDiv.remove();
        alertDiv.appendChild(closeButton);

        flashContainer.insertBefore(alertDiv, flashContainer.firstChild);
        setTimeout(() => alertDiv.remove(), 7000);
    }
}
"""

CONTENIDO_BASE_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Sistema de Gestión para Pollería Montiel">
    <!-- CSRF Token (si lo usas con JS para AJAX POST/PUT/DELETE) -->
    <!-- <meta name="csrf-token" content="{{ csrf_token() }}"> -->
    <title>{% block title %}SGPM - Pollería Montiel{% endblock %}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/estilo.css') }}">
    {% block head_css %}{% endblock %}
</head>
<body>
    {% include 'layouts/_nav.html' %}

    <main class="container">
        {# Contenedor para mensajes flash generados por JS si es necesario #}
        <div id="js-flash-container"></div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert--{{ category if category in ['success', 'error', 'info', 'warning'] else 'info' }}" role="alert">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}
        <!-- El contenido específico de cada página irá aquí -->
        <h1 class="card__title">Bienvenido al Sistema de Gestión de Pollería Montiel</h1>
        <p>Esta es la página base. El contenido se cargará aquí.</p>
        {% endblock %}
    </main>

    {% include 'layouts/_footer.html' %}

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block body_scripts %}{% endblock %}
</body>
</html>
"""

CONTENIDO_NAV_HTML = """
<header class="site-header">
    <div class="container">
        <a href="{{ url_for('main.index') }}" class="site-header__logo">🐔 Pollería Montiel</a>
        <nav class="site-header__nav">
            <ul>
                {% if current_user and current_user.is_authenticated %}
                    <li><a href="{{ url_for('main.index') }}">Inicio</a></li>
                    <li><a href="{{ url_for('pedidos.listar_pedidos') if 'pedidos.listar_pedidos' in config['ROUTES'] else '#' }}">Pedidos</a></li>
                    <li><a href="{{ url_for('caja.dashboard_caja') if 'caja.dashboard_caja' in config['ROUTES'] else '#' }}">Caja</a></li>
                    
                    {% if current_user.has_role('ADMINISTRADOR') %}
                        <li class="dropdown">
                            <a href="#" class="dropdown-toggle">Admin ▾</a>
                            <ul class="dropdown-menu">
                                <li><a href="{{ url_for('clientes.listar_clientes') if 'clientes.listar_clientes' in config['ROUTES'] else '#' }}">Clientes</a></li>
                                <li><a href="{{ url_for('productos.listar_productos') if 'productos.listar_productos' in config['ROUTES'] else '#' }}">Productos</a></li>
                                <li><a href="{{ url_for('auth.listar_usuarios') if 'auth.listar_usuarios' in config['ROUTES'] else '#' }}">Usuarios</a></li>
                                <!-- <li><a href="#">Configuración</a></li> -->
                            </ul>
                        </li>
                    {% endif %}
                    <li><a href="{{ url_for('auth.logout') }}">Cerrar Sesión ({{ current_user.username }})</a></li>
                {% else %}
                    <li><a href="{{ url_for('auth.login') }}">Iniciar Sesión</a></li>
                    <!-- <li><a href="{{ url_for('auth.registro_usuario') }}">Registrar (Admin)</a></li> -->
                {% endif %}
            </ul>
        </nav>
        <!-- Podrías añadir un botón de menú hamburguesa para móviles aquí -->
    </div>
</header>
<style>
/* Estilos básicos para dropdown en nav (mejorar según sea necesario) */
.site-header__nav .dropdown {
    position: relative;
}
.site-header__nav .dropdown-toggle::after {
    /* content: ' ▼'; */ /* Se añade directamente en el HTML para más control */
    display: inline-block;
    margin-left: .255em;
    vertical-align: .255em;
}
.site-header__nav .dropdown-menu {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    z-index: var(--z-index-dropdown);
    min-width: 10rem;
    padding: .5rem 0;
    margin: .125rem 0 0;
    font-size: 1rem;
    color: var(--gris-oscuro);
    text-align: left;
    list-style: none;
    background-color: var(--blanco);
    background-clip: padding-box;
    border: 1px solid rgba(0,0,0,.15);
    border-radius: var(--border-radius-md);
    box-shadow: var(--sombra-md);
}
.site-header__nav .dropdown-menu a {
    display: block;
    width: 100%;
    padding: .5rem 1rem;
    clear: both;
    font-weight: 400;
    color: var(--gris-oscuro);
    text-align: inherit;
    white-space: nowrap;
    background-color: transparent;
    border: 0;
}
.site-header__nav .dropdown-menu a:hover {
    color: var(--rojo-principal);
    background-color: var(--gris-muy-claro);
    text-decoration: none;
}
.site-header__nav .dropdown:hover .dropdown-menu {
    display: block;
}
</style>
<script>
// Pequeño script para el dropdown si se prefiere control JS en lugar de :hover
// document.addEventListener('DOMContentLoaded', function() {
//     const dropdowns = document.querySelectorAll('.site-header__nav .dropdown');
//     dropdowns.forEach(function(dropdown) {
//         const toggle = dropdown.querySelector('.dropdown-toggle');
//         const menu = dropdown.querySelector('.dropdown-menu');
//         if (toggle && menu) {
//             toggle.addEventListener('click', function(event) {
//                 event.preventDefault();
//                 menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
//             });
//             // Opcional: cerrar si se hace clic fuera
//             document.addEventListener('click', function(event) {
//                 if (!dropdown.contains(event.target)) {
//                     menu.style.display = 'none';
//                 }
//             });
//         }
//     });
// });
</script>
"""

CONTENIDO_FOOTER_HTML = """
<footer class="site-footer">
    <div class="container">
        <p>© {{ "now"|datetimeformat('%Y', timezone='America/Mexico_City') if "now"|datetimeformat else '2024' }} {{ config.NOMBRE_NEGOCIO }}. Todos los derechos reservados.</p>
        <p>Sistema de Gestión SGPM v0.1 (MVP)</p>
    </div>
</footer>
"""
# Para que datetimeformat funcione, necesitarás registrarlo como filtro global o usar una extensión.
# Alternativa simple:
# <p>© {{ now.year if now else '2024' }} ... </p>
# Y pasar 'now': datetime.utcnow() al contexto de la plantilla. O simplemente hardcodear el año.

CONTENIDO_FORM_FIELD_HTML = """
{# app/templates/shared/_form_field.html #}
{# Macro para renderizar un campo de formulario con etiqueta y errores #}
{% macro render_field(field, label_visible=True, **kwargs) %}
    <div class="form-group {% if field.errors %}has-error{% endif %}">
        {% if label_visible and field.label %}
            {{ field.label(class="form-label") }}
            {% if field.flags.required %}<span class="required-indicator"></span>{% endif %}
        {% endif %}
        
        {{ field(class="form-control" + (" is-invalid" if field.errors else ""), **kwargs) }}
        
        {% if field.errors %}
            <div class="invalid-feedback">
                {% for error in field.errors %}
                    <span>{{ error }}</span><br>
                {% endfor %}
            </div>
        {% endif %}
        
        {% if field.description %}
            <small class="form-text text-muted">{{ field.description }}</small>
        {% endif %}
    </div>
{% endmacro %}
"""

CONTENIDO_MAIN_INDEX_HTML = """
{% extends "layouts/base.html" %}
{% from "shared/_form_field.html" import render_field %} {# Ejemplo de cómo importar macros #}

{% block title %}Inicio - SGPM{% endblock %}

{% block content %}
<div class="card">
    <div class="card__header">
        <h1 class="card__title mb-0">Dashboard Principal</h1>
    </div>
    <div class="card__body">
        <p>Bienvenido al Sistema de Gestión de {{ config.NOMBRE_NEGOCIO }}, {{ current_user.nombre_completo if current_user and current_user.is_authenticated else "Invitado" }}!</p>
        
        {% if current_user and current_user.is_authenticated %}
            <p>Tu rol es: <strong>{{ current_user.rol }}</strong>.</p>
            <p>Desde aquí podrás acceder a las principales funcionalidades del sistema.</p>
            
            <div class="d-flex" style="gap: 1rem; margin-top: 1.5rem;">
                <a href="{{ url_for('pedidos.crear_pedido') if 'pedidos.crear_pedido' in config['ROUTES'] else '#' }}" class="btn btn--primary btn--lg">Nuevo Pedido</a>
                <a href="{{ url_for('caja.registrar_movimiento') if 'caja.registrar_movimiento' in config['ROUTES'] else '#' }}" class="btn btn--secondary btn--lg">Movimiento de Caja</a>
            </div>
        {% else %}
            <p>Por favor, <a href="{{ url_for('auth.login') }}">inicia sesión</a> para continuar.</p>
        {% endif %}
    </div>
</div>

{# Aquí podrían ir widgets o resúmenes del dashboard #}

{% endblock %}
"""

CONTENIDO_LOGIN_HTML = """
{% extends "layouts/base.html" %}
{% from "shared/_form_field.html" import render_field %}

{% block title %}Iniciar Sesión - SGPM{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card__header">
                <h2 class="card__title mb-0">Iniciar Sesión</h2>
            </div>
            <div class="card__body">
                <form method="POST" action="{{ url_for('auth.login') }}">
                    {{ form.hidden_tag() }} {# CSRF token #}
                    
                    {{ render_field(form.username, placeholder="Tu nombre de usuario") }}
                    {{ render_field(form.password, placeholder="Tu contraseña") }}
                    
                    <div class="form-group form-check mb-m">
                        {{ form.remember_me(class="form-check-input") }}
                        {{ form.remember_me.label(class="form-check-label") }}
                    </div>
                    
                    <button type="submit" class="btn btn--primary btn-block">Ingresar</button>
                </form>
            </div>
            <div class="card__footer text-center">
                <small class="text-muted">
                    <!-- ¿No tienes cuenta? <a href="{{ url_for('auth.registro_usuario') }}">Regístrate aquí (Admin)</a><br> -->
                    <!-- ¿Olvidaste tu contraseña? <a href="#">Recupérala</a> -->
                </small>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

CONTENIDO_REGISTRO_USUARIO_HTML = """
{% extends "layouts/base.html" %}
{% from "shared/_form_field.html" import render_field %}

{% block title %}Registrar Usuario - SGPM{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card__header">
                <h2 class="card__title mb-0">Registrar Nuevo Usuario</h2>
            </div>
            <div class="card__body">
                <form method="POST" action="{{ url_for('auth.registro_usuario') }}">
                    {{ form.hidden_tag() }} {# CSRF token #}
                    
                    {{ render_field(form.nombre_completo, placeholder="Nombre y apellidos del empleado") }}
                    {{ render_field(form.username, placeholder="Nombre de usuario para el sistema (corto, sin espacios)") }}
                    {{ render_field(form.password, placeholder="Contraseña (mínimo 8 caracteres)") }}
                    {{ render_field(form.password2, placeholder="Confirma la contraseña") }}
                    {{ render_field(form.rol) }}
                    
                    <div class="form-group form-check mb-m">
                        {{ form.activo(class="form-check-input") }}
                        {{ form.activo.label(class="form-check-label") }}
                    </div>
                    
                    <button type="submit" class="btn btn--primary btn-block">Registrar Usuario</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
"""

# --- Contenido para los __init__.py y routes.py de los blueprints ---
# (Inicialmente muy básicos)

CONTENIDO_BLUEPRINT_INIT = """
from flask import Blueprint

# El nombre 'auth' aquí debe coincidir con el nombre del directorio
# y con el usado en app/app.py al registrarlo.
# El segundo argumento es __name__, ayuda a Flask a localizar plantillas/estáticos.
# El tercer argumento, template_folder, es opcional si las plantillas están en app/templates/nombre_blueprint/
{blueprint_name} = Blueprint('{blueprint_name}', __name__, template_folder='templates') 

from . import routes # Importa las rutas del blueprint
"""

CONTENIDO_MAIN_ROUTES_PY = """
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main #. es el directorio actual (main)

@main.route('/')
@main.route('/index')
# @login_required # Descomentar para proteger la página principal
def index():
    # if not current_user.is_authenticated:
    #     return redirect(url_for('auth.login'))
    return render_template('main/index.html', title='Inicio')
"""

CONTENIDO_AUTH_ROUTES_PY = """
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import db
from app.models import Usuario
from . import auth # . es el directorio actual (auth)
from .forms import LoginForm, RegistrationForm # Asumiendo que creas estas formas

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data) or not user.activo:
            flash('Nombre de usuario o contraseña inválidos, o usuario inactivo.', 'error')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        flash(f'Bienvenido de nuevo, {user.nombre_completo}!', 'success')
        
        # Redirigir a la página solicitada originalmente o al index
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/registro', methods=['GET', 'POST'])
@login_required # Solo un admin puede registrar otros usuarios inicialmente
def registro_usuario():
    if not current_user.has_role('ADMINISTRADOR'):
        flash('No tienes permiso para registrar usuarios.', 'error')
        return redirect(url_for('main.index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuario(
            username=form.username.data,
            nombre_completo=form.nombre_completo.data,
            rol=form.rol.data,
            activo=form.activo.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Usuario {user.username} registrado exitosamente.', 'success')
        return redirect(url_for('auth.listar_usuarios')) # O a donde quieras redirigir
    return render_template('auth/registro_usuario.html', title='Registrar Usuario', form=form)

@auth.route('/usuarios')
@login_required
def listar_usuarios():
    if not current_user.has_role('ADMINISTRADOR'):
        flash('Acceso no autorizado.', 'error')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Usuarios por página
    usuarios_pagination = Usuario.query.order_by(Usuario.nombre_completo.asc()).paginate(page=page, per_page=per_page, error_out=False)
    usuarios = usuarios_pagination.items
    # Necesitarás una plantilla 'auth/listar_usuarios.html'
    return render_template('auth/listar_usuarios.html', title='Lista de Usuarios', usuarios=usuarios, pagination=usuarios_pagination)

# Más rutas para editar usuario, cambiar contraseña, etc.
"""

CONTENIDO_AUTH_FORMS_PY = """
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.models import Usuario

class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    nombre_completo = StringField('Nombre Completo', validators=[DataRequired(), Length(max=150)])
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Confirmar Contraseña', validators=[DataRequired(), EqualTo('password', message='Las contraseñas deben coincidir.')])
    rol_choices = [
        ('ADMINISTRADOR', 'Administrador'),
        ('CAJERO', 'Cajero'),
        ('TABLAJERO', 'Tablajero'),
        ('REPARTIDOR', 'Repartidor')
    ]
    rol = SelectField('Rol del Usuario', choices=rol_choices, validators=[DataRequired()])
    activo = BooleanField('Usuario Activo', default=True)
    submit = SubmitField('Registrar Usuario')

    def validate_username(self, username):
        user = Usuario.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige otro.')

"""

# --- Funciones para crear la estructura ---
def crear_estructura(base_path, estructura_dict):
    for nombre, contenido in estructura_dict.items():
        current_path = os.path.join(base_path, nombre)

        if isinstance(contenido, dict): # Es un directorio con más contenido
            if not os.path.exists(current_path):
                os.makedirs(current_path)
                print(f"Directorio creado: {current_path}")
            
            # Procesar subdirectorios y archivos dentro de este directorio
            if "dirs" in contenido:
                for sub_dir in contenido["dirs"]:
                    sub_dir_path = os.path.join(current_path, sub_dir)
                    if not os.path.exists(sub_dir_path):
                        os.makedirs(sub_dir_path)
                        print(f"Directorio creado: {sub_dir_path}")
            
            if "files" in contenido:
                for file_name in contenido["files"]:
                    file_path = os.path.join(current_path, file_name)
                    if not os.path.exists(file_path):
                        with open(file_path, "w", encoding="utf-8") as f:
                            # Asignar contenido específico si está definido
                            if file_name == "run.py" and base_path == "": # Archivo raíz
                                f.write(CONTENIDO_RUN_PY)
                            elif file_name == "config.py" and base_path == "": # Archivo raíz
                                f.write(CONTENIDO_CONFIG_PY)
                            elif file_name == "__init__.py" and nombre == "app":
                                f.write(CONTENIDO_APP_INIT_PY)
                            elif file_name == "models.py" and nombre == "app":
                                f.write(CONTENIDO_MODELS_PY)
                            elif file_name == "requirements.txt" and base_path == "":
                                f.write(CONTENIDO_REQUIREMENTS_TXT)
                            elif file_name == ".gitignore" and base_path == "":
                                f.write(CONTENIDO_GITIGNORE)
                            elif file_name == "estilo.css" and nombre == "css":
                                f.write(CONTENIDO_ESTILO_CSS)
                            elif file_name == "main.js" and nombre == "js":
                                f.write(CONTENIDO_MAIN_JS)
                            elif file_name == "base.html" and nombre == "layouts":
                                f.write(CONTENIDO_BASE_HTML)
                            elif file_name == "_nav.html" and nombre == "layouts":
                                f.write(CONTENIDO_NAV_HTML)
                            elif file_name == "_footer.html" and nombre == "layouts":
                                f.write(CONTENIDO_FOOTER_HTML)
                            elif file_name == "_form_field.html" and nombre == "shared":
                                f.write(CONTENIDO_FORM_FIELD_HTML)
                            elif file_name == "index.html" and nombre == "main" and "templates" in current_path: # Plantilla main/index.html
                                f.write(CONTENIDO_MAIN_INDEX_HTML)
                            elif file_name == "login.html" and nombre == "auth" and "templates" in current_path:
                                f.write(CONTENIDO_LOGIN_HTML)
                            elif file_name == "registro_usuario.html" and nombre == "auth" and "templates" in current_path:
                                f.write(CONTENIDO_REGISTRO_USUARIO_HTML)
                            elif file_name == "__init__.py" and nombre in ["auth", "pedidos", "caja", "productos", "clientes", "utils", "main"]:
                                f.write(CONTENIDO_BLUEPRINT_INIT.format(blueprint_name=nombre))
                            elif file_name == "routes.py" and nombre == "main":
                                f.write(CONTENIDO_MAIN_ROUTES_PY)
                            elif file_name == "routes.py" and nombre == "auth":
                                f.write(CONTENIDO_AUTH_ROUTES_PY)
                            elif file_name == "forms.py" and nombre == "auth":
                                f.write(CONTENIDO_AUTH_FORMS_PY)
                            # Añadir más condiciones para otros archivos con contenido inicial
                            else:
                                f.write(f"# Archivo: {file_path}\n") # Contenido por defecto
                        print(f"Archivo creado: {file_path}")
            
            # Llamada recursiva para sub-estructuras (app, static, templates, etc.)
            # Evitar pasar "dirs" y "files" como estructuras anidadas
            sub_estructura = {k: v for k, v in contenido.items() if k not in ["dirs", "files"]}
            if sub_estructura:
                crear_estructura(current_path, sub_estructura)
        
        # Si no es un dict, es un archivo en el nivel actual (no debería pasar con esta estructura)

if __name__ == "__main__":
    # Crear la estructura a partir del directorio actual
    # (el script debe estar fuera de la carpeta NOMBRE_PROYECTO)
    crear_estructura("", ESTRUCTURA_PROYECTO)
    
    # Crear archivo .env de ejemplo en la raíz del proyecto
    env_path = os.path.join(NOMBRE_PROYECTO, ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("# Variables de Entorno para PolleriaMontiel\n")
            f.write("FLASK_APP=run.py\n")
            f.write("FLASK_ENV=development\n") # O FLASK_DEBUG=1
            f.write("SECRET_KEY='tu_super_secreta_clave_aqui_cambiar_esto'\n")
            f.write("# DATABASE_URL='sqlite:///app.db' # Ya se define en config.py, pero puedes sobreescribir aquí\n")
        print(f"Archivo .env de ejemplo creado en: {env_path}")

    # Hacer run.py ejecutable (Linux/Mac)
    run_py_path = os.path.join(NOMBRE_PROYECTO, "run.py")
    if os.name != 'nt' and os.path.exists(run_py_path): # No para Windows
        try:
            current_permissions = os.stat(run_py_path).st_mode
            os.chmod(run_py_path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            print(f"Permisos de ejecución añadidos a: {run_py_path}")
        except Exception as e:
            print(f"No se pudieron cambiar los permisos de {run_py_path}: {e}")


    print("\n--- Estructura del Proyecto Creada Exitosamente ---")
    print(f"Directorio del proyecto: {os.path.abspath(NOMBRE_PROYECTO)}")
    print("\nPróximos pasos recomendados:")
    print(f"1. Navega al directorio del proyecto: cd {NOMBRE_PROYECTO}")
    print("2. Crea y activa un entorno virtual:")
    print("   python -m venv venv")
    print("   En Windows: .\\venv\\Scripts\\activate")
    print("   En Linux/Mac: source venv/bin/activate")
    print("3. Instala las dependencias:")
    print("   pip install -r requirements.txt")
    print("4. (Opcional) Inicializa Git:")
    print("   git init")
    print("   git add .")
    print("   git commit -m \"Fase 0: Estructura inicial del proyecto y configuración base.\"")
    print("5. Crea la base de datos (si es necesario, Flask-SQLAlchemy la creará al primer uso si es SQLite):")
    print("   flask shell")
    print("   >>> from app import db")
    print("   >>> db.create_all()")
    print("   >>> exit()")
    print("   (Nota: db.create_all() es para la creación inicial. Para cambios futuros, usa migraciones con Flask-Migrate)")
    print(f"6. (Opcional) Crea un usuario administrador (si descomentaste el comando en run.py):")
    print(f"   flask create_admin")
    print("7. Ejecuta la aplicación de desarrollo:")
    print("   flask run   (o python run.py)")
    print("   Abre http://127.0.0.1:5000 en tu navegador.")
    print("\n¡Listo para empezar a codificar la Fase 0!")