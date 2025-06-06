from flask import Blueprint

# Define el Blueprint principal
main = Blueprint('main', __name__, template_folder='templates')

from . import routes # Importa las rutas del blueprint
