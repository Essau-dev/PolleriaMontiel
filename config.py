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

    # Polleria Montiel - Configuraciones específicas (MOVIDAS A LA BD - Modelo ConfiguracionSistema)
    # NOMBRE_NEGOCIO = "Pollería Montiel"
    # LIMITE_ITEMS_PA_SIN_COMISION = 3
    # MONTO_COMISION_FIJA_PA_EXTRA = 4.0
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


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
