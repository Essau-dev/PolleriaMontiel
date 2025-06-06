# from flask import Blueprint # Eliminar esta importación

# Define el Blueprint para el módulo de utilidades (si tuviera rutas/plantillas)
# utils = Blueprint('utils', __name__, template_folder='templates') # Eliminar esta línea

# from . import routes # Eliminar esta importación si no hay rutas

# Importar módulos de utilidad directamente
from . import helpers
from . import decorators
