from flask import Blueprint

# Define el Blueprint para el módulo de productos
productos = Blueprint('productos', __name__, template_folder='templates')

from . import routes # Importa las rutas del blueprint
