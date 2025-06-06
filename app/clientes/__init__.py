from flask import Blueprint

# Define el Blueprint para el módulo de clientes
clientes = Blueprint('clientes', __name__, template_folder='templates')

from . import routes # Importa las rutas del blueprint
