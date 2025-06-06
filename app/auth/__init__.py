from flask import Blueprint

# Define el Blueprint para el módulo de autenticación
auth = Blueprint('auth', __name__, template_folder='templates')

from . import routes # Importa las rutas del blueprint
