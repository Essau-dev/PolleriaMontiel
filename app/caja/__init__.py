from flask import Blueprint

# Define el Blueprint para el módulo de caja
caja = Blueprint('caja', __name__, template_folder='templates')

from . import routes # Importa las rutas del blueprint
